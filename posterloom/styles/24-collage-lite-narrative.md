---
id: collage-lite-narrative
name: Collage-Lite Narrative
family: conceptual-hybrid
role: direct
status: gold
---

# Collage-Lite Narrative

## Style intent
Keep one principal representation of the subject. Supporting pieces may only be derived from the same source image; never turn one source into a fake multi-photo story.

## Best for
- culture
- architecture
- travel
- portrait
- objects
- story-rich scenes

## Reject when
- the user forbids any collage behavior
- minimal single-symbol treatment is better
- the source is already visually overloaded

## Style DNA
**Subject / identity behavior**  
Keep one principal representation of the subject. Supporting pieces may only be derived from the same source image; never turn one source into a fake multi-photo story.

**Composition strategy**  
Use one hero image plus only 1–3 source-derived fragments or textures. Never build a contact sheet, moodboard, or multi-photo grid.

**Lighting language**  
Keep the hero's lighting intact and harmonize fragments tonally.

**Color logic**  
Use one source-derived color system across all fragments and paper fields.

**Material / texture language**  
Use torn paper, translucent overlays, archival paper, print grain, or framing sparingly and only to support the source narrative.

**Typography system**  
Independent-culture-magazine style: small title and optional tiny metadata-like line.

**Realism level**  
medium

**Transformation strength**  
medium-high

## Execution contract
1. Treat the uploaded source photograph as the single factual and visual anchor.
2. Protect the scene-analysis identity anchors before stylization.
3. Produce one finished poster, not a collage, contact sheet, moodboard, scrapbook, album, or multi-panel layout.
4. Preserve source truth: do not invent people, brands, dates, landmarks, signatures, seals, costumes, or factual claims.
5. Apply this style through its actual visual mechanism, not a generic preset.
6. Keep typography subordinate to the image, normally no more than 5–10% of the visual area.
7. Use the source-derived palette unless the style contract explicitly permits a controlled reinterpretation.
8. Stop stylization before it damages identity, perspective, material plausibility, or cultural accuracy.

## Style-specific prompt block
Transform the single source photograph using the **Collage-Lite Narrative** visual system. Treat the photograph as the factual anchor and preserve all identity anchors before stylization.

Mechanism: Keep one principal representation of the subject. Supporting pieces may only be derived from the same source image; never turn one source into a fake multi-photo story.

Composition: Use one hero image plus only 1–3 source-derived fragments or textures. Never build a contact sheet, moodboard, or multi-photo grid.

Lighting: Keep the hero's lighting intact and harmonize fragments tonally.

Color: Use one source-derived color system across all fragments and paper fields.

Material and texture: Use torn paper, translucent overlays, archival paper, print grain, or framing sparingly and only to support the source narrative.

Typography: Independent-culture-magazine style: small title and optional tiny metadata-like line.

The result must be materially different from a one-click filter. Every stylized decision should be traceable either to the source image or to the defined Collage-Lite Narrative mechanism. Preserve subject count, perspective, culturally meaningful details, and source-specific geometry. Do not invent facts, people, landmarks, brands, dates, signatures, or unreadable text. Stop the transformation before source identity is damaged.

## Style-specific negative prompt
No nine-grid, contact sheet, many photos, stickers, washi tape, postage stamps, random handwriting, scrapbook clutter, or unrelated found imagery.

## Variation knobs
- support fragments 1–3
- paper texture subtle
- hero area 65–85%
- overlap low/medium
- metadata line optional

## Hybrid behavior
Direct styles may enter `Controlled Hybrid` only if their pair appears in `data/compatibility.json`. The primary keeps subject identity, composition, lighting, palette, and realism. The secondary controls one declared subsystem only.

## Common failure modes
- Applying the same texture or effect uniformly to every pixel.
- Replacing source-specific structure with generic AI imagery.
- Oversizing typography until text becomes the subject.
- Inventing content to make a style stereotype more obvious.
- Ignoring material differences between surfaces.
- Turning batch consistency into forced visual sameness.

## Self-check
- Is the source still immediately recognizable?
- Can major stylized elements be traced to the source or this style's mechanism?
- Is the composition materially different from a simple filter?
- Is text small, legible, and outside identity-critical regions?
- Are there invented facts, extra subjects, malformed structures, or fake characters?
- Does the output read as `Collage-Lite Narrative` specifically rather than generic “AI art”?

## Acceptance criteria
Use `references/visual-benchmark.md`. A production image should normally score at least 17/20 across identity, composition, lighting, palette, material behavior, edges, typography, source specificity, style specificity, and anti-slop quality.
