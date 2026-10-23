#!/usr/bin/env python3
"""Facial-identity lock for PosterLoom.

Routing a portrait to an identity-safe style is necessary but NOT sufficient:
image models redraw faces by default, and "preserve the subject's identity" in a
style prompt is routinely ignored. This module emits a dedicated likeness block
that is injected into EVERY portrait prompt regardless of the chosen style, so
the constraint survives even when the route is a photographic or editorial style.

The block is written to be appended last, immediately before the negative
constraints, because later instructions carry more weight in diffusion and
instruction-tuned models.
"""
from __future__ import annotations

# Phrases that signal a human subject even when subject.type is vague.
PERSON_TYPES = {
    "person", "portrait", "human", "figure", "headshot", "face",
    "people", "crowd", "group", "selfie", "model",
}
PERSON_TAGS = {
    "portrait", "person", "human", "face", "headshot", "people",
    "crowd", "figure", "selfie", "passenger", "worker", "performer",
}

FACE_LIKE_ANCHORS = (
    "face shape", "facial features", "eye shape", "eyebrow shape", "nose shape",
    "mouth shape", "jawline", "cheekbone", "hairline", "facial hair",
    "skin tone", "freckles", "moles", "wrinkles", "glasses", "expression",
)


def _norm(values):
    if not values:
        return set()
    if isinstance(values, str):
        values = [values]
    return {str(v).strip().lower() for v in values if str(v).strip()}


def subject_type_of(profile) -> str:
    return str((profile.get("subject") or {}).get("type", "")).strip().lower()


def identity_anchors_of(profile) -> list:
    return list((profile.get("subject") or {}).get("identity_anchors") or [])


def has_face_risk(profile) -> bool:
    """True when the profile describes a recognizable human face.

    Used to decide whether the likeness lock must be injected. It errs toward
    injecting: a false positive costs a few prompt lines, a false negative
    silently produces a different person.
    """
    stype = subject_type_of(profile)
    if stype in PERSON_TYPES:
        return True
    tags = _norm(profile.get("subject_tags"))
    if tags & PERSON_TAGS:
        return True
    # A face can be present without the subject being typed as a person.
    # Identity anchors are the strongest available signal.
    anchors = " ".join(a.lower() for a in identity_anchors_of(profile))
    if any(a in anchors for a in FACE_LIKE_ANCHORS):
        return True
    # Multiple people still contain faces.
    try:
        body = (profile.get("subject") or {}).get("count")
        if body and int(body) > 1:
            return True
    except (TypeError, ValueError):
        pass
    return False


def tolerance_of(profile) -> str:
    return str(profile.get("transformation_tolerance", "")).strip().lower()


def wants_heavy_transformation(profile) -> bool:
    return tolerance_of(profile) in ("high", "medium-high")


# Styles whose whole visual system is one verified face repeated on the canvas.
# For these, duplication is the intent — but it must be the SAME face, so the
# identity lock stays fully on and only the "never duplicate" clause is relaxed.
REPEAT_IDENTITY_STYLES = {"duotone-identity-stack"}

# Styles whose concept is a NON-PHOTOGRAPHIC illustration that deliberately
# generalizes the face. For these, "reproduce the exact face" would contradict
# the style itself, so the lock does not weaken — it changes shape. It becomes
# a DERIVATION lock: the figure must still trace back to the source (head
# shape, tilt, hairline, age cues, gesture, gaze), but rendered as illustration
# and never as a photorealistic likeness claim.
ABSTRACT_IDENTITY_STYLES = {"scene-distillation-zine"}


def identity_mode(style_id):
    """Which face-disposition rule applies to this style."""
    if style_id in REPEAT_IDENTITY_STYLES:
        return "repeat"
    if style_id in ABSTRACT_IDENTITY_STYLES:
        return "abstract"
    return "single"


def repetition_clause(style_id):
    """Swap the flat no-duplication rule for a same-face repetition rule."""
    if style_id in REPEAT_IDENTITY_STYLES:
        return (
            "7. REPEAT ONE IDENTITY. This style deliberately repeats the same face. "
            "Every copy must be the SAME verified person with identical face shape, "
            "eye shape and spacing, eyebrow shape, nose and mouth shape, jawline, "
            "hairline, skin tone, and age cues. Repetition must never drift into a "
            "different person, an averaged face, or a hybrid of several people."
        )
    return (
        "7. SINGLE IDENTITY. If other people appear, every face must correspond to its own "
        "person in the source. Never duplicate, merge, or average faces."
    )


ABSTRACT_IDENTITY_BLOCK = """FACIAL IDENTITY LOCK — HIGHEST PRIORITY (ABSTRACT MODE){style_ctx}
This style renders a non-photographic illustration, so the source person is the
SEMANTIC subject, not a photographic likeness claim. The lock is not disabled —
it is restated in the only form this style can honour.

1. DERIVE, DO NOT INVENT. If a head or face appears, it must still be derived
   from the source: the same head shape and skull proportion, the same head
   angle and tilt, the same hairline and hair mass, the same apparent age, the
   same gender presentation, the same gesture, posture and gaze direction.
   Generalize the RENDERING, never the IDENTITY.
2. ABSTRACT, DO NOT PHOTOGRAPH. Render the figure as flat printed illustration
   in this style's grammar. Do not render a photorealistic face, do not simulate
   a photograph of the person, and do not present the result as a documentary
   likeness.
3. NO NEW IDENTIFIABLE PERSON. Do not drift toward a model-default face, a
   specific celebrity or public figure, a symmetric ideal, or a generic
   stock-photo head. The abstracted figure must be traceable to THIS source.
4. NO HYBRID PEOPLE. Never merge the source figure with another face, and never
   average it toward a composite.
5. NO ENHANCEMENT. No beautification, no de-aging, no skin smoothing, no
   enlarging of eyes or lips.
6. {anchor_line}
7. SINGLE SOURCE FIGURE. If other people appear, each must correspond to its own
   person in the source. Never duplicate, merge, or average faces.
8. VERIFY BEFORE DELIVERING. Check that the abstracted figure still reads as the
   source person through head shape, head angle, hairline, age cues and gesture.
   If it has drifted into a different or a generic person, regenerate."""


ABSTRACT_IDENTITY_NEGATIVE = (
    "no photorealistic face, no photographic likeness of the source person, "
    "no new identifiable individual, no celebrity lookalike, no model-default "
    "or idealized face, no face averaged toward a composite, no merged faces, "
    "no face duplication, no changed head shape or head angle, no changed "
    "hairline, no age shift, no gender presentation shift, no beautification, "
    "no plastic or airbrushed skin, no teeth or smile alteration, "
    "no extra or missing fingers, no text over the face."
)


def likeness_block(profile, style_id=None, style_name=None) -> str:
    """Return the facial-identity constraint block for a portrait prompt."""
    anchors = identity_anchors_of(profile)
    if anchors:
        anchor_line = (
            "Bind these source-specific identity anchors verbatim: "
            + "; ".join(str(a) for a in anchors)
            + "."
        )
    else:
        anchor_line = (
            "Derive identity anchors from the source image itself before generating. "
            "Do not invent new facial characteristics."
        )

    style_ctx = f" This applies on top of the {style_name or style_id} style." if (style_id or style_name) else ""
    repeat_clause = repetition_clause(style_id)

    if identity_mode(style_id) == "abstract":
        return ABSTRACT_IDENTITY_BLOCK.format(style_ctx=style_ctx, anchor_line=anchor_line)

    return f"""FACIAL IDENTITY LOCK — HIGHEST PRIORITY{style_ctx}
This instruction outranks the style, the aesthetic, and any beautification tendency.

1. REPRODUCE, DO NOT INVENT. Render the exact face present in the source photograph.
   Facial structure is fixed input geometry, not content to reinterpret or improve.
2. PRESERVE EXACTLY: face shape and width, jawline and chin, cheekbone structure,
   eye shape, eye size, eye spacing and eyelid shape, eyebrow shape and position,
   nose width and bridge, lip shape and mouth width, ear position, hairline, facial
   hair pattern, skin tone and undertone, freckles, moles, scars, wrinkles, and
   visible age cues.
3. PRESERVE EXPRESSION AND GAZE: the same emotional read, mouth state, brow tension,
   and gaze direction as the source.
4. {anchor_line}
5. NO SUBSTITUTION. Do not generate a new person. Do not average toward a generic or
   idealized face. Do not shift age, gender presentation, ethnicity, or body type.
6. NO ENHANCEMENT. No beauty retouching, no skin smoothing, no reshaping, no
   enlargement of eyes or lips, no makeup addition, no teeth straightening.
{repeat_clause}
8. VERIFY BEFORE DELIVERING. Compare the generated face against the source on the
   seven identity-critical points — face shape, eye shape/spacing, eyebrow shape,
   nose shape, mouth shape, hairline, skin tone. If any differ, regenerate before
   showing the result."""


def likeness_negative(profile, style_id=None) -> str:
    """Negative constraints naming the specific facial-drift failure modes."""
    if identity_mode(style_id) == "abstract":
        return ABSTRACT_IDENTITY_NEGATIVE
    duplication = (
        "no drifted or mismatched copies within a repeated face, "
        if style_id in REPEAT_IDENTITY_STYLES
        else "no face duplication, no composite or merged faces, "
    )
    return (
        "No different person, no newly invented face, no generic or idealized face, "
        "no face averaged toward a model-default look, no changed face shape or width, "
        "no changed jawline or chin, no altered eye shape, eye size, or eye spacing, "
        "no mismatched eye size between eyes, no eyebrow shape or position change, "
        "no nose width or bridge change, no lip or mouth width change, no changed "
        "hairline or hairstyle, no skin tone or undertone shift, no age shift or "
        "de-aging, no gender presentation shift, no ethnicity shift, no beautification, "
        "no plastic or airbrushed skin, no excessive skin smoothing, no makeup addition, "
        "no teeth or smile alteration, " + duplication +
        "no extra or missing fingers, no text over the face."
    )


def headroom_note(profile) -> str:
    """Framing guidance so the face is not cropped or covered."""
    return (
        "Keep the full face inside the frame with margin around the hairline and chin. "
        "Do not crop through the forehead or jaw. Do not place typography, graphics, "
        "or graphic elements across the face, eyes, or mouth."
    )


def build(profile, style_id=None, style_name=None):
    """Assemble the likeness enforcement payload, or None when not applicable."""
    if not has_face_risk(profile):
        return None
    return {
        "block": likeness_block(profile, style_id, style_name),
        "negative": likeness_negative(profile, style_id),
        "headroom": headroom_note(profile),
        "identity_risk": True,
        "heavy_transformation_requested": wants_heavy_transformation(profile),
    }
