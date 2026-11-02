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
from functools import lru_cache

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


def to_print_language(text: str, mode: str = "print") -> str:
    """Rewrite photographic vocabulary into print vocabulary.

    `mode` is "print" for the flat-ink styles and "photographic" for a style
    whose subject needs continuous tone. A beauty portrait is the case in
    point: "skin texture" and "soft shadows" are the SUBJECT, and rewriting
    them into "ink texture" and "crushed shadow areas" destroys the thing
    the style exists to render. So the rewrite is skipped entirely for a
    photographic style rather than partially applied.
    """
    if not text:
        return ""
    if mode == "photographic":
        return re.sub(r"\s+", " ", str(text)).strip()
    out = str(text)
    for pattern, repl in PHOTOGRAPHIC_TO_PRINT:
        out = re.sub(pattern, repl, out, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out)
    out = re.sub(r"\s+([,.;:])", r"\1", out)
    return out.strip()

# Negative constraints that earn their place in a short prompt. Each one names a
# failure mode that would otherwise be the most likely outcome.
NEGATIVE_PRIORITY = [
    # Style-specific negatives come first. The generic identity negatives
    # below are already covered by the identity lock, so spending the
    # limited negative budget on them repeats what the lock says and
    # starves the ones that only the style knows about.
    # Short, robust tokens. The earlier keys ("no silver-white", "no pearls
    # inside the pupil") stopped matching when the wording in styles.json
    # changed, so the two most important negatives — no glitter, nothing
    # over the pupil — were silently dropped from the prompt.
    # NOTE: there is deliberately no "glitter" / "sparkle" / "shimmer" key.
    # The backend encodes the whole prompt as positive description, so
    # naming the unwanted concept inside a negation still plants it --
    # a prompt saying "no glitter specks" produced a face covered in
    # glitter specks. Those concepts are constrained by ABSENCE, not by
    # a named negative. The pearl-specific constraints come first.
    "rows of pearls", "pupil", "silver or blue-white",
    "heavy contouring", "harsh black eyeliner", "thick false lashes",
    "over-thick lipstick", "orange skin", "foundation mask",
    "patchy or cakey base", "grey-blue face cast",
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

# The beauty-mode lock. The makeup is the requested content, so it may not be
# suppressed — but the bone structure under it stays fixed. This is the compact
# counterpart of face_identity.BEAUTY_IDENTITY_BLOCK: the standard lock says
# "no makeup addition", which would make a beauty style a no-op.
IDENTITY_ESSENCE_BEAUTY = (
    'IDENTITY LOCK (highest priority, beauty mode): apply the makeup; bone structure MUST NOT change. Fixed: face shape, jawline, cheekbones, eye shape, spacing, brows, nose and lips, hairline, skin tone, age, expression, gaze. Beyond cosmetics: no smoothing, reshaping, or bigger eyes or lips.'
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
    "beauty": (
        'IDENTITY LOCK (highest priority, beauty mode): the makeup MUST be applied; the bone structure under it MUST NOT change. Fixed: face shape and jawline, cheekbones, eye shape and spacing, brows, nose and lips, hairline, skin tone, age, expression, gaze. Beyond the cosmetics: no smoothing, no reshaping, no bigger eyes or lips.'
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


def _pick_negative(negative_prompt: str, limit: int = 6,
                   priority: list = None) -> str:
    """Keep the negatives that matter most, not the first ones."""
    if not negative_prompt:
        return ""
    # Split on ", no " — the separator between negatives. Splitting on a
    # bare comma broke any negative that contained a comma of its own
    # ("no silver, blue-white or glitter specks" became "no silver" plus
    # "blue-white or glitter specks", and the second half lost its "no"
    # and read as a positive instruction).
    raw = [p.strip().rstrip(".") for p in re.split(r",\s*(?=no\b)", negative_prompt)
           if p.strip()]
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
    # A style can declare the negatives that are load-bearing for IT.
    # The generic priority list ranks by wording, so a style whose whole
    # point is the pearl arrangement could still lose those clauses to a
    # better-wording identity negative when the budget got tight.
    # Declared negatives are pinned; the rest fill the remaining slots.
    if priority:
        pinned = []
        for want in priority:
            wl = want.lower()
            for item in keep:
                if item.lower() == wl or item.lower().startswith(wl):
                    if item not in pinned:
                        pinned.append(item)
                    break
            else:
                for _, _, item in scored:
                    if item.lower() == wl or item.lower().startswith(wl):
                        if item not in pinned:
                            pinned.append(item)
                        break
        rest = [s[2] for s in scored if s[2] not in pinned]
        room = limit - len(pinned)
        if room < 0:
            # More pinned than the budget allows: keep them all, and let
            # the caller clip. Dropping a pinned clause would break the
            # style's core rule.
            return ", ".join(pinned)
        keep = pinned + rest[:room]
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
    # An explicit medium statement wins. A style whose subject NEEDS
    # continuous tone — a soft-focus beauty portrait, where the pearl
    # specular and the champagne highlight are the whole point — cannot be
    # expressed as posterised flat ink, and forcing it produces a print that
    # contradicts its own mechanism. Such a style declares its medium.
    declared = style.get("medium_statement")
    if declared:
        # No ink phrase. "Ink colours ... and nothing else" is print vocabulary
        # and it contradicts a photographic medium; the palette belongs in the
        # COLOUR section, which carries the hex values.
        return declared

    cs = style.get("color_system") or {}
    inks = cs.get("inks") or []
    n = len(inks) if inks else 2
    substrate = cs.get("substrate") or "chalky white paper"
    n_word = {1: "one-ink", 2: "two-ink", 3: "three-ink"}.get(n, f"{n}-ink")
    ink_phrase = ""
    if inks:
        ink_phrase = f" Ink colours: {', '.join(inks)} — and nothing else."
    return MEDIUM_TEMPLATE.format(n=n_word, technique=_technique(style), substrate=substrate) + ink_phrase


def _first_sentences(text: str, count: int, limit: int, mode: str = "print") -> str:
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
    sents = _sentences(to_print_language(text, mode=mode))
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


def _protocol_core(style: dict, mode: str = "print") -> str:
    """A style's named procedure, when it has one.

    Most styles' mechanism is a print discipline: "posterise", "map onto a
    ramp". For those, the mechanism can live in the optional STYLE section —
    if the budget squeezes it, the sheet is still recognisably that style.

    A style whose MECHANISM IS THE CONTENT is different. A beauty style's
    content IS the four-step protocol and the pearl placement; drop it and
    what remains is a generic studio portrait of a person. That content must
    be a REQUIRED section, so it is stated separately from the mechanism and
    cannot be evicted by the budget.
    """
    proto = style.get("protocol")
    if not proto:
        return ""
    # Return the protocol UNCLIPPED. The caller knows the real budget; a
    # fixed 520 here clipped a protocol that had to fit in ~370, so the
    # steps were cut mid-word instead of being dropped cleanly. The caller
    # clips on step boundaries via _clip_steps.
    return to_print_language(str(proto), mode=mode)


def _look_core(style: dict, mode: str = "print") -> str:
    """The style's own lighting and colour logic, as one section.

    Lighting is where a photographic style lives or dies: a studio beauty
    portrait and a window-lit candid are different images with the same
    makeup. This section carries the style's declared light setup and its
    colour logic, clipped to whole sentences so the operative clause is
    never cut in half.
    """
    include = style.get("look_include") or []
    bits = []
    if "lighting" in include:
        # Take every sentence of the lighting setup, not just the first two.
        # A studio light rig is a set — key direction, wrap, falloff and
        # backdrop colour are one description. Cutting it to two sentences
        # dropped the backdrop, which is not a detail but half the look.
        # The length limit still applies, and clipping happens on whole
        # sentences.
        light = _first_sentences(style.get("lighting", ""), 99, 300, mode=mode)
        if light:
            bits.append(light)
    if "color_logic" in include:
        colour_logic = _first_sentences(style.get("color_logic", ""), 1, 200, mode=mode)
        if colour_logic:
            bits.append(colour_logic)
    return " ".join(bits)


def _style_core(style: dict, mode: str = "print") -> str:
    """The style's mechanism plus its material and typography, in print terms."""
    bits = []
    mech = _first_sentences(style.get("mechanism", ""), 2, 300, mode=mode)
    if mech:
        bits.append(mech)
    mat = _first_sentences(style.get("material_language", ""), 1, 140, mode=mode)
    if mat:
        bits.append("Surface: " + mat)
    typo = _first_sentences(style.get("typography", ""), 1, 130, mode=mode)
    if typo:
        bits.append("Type: " + typo)
    return " ".join(bits)


def _color_core(style: dict, max_ramps: int = 1, limit: int = 0,
                mode: str = "print") -> str:
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

    label = "Palette" if mode == "photographic" else "Inks"

    def build(with_accent: bool, with_coverage: bool, ramps: int) -> str:
        parts = []
        if cs.get("inks"):
            parts.append(f"{label}: {', '.join(cs['inks'])}")
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


def _clip_steps_impl(text: str, limit: int, prefer_complete: bool = True) -> str:
    """Trim a step-wise protocol without cutting a step in half.

    A protocol is written as numbered steps separated by semicolons, e.g.
    "(1) ...; (2) ...; (3) ...". The generic sentence splitter treats a
    semicolon as a sentence boundary, so clipping it to a limit keeps only
    the first fragment and silently drops steps 2 and 3 — which for a makeup
    protocol means the highlight and the eye work never get described.

    So a protocol is clipped on its step boundaries instead. A step that is
    itself too long is clipped by character, but the step's leading marker
    is kept, so the model can still tell how many steps it has.
    """
    if not text:
        return ""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    # Split on the step markers, keeping the marker attached to its step.
    parts = re.split(r"(?=\(\d\))", text)
    parts = [p for p in parts if p.strip()]
    # A trailing named clause ("Pearls: ...") is its own logical unit. Without
    # this it is glued to the previous step, and clipping that step away takes
    # the clause with it — which is how the pearl placement, the signature of
    # the whole style, silently disappeared.
    split_parts = []
    for part in parts:
        m = re.match(r"^(\s*)([A-Z][A-Za-z ]{2,24}:)\s*(.*)$", part, re.S)
        if m and m.group(3).strip() and not part.lstrip().startswith("("):
            split_parts.append(m.group(1) + m.group(2) + " ")
            split_parts.append(m.group(3))
        else:
            split_parts.append(part)
    parts = [p for p in split_parts if p.strip()]
    out, total = [], 0
    for part in parts:
        add = len(part) + (1 if out else 0)
        if total + add > limit:
            break
        out.append(part)
        total += add
    if out:
        # Whole steps fit. Use them — unless a complete version (every step
        # present, each one shorter) also fits, in which case that one is
        # better: it keeps the whole procedure.
        complete = _shrink_steps(parts, limit)
        if prefer_complete and complete and len(complete) <= limit:
            # The complete version is preferred even when it is LONGER.
            # Length is not the metric here: dropping step (3) and (4) from a
            # makeup protocol is a different look, not a shorter description
            # of the same one. Keeping every step with less detail per step
            # is the correct trade.
            return complete
        return " ".join(out).rstrip()

    # They do not. Shrink EACH step instead of dropping steps.
    #
    # Dropping a step is the wrong degradation for a protocol: a makeup
    # protocol that survives with steps (1) and (2) only has no eye work and
    # no blush, which is a different look rather than a shorter description
    # of the same one. Shrinking each step keeps every instruction in play
    # and only drops the words that decorate it.
    return _shrink_steps(parts, limit)


def _shrink_steps(parts: list, limit: int) -> str:
    """Keep EVERY step, but make each one shorter.

    This is the only correct degradation for a protocol. Dropping step (3)
    means the eye work never happens; that is a different look, not a shorter
    description of the same one. Shrinking each step keeps every instruction
    in play and only drops the words that decorate it.
    """
    if not parts:
        return ""
    total = sum(len(p) for p in parts)
    if total <= limit:
        return " ".join(p for p in parts if p.strip())

    # Distribute the budget PROPORTIONALLY, not evenly.
    #
    # Even distribution gives every part the same allowance, so a long
    # step and a short one both end up cut to the same length — and a step
    # cut to a fragment is not an instruction the model can act on. Proportional
    # allocation keeps each part's share of its own content, so every step
    # survives as a readable clause.
    #
    # The floor matters too: a step must keep enough of its own words to
    # remain actionable. Below ~34 characters a step is a stub, so the
    # budget is redistributed to the steps that still have room.
    MIN_STEP = 34
    lengths = [len(p) for p in parts]
    share = [max(MIN_STEP, int(limit * l / total)) for l in lengths]
    # If the floors overflow the budget, scale the floors down together.
    if sum(share) > limit:
        scale = limit / sum(share)
        share = [max(16, int(s * scale)) for s in share]
    # Give any leftover to the parts that were cut hardest.
    leftover = limit - sum(share)
    if leftover > 0:
        order = sorted(range(len(parts)), key=lambda i: lengths[i] - share[i], reverse=True)
        i = 0
        while leftover > 0 and order:
            j = order[i % len(order)]
            if lengths[j] - share[j] > 0:
                share[j] += 1
                leftover -= 1
            i += 1
            if i > len(order) * 3:
                break

    shrunk = []
    for part, allow in zip(parts, share):
        if len(part) <= allow:
            shrunk.append(part)
            continue
        m = re.match(r"(\([^)]*\)|[A-Z][A-Za-z ]{2,24}:)", part.strip())
        if m:
            marker = m.group(1)
            rest = part.strip()[len(marker):]
            shrunk.append(marker + " " + _clip_clauses(
                rest, max(0, allow - len(marker) - 1)))
        else:
            shrunk.append(_clip_clauses(part, allow))
    return " ".join(x for x in shrunk if x.strip())


_INTACT_CACHE: dict = {}
_SCORE_CACHE: dict = {}


def _protocol_intact(clipped: str, source: str) -> bool:
    """Cached wrapper around the strict protocol check.

    The candidate search evaluates hundreds of thousands of prompts, and
    the check runs three regex passes each time. Caching on the clipped
    protocol text makes the search cost a dictionary lookup instead of a
    regex sweep — without the cache, build_compact pegged the CPU at
    64% for minutes and never returned.
    """
    if not source:
        return True
    key = (clipped, source)
    hit = _INTACT_CACHE.get(key)
    if hit is None:
        hit = _protocol_intact_uncached(clipped, source)
        if len(_INTACT_CACHE) > 4096:
            _INTACT_CACHE.clear()
        _INTACT_CACHE[key] = hit
    return hit


def _protocol_intact_uncached(clipped: str, source: str) -> bool:
    """True when every numbered step and the trailing clause survived whole.

    The clipper may shorten a step by dropping its tail, so "the step is
    present" is not enough — the step's full text has to be present. The
    trailing named clause (the pearl rule) is checked the same way.
    """
    if not source:
        return True
    src = " ".join(str(source).split())
    got = " ".join(str(clipped).split())
    # The numbered steps.
    src_steps = re.findall(r"\(\d\)\s*([^;]*)", src)
    got_steps = re.findall(r"\(\d\)\s*([^;]*)", got)
    if len(src_steps) < 4 or len(got_steps) < len(src_steps):
        return False
    for s_step, g_step in zip(src_steps, got_steps):
        if s_step.strip() not in g_step:
            return False
    # The trailing named clause, e.g. "Pearls: ...".
    m = re.search(r"([A-Z][A-Za-z ]{2,24}:)\s*([^;]+)$", src)
    if m:
        label, body = m.group(1), m.group(2).strip()
        gm = re.search(re.escape(label) + r"\s*(.*)$", got)
        if not gm or body not in gm.group(1):
            return False
    return True


def _score_sections(proto: str, look: str, avoid: str, layout: str,
                    look_source: str, avoid_source: str,
                    style: dict = None) -> tuple:
    """Score a candidate from its section texts.

    Split out from _completeness_score so the search loop can rank a
    candidate without assembling and re-splitting the whole prompt
    string. The search evaluates hundreds of thousands of candidates and
    the string work dominated the runtime.

    The score depends only on the four section texts and the sources, and
    the search revisits the same section texts over and over — the
    protocol alone has eleven possible lengths, so the distinct
    combinations are a tiny fraction of the candidate count. Memoising
    here removes the last hot spot in the search.
    """
    key = (proto, look, avoid, layout, look_source, avoid_source,
           id(style) if style is not None else 0)
    hit = _SCORE_CACHE.get(key)
    if hit is None:
        hit = _score_sections_impl(
            proto, look, avoid, layout, look_source, avoid_source, style)
        if len(_SCORE_CACHE) > 65536:
            _SCORE_CACHE.clear()
        _SCORE_CACHE[key] = hit
    return hit


def _completeness_score(candidate: str, look_source: str = "",
                        avoid_source: str = "",
                        style: dict = None) -> tuple:
    """Rank candidate prompts by how much of each section survived.

    Thin wrapper: extract the sections from the assembled prompt, then
    delegate to _score_sections.
    """
    def section(prefix):
        for line in candidate.split("\n"):
            if line.startswith(prefix):
                return line
        return ""
    return _score_sections(
        section("PROTOCOL:"), section("LOOK:"), section("AVOID:"),
        section("LAYOUT:"), look_source, avoid_source, style)


def _score_sections_impl(proto: str, look: str, avoid: str, layout: str,
                         look_source: str, avoid_source: str,
                         style: dict = None) -> tuple:
    """Rank a candidate from its section texts.

    Length alone is the wrong metric — a candidate that fits by throwing
    away the negatives is not better than one that fits by shortening the
    layout. What matters is that every section keeps its content, and
    especially that the protocol (the content of the image) and the
    negatives (what stop the pearls turning into glitter) are whole.

    The tuple is compared lexicographically: protocol first, then the
    negatives, then the look, then everything else.
    """
    proto = proto
    avoid = avoid
    look = look
    layout = layout
    # A protocol is complete when it still carries every numbered step
    # and its trailing clause (for the pearl style, the bead rule).
    # A protocol is complete only when every step still carries real
    # content. Counting "(" was not enough: _shrink_steps renders the
    # markers as "(1)  " with padding, so a protocol whose steps had all
    # been cut to fragments still counted four and was scored as whole.
    steps = re.findall(r"\((\d)\)\s*([^()]*)", proto)
    # Strict: every source step must survive WHOLE, not just as a stub.
    # The previous test only checked that each step had >=12 characters,
    # so a protocol clipped mid-clause ("thin semi-matte base" cut out of
    # "thin semi-matte base, skin texture visible") still counted as
    # complete and beat a shorter-but-intact protocol.
    proto_complete = (
        len(steps) >= 4
        and all(len(body.strip()) >= 12 for _, body in steps)
        and _protocol_intact(
            proto, (style or {}).get("protocol", ""))
    )
    avoid_items = avoid.count(",") + (1 if avoid else 0)
    # Order matters. The protocol must be whole (it is the content), then
    # the negatives must be whole (they are what make the pearls read as
    # beads rather than glitter), then the LOOK must be whole (the studio
    # rig and the cold-white backdrop are the style's signature). Raw
    # protocol LENGTH comes last among these: a longer protocol that
    # squeezes the backdrop out is not better, it is a different image.
    # Priority order, and the reasoning behind it:
    #   1. the protocol must be whole — it IS the content of the image
    #   2. then how much of the protocol survived — a longer protocol is
    #      more of the procedure, and it is what the budget should protect
    #   3. then how many distinct negatives survived — they are what turn
    #      the pearls into beads instead of glitter
    #   4. then the LOOK section, then the layout
    # Raw negative LENGTH ranks below the protocol on purpose: one long
    # negative is worth less than the protocol's pearl-placement clause.
    # How many sentences did each section keep, relative to its source?
    # A section that lost its last clause is not "a bit shorter" — it is
    # missing a decision (the backdrop, the light hierarchy). Counting
    # kept clauses ranks that above raw character length, which is what
    # made a slightly longer protocol beat a complete LOOK.
    def kept_sentences(section_text, source_sentences):
        if not section_text or not source_sentences:
            return 0
        return sum(1 for sent in source_sentences if sent.strip() in section_text)

    look_kept = kept_sentences(look, _sentences(look_source))
    # Count how many of the source's hard constraints survived. Counting
    # the CLIPPED count instead made a candidate with 3 constraints tie
    # with one that kept all 6, so the search had no reason to protect
    # the constraint list.
    avoid_src_clauses = [
        c.strip().rstrip(".") for c in re.split(r",\s*(?=no\b)", avoid_source)
        if c.strip()
    ] if avoid_source else []
    avoid_kept = (
        sum(1 for c in avoid_src_clauses if c in avoid)
        if avoid_src_clauses else min(avoid_items, 8)
    )
    # Every clause the AVOID section ends up with counts, and the LOOK
    # section's sentence count counts too. Comparing raw LENGTH let a
    # longer protocol push the light hierarchy and the hard constraints
    # out of the prompt — the two things a beauty style cannot lose.
    # Comparing the number of retained CLAUSES keeps those sections whole
    # and trims detail words instead.
    # Order matters: a section that LOST a whole clause is missing a
    # decision, which is worse than a section that is merely shorter.
    # Ranking raw length ahead of clause coverage let a longer protocol
    # push the LOOK light hierarchy out of the prompt entirely — the
    # model then had no key light direction and no backdrop.
    return (
        1 if proto_complete else 0,
        look_kept,
        len(proto),
        avoid_kept,
        len(look),
        len(avoid),
        len(layout),
    )


def _clip_clauses_impl(text: str, limit: int) -> str:
    """Clip a comma-separated list of short phrases on clause boundaries.

    The negatives are independent phrases ("no glitter specks", "no rows
    of pearls"). Cutting one in half leaves a phrase that reads as damage,
    and dropping half a phrase loses the constraint. So they are dropped
    whole, shortest-loss first.
    """
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    parts = [p for p in text.split(", ") if p.strip()]
    kept = []
    total = 0
    for p in parts:
        add = len(p) + (2 if kept else 0)
        if total + add > limit and kept:
            break
        kept.append(p)
        total += add
    return ", ".join(kept)


def _clip_words(text: str, limit: int) -> str:
    """Clip to a word boundary, so a step never ends mid-word.

    A step cut at an arbitrary character ("skin texture" -> "skin t") reads
    as damage rather than as a shorter instruction, and the model has to
    guess what was cut. Clipping on a space keeps every surviving word
    intact.
    """
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    if limit <= 0:
        return ""
    cut = text[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:")


# --- memoisation for the candidate search -------------------------------
#
# build_compact evaluates the cross product of nine section limits
# (protocol x look x avoid x arrangement x style x subject x source x
# layout x colour), roughly five million candidates per lock variant.
# Every one of them re-clipped every section from scratch, so the search
# took 75 seconds and pegged the CPU — a render never finished.
#
# These three helpers are pure: the same (text, limit) always yields the
# same output, and only a handful of limit values are ever tried per
# section. Caching them turns the search from re-deriving every clip
# into a dictionary lookup.

@lru_cache(maxsize=8192)
def _clip_sentences_cached(text: str, limit: int) -> str:
    return _clip_sentences_impl(text, limit)


@lru_cache(maxsize=8192)
def _clip_clauses_cached(text: str, limit: int) -> str:
    return _clip_clauses_impl(text, limit)


@lru_cache(maxsize=8192)
def _clip_steps_cached(text: str, limit: int) -> str:
    return _clip_steps_impl(text, limit)



def _clip_sentences_impl(text: str, limit: int) -> str:
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
        # A separator is needed BETWEEN sentences, not after the last one.
        # Counting it after every sentence made the effective limit one
        # character per sentence too small, so a section that fitted
        # exactly lost its final clause.
        need = len(s) + (1 if out else 0)
        if total + need > limit and out:
            break
        out.append(s)
        total += need
    if out:
        # A single sentence may still exceed the limit — clip it.
        joined = " ".join(out)
        return _clip(joined, limit) if len(joined) > limit else joined
    return _clip(text, limit)




# Public, memoised entry points. The search loop calls these.
_clip_sentences = _clip_sentences_cached
_clip_clauses = _clip_clauses_cached
_clip_steps = _clip_steps_cached

def _subject_core(profile: dict, style: dict, mode: str = "print") -> str:
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
    # A style that declares its own lighting setup can override the subject
    # summary. Otherwise the photo's own description ("soft window light
    # from the left") contradicts the style's setup, and the model resolves
    # the contradiction by dropping one of them — usually the style's.
    summary = str(style.get("subject_summary")
                  or subject.get("summary", "")).strip()
    if summary:
        bits.append(f"Subject: {to_print_language(summary, mode=mode)}")
    else:
        stype = str(subject.get("type", "")).strip()
        if stype:
            bits.append(f"Subject: {stype}")

    # A style may declare which scene fields it wants carried over.
    #
    # The default is all of them, and that is right for most styles: the
    # scene's light and mood describe the source photo, and the style
    # renders it as it is.
    #
    # But a style that DECLARES its own lighting setup and its own backdrop
    # must not also inherit the photo's "window light from the left" — the
    # two contradict each other, and the model resolves the contradiction by
    # ignoring the style. Restricting the carried fields is what makes the
    # style's own setup authoritative. It also saves budget, which matters
    # because the protocol is what must survive.
    allowed = style.get("subject_fields")
    fields = (("lighting", "Value"), ("mood", "Mood"),
              ("materials", "Materials"), ("geometry", "Layout"))
    for key, label in fields:
        if allowed is not None and key not in allowed:
            continue
        vals = [str(v) for v in (profile.get(key) or [])][:3]
        if vals:
            bits.append(f"{label}: {', '.join(to_print_language(v, mode=mode) for v in vals)}")
    if allowed is None or "environment" in allowed:
        if profile.get("environment"):
            bits.append(f"Setting: {to_print_language(str(profile['environment']), mode=mode)}")
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
    declared_source = style.get("source_statement")
    if declared_source:
        return str(declared_source)
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

    # A style that declares its own medium is a photographic style: its
    # subject needs continuous tone, and the print vocabulary would destroy
    # the thing the style exists to render.
    render_mode = "photographic" if style.get("medium_statement") else "print"

    mode = identity_mode(style.get("id"))
    identity = {
        "repeat": IDENTITY_ESSENCE_REPEAT,
        "abstract": IDENTITY_ESSENCE_ABSTRACT,
        "beauty": IDENTITY_ESSENCE_BEAUTY,
        "single": IDENTITY_ESSENCE,
    }[mode]

    source = _source_role_clause(style, described=bool(subject_override))
    subject = subject_override if subject_override else _subject_core(
        profile, style, mode=render_mode)
    medium = _medium_sentence(style)
    needs_lock = _needs_identity(profile)
    # The composition is what makes the stack a stack. The mechanism sentence
    # says "repeat as a stack" but the arrangement itself lives in the
    # composition field, and without it the model renders a single portrait.
    composition = _first_sentences(
        style.get("composition", ""), 1, 240, mode=render_mode)
    # A photographic style names its palette inside the protocol already
    # ("champagne-gold highlight", "matte apricot blush", "cool ivory
    # pearl"), so its COLOUR section only needs the hex values as backup.
    # A print style still needs the full list, because the medium statement
    # is what makes the model pick its own palette otherwise.
    colour_limit = 110 if render_mode == "photographic" else 220
    colour = ""
    if style.get("color_system") and not style.get("palette_in_protocol"):
        colour = _color_core(style, max_ramps=1, limit=colour_limit,
                             mode=render_mode)
    lock_text = identity if needs_lock else ""

    # The negatives, inline.
    #
    # MiniMax image-01 has no negative_prompt field, so a style's negative
    # constraints only reach the model if they are written into the prompt.
    # The compact path had no "avoid" section at all, which meant every
    # style's negative_prompt was silently dropped — measured on the pearl
    # beauty style, where the pearls rendered as glitter instead of beads
    # because nothing said "no glitter" in the text that was actually sent.
    avoid = _pick_negative(style.get("negative_prompt", ""), 6,
                           style.get("priority_negative"))

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
    style_core = _style_core(style, mode=render_mode)
    protocol = _protocol_core(style, mode=render_mode)
    # The style's own LIGHTING and COLOUR logic. These were previously
    # dropped — only the mechanism, material and typography reached the
    # prompt. For most styles that is survivable because the mechanism
    # implies the light. For a style whose whole visual system IS a lighting
    # setup (a studio beauty portrait), dropping it makes the style a
    # generic portrait with the right palette.
    # Opt-in. Adding this section to every style would reallocate the
    # budget for the whole library — a change well beyond one new style.
    # A style opts in by declaring look_include.
    look = ""
    if style.get("look_include"):
        look = _look_core(style, mode=render_mode)
    required = [
        ("medium", medium, 200),
        ("source", source, 150),
        ("subject", subject, 230),
        ("layout", composition, 100),
        ("arrangement", arrangement, 60),
        ("colour", colour, 90),
        ("avoid", avoid, 60),
        ("lock", lock_text, 0),
    ]
    # The protocol sits right after the subject: it IS the content of a
    # beauty-style image, so it is required and it is placed where the model
    # reads it before the identity lock explains that the makeup is allowed.
    if protocol:
        required.insert(3, ("protocol", protocol, 240))
    # The look section carries the style's declared lighting. It goes right
    # after the protocol — the makeup says WHAT the face looks like, the
    # look says HOW it is lit, and the two have to agree.
    if look:
        required.insert(4, ("look", look, 120))
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
        ("avoid", _pick_negative(style.get("negative_prompt", ""), 6,
                                  style.get("priority_negative")), 60),
    ]
    if arrangement:
        # STYLE is already in the required set — do not emit it twice.
        optional = [o for o in optional if o[0] != "style"]

    # Spend the budget: keep every required section, then add the optional
    # ones if they fit, then clip the required ones toward their floors.
    # The medium statement is the highest-leverage sentence, so it gets more
    # room than the 240 the print template needed, and a style that declares
    # its own medium must not be prefixed with the print template's opener.
    labels = {"medium": None, "source": None, "subject": "Subject:",
              "protocol": "PROTOCOL:", "look": "LOOK:", "layout": "LAYOUT:",
              "arrangement": "ARRANGEMENT:", "colour": "COLOUR:",
              "lock": "IDENTITY LOCK", "style": "STYLE ", "avoid": "AVOID:"}
    if style.get("medium_statement"):
        labels["medium"] = None

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


    def assembled_length(req, labels):
        """Length of the prompt that build(req, []) would produce.

        The candidate search measures millions of prompts and most of
        them are too long, so joining the strings only for the ones that
        fit is much cheaper than joining every one of them.
        """
        total = 0
        count = 0
        for name, text, _floor in req:
            if not text:
                continue
            lab = labels.get(name)
            if lab and not text.startswith(lab):
                total += len(lab) + 1 + len(text)
            else:
                total += len(text)
            count += 1
        if count:
            total += count - 1
        return total


    # The candidate search is a cross product of nine section limits, so
    # the same section content is assembled into millions of prompts.
    # Scoring only reads the sections, not the assembled string, so the
    # score is computed from the section texts directly — no string join
    # per candidate. The join happens once, for the winner.
    def score_parts(parts, look_src, avoid_src, style_obj):
        """Rank a candidate from its section texts.

        `look_src` and `avoid_src` are the FULL source texts; the parts
        carry the clipped versions.
        """
        proto_text = ""
        look_text = ""
        avoid_text = ""
        layout_text = ""
        for name, text, _floor in parts:
            if name == "protocol":
                proto_text = text
            elif name == "look":
                look_text = text
            elif name == "avoid":
                avoid_text = text
            elif name == "layout":
                layout_text = text
        return _score_sections(
            proto_text, look_text, avoid_text, layout_text,
            look_src, avoid_src, style_obj)

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
    # De-duplicate: for some modes the "short" form is not shorter.
    if needs_lock and short_lock and short_lock == lock_text:
        lock_variants = (lock_text,)
    # A declared medium statement carries the print/photo decision, so it
    # needs more room than the 240 the print template's single sentence used.
    # Clipping it to 240 cut it mid-clause and lost the "never as a flat print"
    # instruction — which is the whole reason the style declares a medium.
    med_limit, med_floor = (420, 300) if style.get("medium_statement") else (240, 200)
    prot_limit, prot_floor = (520, 260) if protocol else (0, 0)
    look_limit, look_floor = (300, 120) if look else (0, 0)
    # Keep the BEST candidate, not the first that fits.
    #
    # First-fit returned whichever combination happened to fit
    # first, which could clip the LOOK section and the negatives while
    # leaving the protocol whole. The protocol is the content, but the
    # negatives are what make the pearls read as beads, so both have
    # to survive. Score every candidate and keep the most complete one.
    best = None
    best_score = None
    for lock in lock_variants:
        if not lock and needs_lock:
            continue
        for subj in (400, 320, 260, 230, 190, 150, 120, 100):
            for src in (None, 320, 260, 200, 150):
                for lay in (240, 180, 140, 100, 60):
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
                        # The protocol's limit is part of the search, not a
                        # constant. When the other sections already fill the
                        # budget, a fixed protocol limit meant the protocol
                        # was the only section that had to give way — and its
                        # degradation (dropping whole steps) is the one that
                        # changes the look. Searching the limit lets the
                        # protocol shrink gently while everything else holds.
                        # The protocol's own full length is a candidate.
                        # Without it the search starts below the source
                        # length, so every candidate that fits has the
                        # protocol already clipped — the full procedure is
                        # never even on the table.
                        full_prot = len(protocol)
                        prot_limits = (
                            (full_prot, prot_limit, 470, 440, 420, 400, 380, 350, 320, 290, 260)
                            if protocol else (0,))
                        full_look = len(look)
                        # The look's own length first, then progressively
                        # shorter versions. The clip happens on whole
                        # sentences, so a shorter limit drops a sentence
                        # rather than truncating one.
                        look_limits = (
                            (full_look, 300, 240, 190, 150, 110)
                            if look else (0,))
                        # The negatives shrink too. With them fixed, no
                        # candidate carried the full protocol: the search
                        # could only clip the protocol down to make room,
                        # and the protocol is the content.
                        avoid_limits = (
                            (len(avoid), 150, 120, 90, 60) if avoid else (0,))
                        for prot_lim in prot_limits:
                          for look_lim in look_limits:
                            for avoid_lim in avoid_limits:
                              for arr_lim in arr_limits:
                                for sty_lim in sty_limits:
                                  req = [
                                      ("medium", _clip_sentences(medium, med_limit), med_floor),
                                      ("source", source if src is None else _clip_sentences(source, src), 150),
                                      ("subject", _clip_sentences(subject, subj), 150),
                                      ("protocol", _clip_steps(protocol, prot_lim), prot_floor),
                                      ("look", _clip_sentences(look, look_lim), look_floor),
                                      ("layout", _clip_sentences(composition, lay), 100),
                                      ("arrangement", arrangement if arr_lim is None
                                       else _clip_sentences(arrangement, arr_lim), 60),
                                      ("colour", colour if col is None else _clip_sentences(colour, col), 70),
                                      ("avoid", _clip_clauses(avoid, avoid_lim), 60),
                                      ("lock", lock, 0),
                                  ]
                                  if arrangement:
                                      req.append(("style", _clip_sentences(
                                          style_core, sty_lim), 120))
                                  # Measure without joining. The prompt
                                  # is the parts joined by newlines, so its
                                  # length is the sum of the part lengths
                                  # plus one separator each. Building the
                                  # string for every candidate was the
                                  # single biggest cost in the search.
                                  if assembled_length(req, labels) <= budget:
                                      score = score_parts(
                                          req, look, avoid, style)
                                      if best_score is None or score > best_score:
                                          best_score = score
                                          best = build(req, [])

    if best is not None:
        return _enforce_budget(best, budget, style, needs_lock)

    # Absolute floor: the medium, the source rule, the subject, the lock.
    # NO PHOTOGRAPHY survives here because it is a hard constraint, not a
    # stylistic preference.
    req = [
        ("medium", _clip_sentences(medium, med_limit), med_floor),
        ("source", _clip_sentences(source, 240), 150),
        ("subject", _clip_sentences(subject, 150), 150),
        ("protocol", _clip_steps(protocol, prot_limit), prot_floor),
        ("look", _clip_sentences(look, look_limit), look_floor),
        ("avoid", avoid, 60),
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
    med_limit = 420 if style.get("medium_statement") else 240
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
    order = ["AVOID:", "STYLE ", "ARRANGEMENT:", "COLOUR:", "LOOK:", "LAYOUT:",
             "Subject:", "PROTOCOL:"]
    floors = {"AVOID:": 0, "STYLE ": 60, "ARRANGEMENT:": 60,
              "COLOUR:": 60, "LOOK:": 80, "LAYOUT:": 80, "Subject:": 100,
              "PROTOCOL:": 200}

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
    medium_line = next(
        (l for l in lines
         if l.startswith("A flat ") or l.startswith("A high-end studio")
         or l.startswith("A photographic ")
         or (style.get("medium_statement")
             and l.startswith(style["medium_statement"][:40]))),
        "")
    subject_line = next((l for l in lines if l.startswith("Subject:")), "")
    protocol_line = next((l for l in lines if l.startswith("PROTOCOL:")), "")
    look_line = next((l for l in lines if l.startswith("LOOK:")), "")
    layout_line = next((l for l in lines if l.startswith("LAYOUT:")), "")
    arrangement_line = next((l for l in lines if l.startswith("ARRANGEMENT:")), "")
    colour_line = next((l for l in lines if l.startswith("COLOUR:")), "")
    source_line = next((l for l in lines
                        if l.startswith("NO PHOTOGRAPHY") or l.startswith("The subject below")
                        or l.startswith("Use the source photograph")), "")
    lock_line = next((l for l in lines if l.startswith("IDENTITY LOCK")), "")

    # The NO PHOTOGRAPHY rule is a hard constraint and is never clipped.
    keep = [
        _clip_sentences(medium_line, med_limit),
        source_line if no_photography else _clip_sentences(source_line, 220),
        _clip_sentences(subject_line, 140),
        _clip_steps(protocol_line, 520),
        _clip_sentences(look_line, 300),
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
        _clip_sentences(medium_line, med_limit),
        no_photography or "",
        _clip_steps(protocol_line, 460),
        _clip_sentences(look_line, 240),
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

