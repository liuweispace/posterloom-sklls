---
id: paper-cut-graphic
name: Paper-Cut Graphic
family: graphic-print
role: direct
status: gold
---

# Paper-Cut Graphic

## Style intent
Preserve the subject silhouette, proportions, and only the internal cutouts required for recognition.

## Best for
- architecture
- landscape
- trees
- streets
- temples
- objects
- strong spatial layering

## Reject when
- fine face close-up is the priority
- transparent material realism is critical
- documentary density must remain intact

## Style DNA
**Subject / identity behavior**  
Preserve the subject silhouette, proportions, and only the internal cutouts required for recognition.

**Composition strategy**  
Break the scene into a controlled stack of foreground, hero, midground, background, sky/water, and shadow paper planes derived from the source.

**Lighting language**  
Use shallow physical cast shadows between layers instead of glossy 3D lighting.

**Color logic**  
Use roughly 5–9 source-derived matte paper colors.

**Material / texture language**  
Fibrous matte paper, crisp hand-cut edges, subtle thickness, and shallow cast shadows.

**Typography system**  
Small clean typography printed on a flat paper field; avoid novelty craft fonts.

**Realism level**  
low

**Transformation strength**  
high

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
Transform the single source photograph using the **Paper-Cut Graphic** visual system. Treat the photograph as the factual anchor and preserve all identity anchors before stylization.

Mechanism: Preserve the subject silhouette, proportions, and only the internal cutouts required for recognition.

Composition: Break the scene into a controlled stack of foreground, hero, midground, background, sky/water, and shadow paper planes derived from the source.

Lighting: Use shallow physical cast shadows between layers instead of glossy 3D lighting.

Color: Use roughly 5–9 source-derived matte paper colors.

Material and texture: Fibrous matte paper, crisp hand-cut edges, subtle thickness, and shallow cast shadows.

Typography: Small clean typography printed on a flat paper field; avoid novelty craft fonts.

The result must be materially different from a one-click filter. Every stylized decision should be traceable either to the source image or to the defined Paper-Cut Graphic mechanism. Preserve subject count, perspective, culturally meaningful details, and source-specific geometry. Do not invent facts, people, landmarks, brands, dates, signatures, or unreadable text. Stop the transformation before source identity is damaged.

## Style-specific negative prompt
No scrapbook stickers, greeting-card craft, deep 3D extrusion, glossy plastic layers, random floral cutouts, excessive drop shadows, or loss of original silhouette.

## Variation knobs
- layers 5–9
- shadow depth shallow
- edge crisp/slightly handmade
- palette matte
- internal cutouts selective

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
- Does the output read as `Paper-Cut Graphic` specifically rather than generic “AI art”?

## Acceptance criteria
Use `references/visual-benchmark.md`. A production image should normally score at least 17/20 across identity, composition, lighting, palette, material behavior, edges, typography, source specificity, style specificity, and anti-slop quality.
