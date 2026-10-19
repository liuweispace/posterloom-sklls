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
7. SINGLE IDENTITY. If other people appear, every face must correspond to its own
   person in the source. Never duplicate, merge, or average faces.
8. VERIFY BEFORE DELIVERING. Compare the generated face against the source on the
   seven identity-critical points — face shape, eye shape/spacing, eyebrow shape,
   nose shape, mouth shape, hairline, skin tone. If any differ, regenerate before
   showing the result."""


def likeness_negative(profile) -> str:
    """Negative constraints naming the specific facial-drift failure modes."""
    return (
        "No different person, no newly invented face, no generic or idealized face, "
        "no face averaged toward a model-default look, no changed face shape or width, "
        "no changed jawline or chin, no altered eye shape, eye size, or eye spacing, "
        "no mismatched eye size between eyes, no eyebrow shape or position change, "
        "no nose width or bridge change, no lip or mouth width change, no changed "
        "hairline or hairstyle, no skin tone or undertone shift, no age shift or "
        "de-aging, no gender presentation shift, no ethnicity shift, no beautification, "
        "no plastic or airbrushed skin, no excessive skin smoothing, no makeup addition, "
        "no teeth or smile alteration, no face duplication, no composite or merged faces, "
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
        "negative": likeness_negative(profile),
        "headroom": headroom_note(profile),
        "identity_risk": True,
        "heavy_transformation_requested": wants_heavy_transformation(profile),
    }
