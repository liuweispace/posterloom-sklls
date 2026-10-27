#!/usr/bin/env python3
"""Budget-aware prompt compilation for backends with a hard prompt length cap.

PosterLoom's full prompt is deliberately thorough — a 3857-character prompt
carries the scene map, the full style mechanism, the named colour system, the
facial-identity lock with eight clauses, and the negative constraints. That is
the right artifact for a long-context chat model, and the wrong artifact for an
image API that rejects anything over 1500 characters.

This module builds a *different* prompt for that case, not a truncated one.
Truncating loses the tail — which is exactly where the identity lock and the
negative constraints live. Instead this rebuilds from the same structured data,
keeping the clauses that actually change the rendered pixels and dropping the
ones that are advice rather than instruction.

The vocabulary matters more than the length, and this was measured rather than
assumed. Against MiniMax image-01, with an identical prompt:

  - "a young man's head and shoulders, hair rendered as a solid flat black
    mass, features simplified into hard flat shapes"  -> flat print
  - "a young man with thick tousled black hair and a coral shirt, looking
    down to the left"                                  -> photograph

The second reads as a description of a photograph, and the model renders one.
So this module rewrites subject descriptions into print language before they
reach the backend, and states the medium in print terms up front.

What survives the budget, in priority order:

1. The print medium — the sentence that decides whether a print or a photo
   comes back.
2. The style's graphic mechanism.
3. The named colour system with hex values — concrete beats adjective.
4. The subject, described concretely and in print language.
5. The facial-identity lock, condensed to its operative clauses.
6. The highest-value negatives.

What gets dropped: the scene map restatement, the framing/headroom note, the
delivery gate, the self-check, and any stylistic prose that only restates
what the mechanism already said.
"""
from __future__ import annotations

import re

DEFAULT_BUDGET = 1400

# ---------------------------------------------------------------------------
# Print language
# ---------------------------------------------------------------------------
# Every entry here was chosen because the photographic wording demonstrably
# pulled the model back toward a photographic render.
PHOTOGRAPHIC_TO_PRINT = [
    (r"\b(photo|photograph|photographic|photography)\b", "printed image"),
    (r"\bphotorealistic\b", "flat printed shapes"),
    (r"\bskin texture\b", "ink texture"),
    (r"\bpores\b", "ink speckle"),
    (r"\bstubble\b", "stubble marks"),
    (r"\bfreckles\b", "freckle marks"),
    (r"\bhair strands\b", "hairline shapes"),
    (r"\bsoft shadows\b", "crushed shadow areas"),
    (r"\bgradients?\b", "flat colour bands"),
    (r"\bcontinuous tone\b", "flat ink areas"),
    (r"\bstudio lighting\b", "print value structure"),
    (r"\bshoulders\b", "upper body"),
    (r"\bwearing\b", "in"),
    (r"\blooking down to the left\b", "head tilted down and to the left"),
    (r"\bnatural texture\b", "flat shape texture"),
    (r"\bsmooth skin\b", "flat skin shapes"),
    (r"\blens\b", ""),
    (r"\bdepth of field\b", "flat depth"),
    (r"\bcontinuous-tone\b", "flat-ink"),
]

# The medium statement. This is the strongest lever in the whole prompt: it
# is what makes the difference between a flat print and a photograph.
MEDIUM_TEMPLATE = (
    "A flat {n} {technique} on {substrate}. Only the named inks, "
    "no others. Hard posterised edges, no smooth shading, no continuous tone. "
    "Visible ink grain, uneven ink coverage and slight misregistration. "
    "Tone must read as ink on paper, not as a photograph."
)

TECHNIQUE_BY_FAMILY = {
    "graphic-portrait": "screen-print",
    "portrait": "screen-print",
    "graphic": "screen-print",
    "poster": "screen-print",
    "print": "screen-print",
    "collage": "paper collage",
    "painterly": "gouache",
    "painterly-impasto": "impasto oil",
    "photographic": "screen-print",
    "editorial": "magazine halftone",
    "analog": "risograph",
    "zine": "riso",
    "architectural": "technical pen and ink",
    "minimal": "risograph",
}

TECHNIQUE_DEFAULT = "screen-print"


def to_print_language(text: str) -> str:
    """Rewrite photographic vocabulary into print vocabulary."""
    if not text:
        return ""
    out = str(text)
    for pattern, repl in PHOTOGRAPHIC_TO_PRINT:
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out)
    out = re.sub(r"\s+([,.;:])", r"\1", out)
    return out.strip()

# Negative constraints that earn their place in a short prompt. Each one names a
# failure mode that would otherwise be the most likely outcome.
NEGATIVE_PRIORITY = [
    "no photo fragments", "no photorealistic", "no tracing", "no rotoscoping",
    "no photo windows", "no generic abstract motifs", "no decorative metaphors",
    "no universal-symbol", "no random ambiguity", "no overly faithful anatomy",
    "no realistic shading", "no cute cartoon", "no kawaii", "no anime",
    "no polished vector", "no arbitrary dots", "no decorative scattering",
    "no sticker-like cutout", "no fuzzy selection halo", "no decorative stamps",
    "no tape", "no multiple competing bright hues", "no dense scrapbooking",
    "no commercial advertising hierarchy", "no logo", "no CTA", "no glossy mockup",
    "no curled paper", "no hard shadows", "no 3D", "no cinematic lighting",
    "no depth of field", "no neon", "no watermark",
    "no face duplication", "no composite or merged faces", "no new or different person",
    "no face averaged", "no changed jawline", "no changed eye shape",
    "no hairline", "no skin tone", "no age shift", "no beautification",
    "no plastic or airbrushed skin", "no teeth", "no text over the face",
    "no generic mood labels", "no clean digital clipping", "no uniform torn border",
    "no heavy cast shadows", "no scattered confetti", "no arbitrary dots",
    "no full-scene photocopy", "no evenly detailed", "no dense hatching",
    "no complete object outlines", "no filler decoration",
    "no detached corner color blocks", "no isolated brush swatches",
    "no large or polished digital typography", "no legible pseudo-symbol systems",
    "no new identifiable individual", "no celebrity lookalike",
    "no model-default or idealized face", "no photorealistic face",
    "no photographic likeness",
]

# The identity clauses that carry the most weight per character. The full lock
# has eight clauses and runs about 1900 characters — more than the entire
# budget on its own.
IDENTITY_ESSENCE = (
    "IDENTITY LOCK (highest priority): reproduce the exact face from the source. "
    "Fixed geometry: face shape and width, jawline and chin, cheekbones, eye shape "
    "and size and spacing, eyebrow shape and position, nose width and bridge, lip "
    "shape and mouth width, ear position, hairline, facial hair, skin tone and "
    "undertone, freckles, moles, wrinkles, visible age. Also fixed: expression, "
    "mouth state, brow tension, gaze direction. No new person, no averaging toward "
    "a generic or idealized face, no age/gender/ethnicity shift, no beautification, "
    "no skin smoothing, no makeup, no teeth alteration. If other people appear, each "
    "face must be its own person — never duplicate, merge, or average faces."
)

IDENTITY_ESSENCE_REPEAT = (
    "IDENTITY LOCK (highest priority): this style repeats the SAME face on purpose. "
    "Every copy must be the identical verified person — same face shape, eye shape and "
    "spacing, brow, nose, mouth, jawline, hairline, skin tone and age cues. Repetition "
    "must never drift into a different person, an averaged face, or a hybrid of people."
)

IDENTITY_ESSENCE_ABSTRACT = (
    "IDENTITY LOCK (highest priority, abstract mode): this style renders a "
    "non-photographic illustration, so the source person is the SEMANTIC subject, not a "
    "photographic likeness. Any figure must still be derived from the source — same head "
    "shape and proportion, same head angle and tilt, same hairline and hair mass, same "
    "apparent age, same gender presentation, same gesture, posture and gaze direction. "
    "Generalize the RENDERING, never the IDENTITY. Render as flat printed illustration, "
    "never as a photorealistic face or a simulated photograph. No new identifiable "
    "person, no celebrity lookalike, no model-default face, no hybrid or averaged faces."
)

# Shorter forms, used only when the budget demands them. Each keeps the clauses
# that change pixels and drops the restatement.
IDENTITY_SHORT = {
    "single": (
        "IDENTITY LOCK (highest priority): reproduce the exact source face. Fixed: face "
        "shape and width, jawline, cheekbones, eye shape/size/spacing, brow shape and "
        "position, nose width and bridge, lip and mouth shape, ear position, hairline, "
        "facial hair, skin tone, freckles, age. Also fixed: expression and gaze. No new "
        "person, no averaged or idealized face, no age/gender/ethnicity shift, no "
        "beautification, no skin smoothing, no makeup. Each face = its own person; never "
        "duplicate, merge, or average faces."
    ),
    "repeat": (
        "IDENTITY LOCK (highest priority): this style repeats the SAME face on purpose. "
        "Every copy must be the identical verified person — same face shape, eye shape and "
        "spacing, brow, nose, mouth, jawline, hairline, skin tone and age cues. Never drift "
        "into a different person, an averaged face, or a hybrid of people."
    ),
    "abstract": (
        "IDENTITY LOCK (highest priority, abstract mode): this style renders "
        "non-photographic illustration, so the source person is the SEMANTIC subject, not a "
        "photographic likeness. Any figure must still derive from the source — same head "
        "shape, head angle and tilt, hairline, age, gender presentation, gesture and gaze. "
        "Generalize the RENDERING, never the IDENTITY. Render as flat printed illustration, "
        "never photorealistic. No new identifiable person, no celebrity lookalike, no "
        "model-default face, no averaged faces."
    ),
}


def _sentences(text: str) -> list:
    """Split prose into sentences, keeping the punctuation."""
    if not text:
        return []
    parts = re.split(r"(?<=[.;!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _clip(text: str, limit: int) -> str:
    """Trim to a character budget at a word boundary."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:") + "..."


def _pick_negative(negative_prompt: str, limit: int = 6) -> str:
    """Keep the negatives that matter most, not the first ones."""
    if not negative_prompt:
        return ""
    raw = [p.strip().rstrip(".") for p in negative_prompt.split(",") if p.strip()]
    scored = []
    for i, item in enumerate(raw):
        low = item.lower()
        best = 99
        for rank, key in enumerate(NEGATIVE_PRIORITY):
            if key in low:
                best = min(best, rank)
                break
        # Unlisted negatives get a middling rank so known ones always win.
        scored.append((best, i, item))
    scored.sort()
    keep = [s[2] for s in scored[:limit]]
    return ", ".join(keep)


def _technique(style: dict) -> str:
    family = (style.get("family") or "").lower()
    for key, tech in TECHNIQUE_BY_FAMILY.items():
        if key in family:
            return tech
    return TECHNIQUE_DEFAULT


def _medium_sentence(style: dict) -> str:
    """The print-medium statement. This is the highest-leverage sentence.

    It names the ink colours outright, because the model will otherwise pick
    its own palette — and its default for a portrait is black and cream, which
    is a fine print and the wrong print.
    """
    cs = style.get("color_system") or {}
    inks = cs.get("inks") or []
    n = len(inks) if inks else 2
    substrate = cs.get("substrate") or "chalky white paper"
    n_word = {1: "one-ink", 2: "two-ink", 3: "three-ink"}.get(n, f"{n}-ink")
    ink_phrase = ""
    if inks:
        ink_phrase = f" Ink colours: {', '.join(inks)} — and nothing else."
    return MEDIUM_TEMPLATE.format(n=n_word, technique=_technique(style), substrate=substrate) + ink_phrase


def _first_sentences(text: str, count: int, limit: int) -> str:
    """Take whole sentences, never a mid-word cut.

    Cutting a sentence in half loses the operative clause — that is how
    "Exactly one copy is the canonical identity anchor..." disappears, which
    is the clause that makes the repetition rule coherent. So the text is
    taken sentence by sentence and the last one is dropped if it does not fit.

    The last kept sentence is clipped to the limit rather than discarded
    when it is the only one. Dropping it returns an empty string, and an
    empty section is worse than a shortened one: the section silently
    vanishes from the prompt and the thing it was there to say is gone.
    """
    sents = _sentences(to_print_language(text))
    out = []
    total = 0
    for s in sents[:count]:
        if total + len(s) + 1 > limit and out:
            break
        out.append(s)
        total += len(s) + 1
    if out:
        return " ".join(out)
    # One sentence that is on its own too long: clip it rather than lose it.
    if sents:
        return _clip(sents[0], limit)
    return ""


def _style_core(style: dict) -> str:
    """The style's mechanism plus its material and typography, in print terms."""
    bits = []
    mech = _first_sentences(style.get("mechanism", ""), 2, 300)
    if mech:
        bits.append(mech)
    mat = _first_sentences(style.get("material_language", ""), 1, 140)
    if mat:
        bits.append("Surface: " + mat)
    typo = _first_sentences(style.get("typography", ""), 1, 130)
    if typo:
        bits.append("Type: " + typo)
    return " ".join(bits)


def _color_core(style: dict, max_ramps: int = 1, limit: int = 0) -> str:
    """Named inks and hex values — the part a model can actually execute.

    Kept short on purpose. The full version — substrate, inks, accent,
    coverage, four ramps and a closing instruction — runs to 632 characters,
    which is more than a third of the whole budget, and the ramps are the
    least load-bearing part of it. The ink names carry the palette; one ramp
    carries the values. The closing instruction matters more than it looks:
    "use these hex values literally" is what stops the model from answering
    "crimson" with a generic warm red.

    `limit` caps the result. When the accent or coverage description is long
    — the zine styles describe a whole colour policy in prose — those go
    first, because the ink names and the hex ramp are the parts a model can
    act on.
    """
    cs = style.get("color_system")
    if not cs:
        return ""

    def build(with_accent: bool, with_coverage: bool, ramps: int) -> str:
        parts = []
        if cs.get("inks"):
            parts.append(f"Inks: {', '.join(cs['inks'])}")
        if with_accent and cs.get("accent"):
            parts.append(f"accent {cs['accent']}")
        if with_coverage and cs.get("coverage"):
            parts.append(f"coverage {cs['coverage']}")
        for name, ramp in list((cs.get("ramps") or {}).items())[:ramps]:
            stops = ", ".join(f"{k} {v}" for k, v in ramp.items())
            parts.append(f"ramp {name}: {stops}")
        parts.append("Use these hex values literally, not adjectives.")
        return " | ".join(parts)

    text = build(True, True, max_ramps)
    if not limit or len(text) <= limit:
        return text

    # Drop the coverage description first, then the accent, then the ramp.
    for with_accent, with_coverage, ramps in (
        (True, False, max_ramps),
        (False, False, max_ramps),
        (False, False, 0),
    ):
        text = build(with_accent, with_coverage, ramps)
        if len(text) <= limit:
            return text
    return _clip(text, limit)


def _clip_sentences(text: str, limit: int) -> str:
    """Trim to whole sentences, so a fact is never cut in half.

    A character-level cut through the middle of a sentence produces a prompt
    that ends mid-clause, which reads as a mistake and loses the binding fact.

    When the text is a single sentence that is on its own longer than the
    limit, it is clipped to the limit. Returning it whole would make the
    limit meaningless: the caller shrinks a section, the section does not
    shrink, and the prompt cannot be made to fit.
    """
    sents = _sentences(text)
    out = []
    total = 0
    for s in sents:
        if total + len(s) + 1 > limit and out:
            break
        out.append(s)
        total += len(s) + 1
    if out:
        # A single sentence may still exceed the limit — clip it.
        joined = " ".join(out)
        return _clip(joined, limit) if len(joined) > limit else joined
    return _clip(text, limit)


def _subject_core(profile: dict, style: dict) -> str:
    """Describe the subject concretely, in print language.

    The model has no other way to know the subject, so the facts matter — but
    the wording decides whether they arrive as a print or as a photograph.

    The identity anchors are deliberately left out. The identity lock already
    lists them, and repeating both cost about 200 characters of a 1400
    character budget. The subject here is what the subject IS; the lock is
    what must not change.
    """
    subject = profile.get("subject", {}) or {}
    bits = []
    summary = str(subject.get("summary", "")).strip()
    if summary:
        bits.append(f"Subject: {to_print_language(summary)}")
    else:
        stype = str(subject.get("type", "")).strip()
        if stype:
            bits.append(f"Subject: {stype}")
    for key, label in (("lighting", "Value"), ("mood", "Mood"),
                       ("materials", "Materials"), ("geometry", "Layout")):
        vals = [str(v) for v in (profile.get(key) or [])][:3]
        if vals:
            bits.append(f"{label}: {', '.join(to_print_language(v) for v in vals)}")
    if profile.get("environment"):
        bits.append(f"Setting: {to_print_language(str(profile['environment']))}")
    return " ".join(bits)


def _source_role_clause(style: dict, described: bool = False) -> str:
    """The photo is either an anchor to keep or evidence to interpret.

    `described` means the subject was read from the photo by a vision model
    rather than attached to the image request. In that case the clause has to
    say so, because the photo is not in the request and the model cannot see it.

    For the semantic-reference styles this carries the NO PHOTOGRAPHY rule,
    which is a hard constraint on the output and not a stylistic suggestion.
    It is stated in the same words the style contract uses, so the two cannot
    drift apart.
    """
    if (style.get("source_role") or "visual-anchor") == "semantic-reference":
        return (
            "NO PHOTOGRAPHY. The source photograph is SEMANTIC EVIDENCE only — a "
            "reference for meaning, subject, gesture and relationship, not a visual "
            "layer to keep. Never reproduce, embed, crop, collage, trace or retain its "
            "photographic pixels or photorealistic regions. The output contains "
            "original illustration, paper and typography only. Preserve the subject's "
            "semantic identity — same core subject, same relationship, same gesture and "
            "gaze — and reinterpret how it looks, never what it means."
        )
    if described:
        return (
            "The subject below was read from the source photograph. Treat every stated "
            "fact as binding: same person, same proportions, same age, same clothing, "
            "same head angle, same gaze. Do not substitute a different person or invent "
            "any detail that is not stated."
        )
    return (
        "Use the source photograph as the factual and visual anchor. Keep the subject's "
        "defining identity. Do not substitute a different person, object, building, "
        "costume, location, brand, date, or historical claim."
    )


# (max colour ramps, max negatives, style prose limit or None) in the order they
# are given up. A style with no colour system simply ignores the ramp column.
_VARIANTS = [
    (4, 6, None), (4, 4, None), (2, 4, None), (2, 3, None), (1, 3, None),
    (1, 2, None), (1, 0, None),
    (1, 0, 200), (1, 0, 150), (1, 0, 110),
    (0, 0, 110),
]


def build_compact(profile: dict, style: dict, budget: int = DEFAULT_BUDGET,
                   subject_override: str = None,
                   layout_override: str = None) -> str:
    """Build a prompt that fits a hard character budget.

    The prompt is assembled from sections in a fixed priority order, and the
    budget is spent top down until it runs out. The order was fixed by
    measuring what each section actually does to the rendered image:

      1. medium      the print statement. Decides print vs photograph.
      2. source      the role of the photo. Carries NO PHOTOGRAPHY, which is
                     a hard constraint on what may appear at all.
      3. subject     who or what is depicted, and the identity facts the
                     lock refers back to.
      4. layout      the arrangement. Without it a "stack" style renders one
                     portrait — the style's core failure mode.
      5. colour      the named inks and their hex values. Without it the
                     model picks its own palette.
      6. lock        the identity lock. Never dropped: it is what makes the
                     output safe to send unattended.
      7. style       the mechanism prose.
      8. avoid       the negative constraints.

    Sections 1-6 are required. 7 and 8 are given whatever is left over, in
    that order, so a style with a long mechanism does not push out the
    things that decide the image.

    `subject_override` replaces the profile's subject block with a
    description produced elsewhere — typically a vision model's factual
    reading of the source photo. That is how likeness survives the loss of
    the reference attachment, which is what keeps the print treatment intact.

    `layout_override` replaces the LAYOUT section with a per-variant
    arrangement directive. One image API call with `n=3` returns three samples
    of the SAME prompt, so distinct designs need distinct prompts — and the
    arrangement is the one axis that can differ without changing the style,
    the palette or the identity.
    """
    from face_identity import identity_mode

    mode = identity_mode(style.get("id"))
    identity = {
        "repeat": IDENTITY_ESSENCE_REPEAT,
        "abstract": IDENTITY_ESSENCE_ABSTRACT,
        "single": IDENTITY_ESSENCE,
    }[mode]

    source = _source_role_clause(style, described=bool(subject_override))
    subject = subject_override if subject_override else _subject_core(profile, style)
    medium = _medium_sentence(style)
    needs_lock = _needs_identity(profile)
    # The composition is what makes the stack a stack. The mechanism sentence
    # says "repeat as a stack" but the arrangement itself lives in the
    # composition field, and without it the model renders a single portrait.
    composition = _first_sentences(style.get("composition", ""), 1, 240)
    colour = _color_core(style, max_ramps=1, limit=220) if style.get("color_system") else ""
    lock_text = identity if needs_lock else ""

    # The per-variant arrangement gets its OWN section rather than being
    # prepended to LAYOUT. Two measured reasons:
    #
    # 1. Placement. A style's composition often states a default
    #    arrangement ("build a vertical stack along the centerline"). A
    #    variant that contradicts it must come AFTER it, because the later
    #    instruction is the one the model follows. Prepending it made the
    #    variant lose, and the sheet came out as the style's default.
    # 2. Budget. The enforcement clips sections by whole sentences from the
    #    front, so a variant sharing a section with the style's composition
    #    is the part that gets cut — the sheet silently fell back to the
    #    style's default arrangement. A separate section cannot be clipped
    #    into a different meaning.
    arrangement = (layout_override or "").strip()

    # The required sections, in priority order, each with a floor.
    # ARRANGEMENT sits right after LAYOUT: it refines the arrangement for this
    # particular sheet without replacing the style's own composition.
    #
    # The STYLE section is required whenever an arrangement is present. It
    # carries the print mechanism — posterised edges, the ink surface, the
    # discipline that keeps the sheet a print rather than a photograph. When
    # the arrangement consumed the budget and evicted STYLE, the sheets
    # came back as duotone photographs: correct palette, wrong medium. The
    # mechanism is not recoverable from anywhere else in the prompt.
    style_core = _style_core(style)
    required = [
        ("medium", medium, 200),
        ("source", source, 150),
        ("subject", subject, 230),
        ("layout", composition, 100),
        ("arrangement", arrangement, 60),
        ("colour", colour, 90),
        ("lock", lock_text, 0),
    ]
    if arrangement:
        required.append(("style", style_core, 120))
    # The optional sections, in the order they get whatever budget is left.
    # When a per-variant arrangement is present it costs about 150 characters,
    # and the naive result is that the STYLE section — which carries the print
    # mechanism, the surface and the ink discipline — gets evicted entirely.
    # That is what made the sheets drift back toward photography: without the
    # mechanism prose the model has nothing telling it to posterise.
    #
    # So the arrangement is paid for out of the optional sections. The STYLE
    # section is what keeps the medium right; the arrangement is what makes
    # the set varied. The medium wins.
    optional = [
        ("style", style_core, 120),
        ("avoid", _pick_negative(style.get("negative_prompt", ""), 6), 60),
    ]
    if arrangement:
        # STYLE is already in the required set — do not emit it twice.
        optional = [o for o in optional if o[0] != "style"]

    # Spend the budget: keep every required section, then add the optional
    # ones if they fit, then clip the required ones toward their floors.
    labels = {"medium": "A flat ", "source": None, "subject": "Subject:",
              "layout": "LAYOUT:", "arrangement": "ARRANGEMENT:",
              "colour": "COLOUR:", "lock": "IDENTITY LOCK",
              "style": "STYLE ", "avoid": "AVOID:"}

    def build(req, opt):
        parts = []
        for name, text, floor in req:
            if not text:
                continue
            lab = labels.get(name)
            if lab and not text.startswith(lab):
                parts.append(f"{lab} {text}" if lab.endswith(":") else f"{lab} {text}")
            else:
                parts.append(text)
        for name, text, floor in opt:
            if not text:
                continue
            lab = labels.get(name)
            if lab and not text.startswith(lab):
                parts.append(f"{lab} {text}")
            else:
                parts.append(text)
        return "\n".join(parts)

    # Try the full thing first.
    candidate = build(required, optional)
    if len(candidate) <= budget:
        return _enforce_budget(candidate, budget, style, needs_lock)

    # Drop the optional sections, most expendable first. The required set
    # alone is what must fit — it is the six sections that decide the image.
    for opt_count in (1, 0):
        candidate = build(required, optional[:opt_count])
        if len(candidate) <= budget:
            return _enforce_budget(candidate, budget, style, needs_lock)

    # Clip the required sections toward their floors, in reverse priority
    # order — the subject and the lock are the last to be touched.
    #
    # The lock switches to its short form here. The full lock is 688
    # characters and lists every fixed feature; the short one keeps the
    # clauses that change pixels and drops the restatement. That difference
    # is what lets the layout and colour sections survive alongside it.
    short_lock = IDENTITY_SHORT[mode] if needs_lock else ""
    # When the scene has no face there is no lock, and the loop must still
    # run — skipping it on the empty lock was leaving the layout and colour
    # sections out of every non-portrait prompt.
    lock_variants = (lock_text, short_lock) if needs_lock else ("",)
    for lock in lock_variants:
        if not lock and needs_lock:
            continue
        for subj in (400, 320, 260, 230, 190, 150, 120, 100):
            for src in (None, 320, 260, 200, 150):
                for lay in (240, 180, 140, 100):
                    for col in (None, 200, 150, 100, 70):
                        # The arrangement and the print mechanism are shrunk
                        # too, not fixed. A variant adds about 150 characters
                        # to a set that was already near the limit, and when
                        # the loop could not shrink them it fell through to
                        # the absolute floor — which drops LAYOUT, ARRANGEMENT
                        # and STYLE entirely. The sheet then came back
                        # without its arrangement AND without its print
                        # mechanism: a duotone photograph in the default
                        # layout, indistinguishable from every other sheet.
                        arr_limits = (None, 130, 100, 80, 60) if arrangement else (None,)
                        sty_limits = (200, 150, 120) if arrangement else (None,)
                        for arr_lim in arr_limits:
                            for sty_lim in sty_limits:
                                req = [
                                    ("medium", _clip_sentences(medium, 240), 200),
                                    ("source", source if src is None else _clip_sentences(source, src), 150),
                                    ("subject", _clip_sentences(subject, subj), 150),
                                    ("layout", _clip_sentences(composition, lay), 100),
                                    ("arrangement", arrangement if arr_lim is None
                                     else _clip_sentences(arrangement, arr_lim), 60),
                                    ("colour", colour if col is None else _clip_sentences(colour, col), 70),
                                    ("lock", lock, 0),
                                ]
                                if arrangement:
                                    req.append(("style", _clip_sentences(
                                        style_core, sty_lim), 120))
                                candidate = build(req, [])
                                if len(candidate) <= budget:
                                    return _enforce_budget(candidate, budget, style, needs_lock)

    # Absolute floor: the medium, the source rule, the subject, the lock.
    # NO PHOTOGRAPHY survives here because it is a hard constraint, not a
    # stylistic preference.
    req = [
        ("medium", _clip_sentences(medium, 200), 200),
        ("source", _clip_sentences(source, 240), 150),
        ("subject", _clip_sentences(subject, 150), 150),
        ("lock", short_lock or lock_text, 0),
    ]
    candidate = build(req, [])
    return _enforce_budget(candidate, budget, style, needs_lock)



def _enforce_budget(candidate: str, budget: int, style: dict, needs_lock: bool) -> str:
    """Guarantee the prompt fits, whatever the inputs were.

    The layered fallbacks in build_compact normally land inside the budget on
    their own. This is the backstop for the cases they cannot cover: a style
    whose mechanism and composition are both long, a subject description that
    is one huge sentence, or a backend with a tighter cap than any we tested.

    It works on the sections, not on the raw string. Sections are clipped in
    reverse priority order until the whole thing fits, and each section keeps
    a floor so it never becomes a stub. The identity lock and the NO
    PHOTOGRAPHY rule are never clipped away: they are the two clauses that
    constrain what the output may contain at all.
    """
    if len(candidate) <= budget:
        return candidate

    lines = candidate.split("\n")
    no_photography = None
    for line in lines:
        if line.startswith("NO PHOTOGRAPHY"):
            no_photography = line
            break

    # Order the sections by how much they decide the image, least first.
    # ARRANGEMENT is clipped BEFORE LAYOUT because the style's own composition
    # is what keeps the sheet in-style, while the arrangement only refines
    # how this one sheet is laid out. Losing the arrangement costs the set
    # its variety; losing the composition costs the sheet its identity.
    order = ["AVOID:", "STYLE ", "ARRANGEMENT:", "COLOUR:", "LAYOUT:", "Subject:"]
    floors = {"AVOID:": 0, "STYLE ": 60, "ARRANGEMENT:": 60,
              "COLOUR:": 60, "LAYOUT:": 80, "Subject:": 100}

    def find(prefix):
        for i, line in enumerate(lines):
            if line.startswith(prefix):
                return i
        return None

    # Shrink the least important sections first, one step at a time, until the
    # whole prompt fits.
    for prefix in order:
        idx = find(prefix)
        if idx is None:
            continue
        floor = floors[prefix]
        text = lines[idx]
        for limit in (240, 200, 160, 130, 110, 90, 75, floor):
            if limit < floor:
                continue
            candidate_lines = list(lines)
            candidate_lines[idx] = _clip_sentences(text, limit)
            cand = "\n".join(candidate_lines)
            if len(cand) <= budget:
                return cand
        # If even the floor does not fit, drop the section entirely — except
        # for the sections that carry a hard rule.
        if floor == 0:
            candidate_lines = list(lines)
            del candidate_lines[idx]
            cand = "\n".join(candidate_lines)
            if len(cand) <= budget:
                return cand

    # Still too long: rebuild from the five sections that decide the image.
    medium_line = next((l for l in lines if l.startswith("A flat ")), "")
    subject_line = next((l for l in lines if l.startswith("Subject:")), "")
    layout_line = next((l for l in lines if l.startswith("LAYOUT:")), "")
    arrangement_line = next((l for l in lines if l.startswith("ARRANGEMENT:")), "")
    colour_line = next((l for l in lines if l.startswith("COLOUR:")), "")
    source_line = next((l for l in lines
                        if l.startswith("NO PHOTOGRAPHY") or l.startswith("The subject below")
                        or l.startswith("Use the source photograph")), "")
    lock_line = next((l for l in lines if l.startswith("IDENTITY LOCK")), "")

    # The NO PHOTOGRAPHY rule is a hard constraint and is never clipped.
    keep = [
        _clip_sentences(medium_line, 190),
        source_line if no_photography else _clip_sentences(source_line, 220),
        _clip_sentences(subject_line, 140),
        _clip_sentences(layout_line, 90),
        _clip_sentences(arrangement_line, 120),
        _clip_sentences(colour_line, 100),
        lock_line,
    ]
    out = "\n".join(k for k in keep if k)
    if len(out) <= budget:
        return out

    # Absolute minimum: medium, the hard rule, the layout, the colour and the
    # lock. Everything except the style prose and the negatives — those two
    # are recoverable from the style contract, the rest are not.
    #
    # The arrangement is NOT recoverable: it is the only thing that
    # distinguishes this sheet from the other sheets in the set. So it
    # survives the absolute floor, ahead of the colour, and the print
    # mechanism gets whatever room is left.
    minimal = [
        _clip_sentences(medium_line, 160),
        no_photography or "",
        _clip_sentences(layout_line, 80),
        _clip_sentences(arrangement_line, 110),
        _clip_sentences(colour_line, 90),
        lock_line,
    ]
    out = "\n".join(k for k in minimal if k)
    if len(out) > budget:
        # The lock is the one clause that must not be silently lost. Trim the
        # medium until it fits rather than dropping the lock.
        lock_len = len(lock_line)
        room = max(0, budget - lock_len - 2)
        out = "\n".join(k for k in [
            _clip_sentences(medium_line, max(60, room)),
            no_photography or "",
            lock_line,
        ] if k)
    return out



def _needs_identity(profile: dict) -> bool:
    try:
        import face_identity
        return face_identity.has_face_risk(profile)
    except Exception:
        return False


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT / "scripts"))
    from compose_prompt import load, style_by_id
    from rank_styles import rank

    profile = load(sys.argv[1])
    style_id = sys.argv[2] if len(sys.argv) > 2 else rank(profile)["primary"]
    style = style_by_id(style_id)
    text = build_compact(profile, style)
    print(f"[{len(text)} chars, budget {DEFAULT_BUDGET}]\n")
    print(text)