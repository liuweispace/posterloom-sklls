#!/usr/bin/env python3
"""Generate style contract .md files from data/styles.json.

The library previously registered styles in JSON without a matching contract
file, so the agent's step "load the chosen style contract" silently failed for
those styles. Generating contracts from the JSON makes drift impossible: the
JSON stays the single source of truth.

Existing contracts are left untouched unless --force is passed.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLES_JSON = ROOT / "data/styles.json"
STYLES_DIR = ROOT / "styles"

EXEC_CONTRACT = """1. Treat the uploaded source photograph as the single factual and visual anchor.
2. Protect the scene-analysis identity anchors before stylization.
3. Produce one finished poster, not a collage, contact sheet, moodboard, scrapbook, album, or multi-panel layout.
4. Preserve source truth: do not invent people, brands, dates, landmarks, signatures, seals, costumes, or factual claims.
5. Apply this style through its actual visual mechanism, not a generic preset.
6. Keep typography subordinate to the image, normally no more than 5–10% of the visual area.
7. Use the source-derived palette unless the style contract explicitly permits a controlled reinterpretation.
8. Stop stylization before it damages identity, perspective, material plausibility, or cultural accuracy."""

HYBRID = """Direct styles may enter `Controlled Hybrid` only if their pair appears in `data/compatibility.json`. The primary keeps subject identity, composition, lighting, palette, and realism. The secondary controls one declared subsystem only."""

PORTRAIT_FAILURE = """- Generating a new or generic face when the source person must stay recognizable.
- Averaging the face toward a model-default or idealized look.
- Letting the style's medium reinterpret facial structure.
- Smoothing, reshaping, or beautifying the face.
- Losing source-specific anchors: eye shape, brow shape, hairline, skin tone, age cues.
- Placing typography or graphic elements across the face."""

PORTRAIT_SELFCHECK = """- Is this the same person as in the source, not a similar-looking invented person?
- Do face shape, eye shape/spacing, eyebrow shape, nose shape, mouth shape, hairline, and skin tone all match?
- Is the expression and gaze direction preserved?
- Are there no added beautifications, age shifts, or makeup?
- Is the face fully inside the frame with margin, and free of graphic overlays?"""

GENERIC_FAILURE = """- Applying the same texture or effect uniformly to every pixel.
- Replacing source-specific structure with generic AI imagery.
- Oversizing typography until text becomes the subject.
- Inventing content to make a style stereotype more obvious.
- Ignoring material differences between surfaces.
- Turning batch consistency into forced visual sameness."""

GENERIC_SELFCHECK = """- Is the source still immediately recognizable?
- Can major stylized elements be traced to the source or this style's mechanism?
- Is the composition materially different from a simple filter?
- Is text small, legible, and outside identity-critical regions?
- Are there invented facts, extra subjects, malformed structures, or fake characters?
- Does the output read as this style specifically rather than generic “AI art”?"""

ACCEPTANCE = """Use `references/visual-benchmark.md`. A production image should normally score at least 17/20 across identity, composition, lighting, palette, material behavior, edges, typography, source specificity, style specificity, and anti-slop quality."""


def bullets(values, empty="-"):
    items = list(values or [])
    return "\n".join(f"- {v}" for v in items) if items else empty


def is_portrait(style: dict) -> bool:
    return "portrait" in (style.get("family") or "") or style.get("id", "").endswith("-portrait") or style.get("id") == "photojournalistic"


def render(style: dict) -> str:
    portrait = is_portrait(style)
    failures = PORTRAIT_FAILURE + "\n" + GENERIC_FAILURE if portrait else GENERIC_FAILURE
    selfcheck = PORTRAIT_SELFCHECK + "\n" + GENERIC_SELFCHECK if portrait else GENERIC_SELFCHECK

    knobs = bullets(style.get("variation_knobs"))
    if portrait:
        knobs += "\n- likeness fidelity exact/strict"

    return f"""---
id: {style['id']}
name: {style['name']}
family: {style['family']}
role: {style['role']}
status: {style['status']}
---

# {style['name']}

## Style intent
{style['mechanism']}

## Best for
{bullets(style['best_for'])}

## Reject when
{bullets(style['reject_if'])}

## Style DNA
**Subject / identity behavior**  
{style['mechanism']}

**Composition strategy**  
{style['composition']}

**Lighting language**  
{style['lighting']}

**Color logic**  
{style['color_logic']}

**Material / texture language**  
{style['material_language']}

**Typography system**  
{style['typography']}

**Realism level**  
{style['realism']}

**Transformation strength**  
{style['transformation']}

## Execution contract
{EXEC_CONTRACT}

## Style-specific prompt block
{style['prompt_block']}

## Style-specific negative prompt
{style['negative_prompt']}

## Variation knobs
{knobs}

## Hybrid behavior
{HYBRID}

## Common failure modes
{failures}

## Self-check
{selfcheck}

## Acceptance criteria
{ACCEPTANCE}
"""


def existing_ids() -> set:
    ids = set()
    for path in STYLES_DIR.glob("*.md"):
        ids.add(re.sub(r"^\d+-", "", path.stem))
    return ids


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate missing style contract files.")
    ap.add_argument("--force", action="store_true", help="overwrite existing contracts")
    ap.add_argument("--prefix", action="store_true", help="keep the NN- filename prefix")
    args = ap.parse_args()

    data = json.loads(STYLES_JSON.read_text(encoding="utf-8"))
    styles = [s for s in data["styles"] if s.get("role") == "direct"]

    have = existing_ids()
    written, skipped = [], []

    for i, style in enumerate(styles, 1):
        sid = style["id"]
        target = STYLES_DIR / (f"{i:02d}-{sid}.md" if args.prefix else f"{sid}.md")
        if sid in have and not args.force:
            skipped.append(sid)
            continue
        target.write_text(render(style), encoding="utf-8")
        written.append(target.name)

    print(f"written: {len(written)}")
    for n in written:
        print(f"  + {n}")
    print(f"skipped (already present): {len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
