#!/usr/bin/env python3
"""Layout variants — so three generated posters are three designs, not three samples.

Measured problem: `image-01` with `n=3` returns three samples of the SAME
prompt. They vary in rendering detail, not in design. Three prints of one
design is not what "give me three" means.

Measured constraint: the MiniMax API takes one prompt per request. There is no
batch-of-prompts field. So distinct designs require distinct requests.

This module supplies the per-variant LAYOUT directive that turns one prompt
into N prompts with genuinely different compositions: different crop, different
placement, different use of negative space — and, for the one style whose whole
concept is repetition, different arrangements of the copies.

Two rules govern every variant:

  1. It may only change ARRANGEMENT. Never the ink palette, never the medium,
     never the identity. A variant that changes the palette is a different
     style, not a different take on this one.
  2. It must obey the style's identity mode. `repeat` may arrange copies;
     `single` must not introduce a second face; `abstract` renders one
     derived figure as illustration.

The wording stays in print language. "Head fills the frame" is a layout
instruction; "close-up portrait, soft focus, natural light" is photography
vocabulary and drags the render back toward a photograph.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Variant sets, one per identity mode.
#
# Each variant is ONE sentence. That matters: the budget enforcement clips
# sections by whole sentences, so a two-sentence variant could lose its second
# half and leave a directive the model cannot act on.
# ---------------------------------------------------------------------------

REPEAT_VARIANTS = [
    (
        "column",
        "Three copies of the same face in a tight vertical column down the "
        "centre line, each one cropped by the one above it, the smallest at "
        "the bottom.",
    ),
    (
        "echo",
        "One large copy of the same face filling the upper half of the sheet, "
        "with two smaller copies of the same face stepping down the right edge "
        "like an echo.",
    ),
    (
        "cascade",
        "Four copies of the same face cascading diagonally from the upper left "
        "corner toward the lower right, overlapping each other like a spread "
        "of cards.",
    ),
    (
        "cluster",
        "Three copies of the same face clustered tightly into the lower right "
        "quarter of the sheet, tilted at different angles, with a wide empty "
        "field of bare paper across the upper left.",
    ),
    (
        "pair",
        "Two copies of the same face side by side across the middle of the "
        "sheet, one larger and one smaller, cropped at the shoulders so they "
        "share the horizontal centre line.",
    ),
]

SINGLE_VARIANTS = [
    (
        "close-centre",
        "Close crop on the head and shoulders, the subject centred and filling "
        "most of the frame, cropped just below the collar.",
    ),
    (
        "offset-left",
        "Half-body crop, the subject shifted onto the right third with the "
        "head near the upper third, a wide empty field of bare paper opening "
        "across the whole left half.",
    ),
    (
        "wide-low",
        "A small full-length subject placed low in the frame, a vast empty "
        "paper field above and around it, the figure small enough to read as a "
        "shape rather than a face.",
    ),
    (
        "edge",
        "The subject cropped hard against the left edge of the sheet, the "
        "head partly cut by the frame, all the empty paper falling to the "
        "right.",
    ),
    (
        "high-low",
        "The subject low and centred in the lower third, seen slightly from "
        "below, with an unbroken expanse of empty paper filling the upper two "
        "thirds.",
    ),
]

ABSTRACT_VARIANTS = [
    (
        "close-centre",
        "Close crop on the head and shoulders of the illustrated figure, "
        "centred and filling most of the frame, drawn as flat printed shapes "
        "rather than modelled in light.",
    ),
    (
        "offset-left",
        "Half-body illustrated figure shifted onto the right third with the "
        "head near the upper third, a wide empty field of bare paper opening "
        "across the whole left half.",
    ),
    (
        "wide-low",
        "A small illustrated figure placed low in the frame, a vast empty "
        "paper field above and around it, the figure read as a flat silhouette "
        "rather than a portrait.",
    ),
    (
        "edge",
        "The illustrated figure cropped hard against the left edge of the "
        "sheet, the head partly cut by the frame, all the empty paper falling "
        "to the right.",
    ),
    (
        "high-low",
        "The illustrated figure low and centred in the lower third, a wide "
        "empty expanse of paper filling the upper two thirds, the figure "
        "described by outline and gesture alone.",
    ),
]

SCENE_VARIANTS = [
    (
        "wide-low",
        "A wide establishing view with the subject small and low in the frame, "
        "a vast empty paper field filling most of the sheet above it.",
    ),
    (
        "tight",
        "A tight crop on the key form, filling the frame edge to edge so the "
        "subject reads as texture and shape rather than as a scene.",
    ),
    (
        "offset-left",
        "The subject pushed onto the right third of the sheet, a wide empty "
        "field of bare paper filling the whole left half.",
    ),
    (
        "diagonal",
        "The subject running on a strong diagonal from the lower left to the "
        "upper right, with the remaining paper cut into two clean triangular "
        "fields.",
    ),
    (
        "centre-band",
        "The subject arranged as a single horizontal band across the middle "
        "third of the sheet, with equal bands of empty paper above and below.",
    ),
]


def _select(pool: list, count: int) -> list:
    """Pick `count` distinct variants, spread across the pool.

    The pool is walked with a stride so consecutive variants differ in more
    than one axis — taking the first three in order would give three crops
    that all share a placement.
    """
    if count <= 0:
        return []
    n = len(pool)
    if count >= n:
        return list(pool)
    stride = 2 if n % count else 1
    picked, seen = [], set()
    i = 0
    while len(picked) < count and i < n * 2:
        idx = (i * stride) % n
        if idx not in seen:
            seen.add(idx)
            picked.append(pool[idx])
        i += 1
    return picked[:count]


def layout_variants(style: dict, count: int, identity_mode: str = "single",
                    has_face: bool = False) -> list:
    """Return `count` variant dicts for one style.

    Each dict has:
      id     a short slug, used in the filename and the report
      label  a human-readable name
      text   the ONE-sentence layout directive
    """
    style_id = style.get("id", "")
    if identity_mode == "repeat":
        pool = REPEAT_VARIANTS
    elif identity_mode == "abstract":
        pool = ABSTRACT_VARIANTS
    elif has_face:
        pool = SINGLE_VARIANTS
    else:
        pool = SCENE_VARIANTS

    out = []
    for slug, text in _select(pool, count):
        out.append({
            "id": slug,
            "label": slug.replace("-", " "),
            "text": text,
            "style_id": style_id,
        })
    return out


def default_variant(count: int, identity_mode: str = "single",
                    has_face: bool = False) -> dict:
    """The single variant used when only one image is requested."""
    variants = layout_variants(
        {"id": ""}, count or 1, identity_mode=identity_mode, has_face=has_face)
    return variants[0]
