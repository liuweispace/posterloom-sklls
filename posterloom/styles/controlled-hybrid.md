---
id: controlled-hybrid
name: Controlled Hybrid
family: meta-style
role: meta
status: gold
---

# Controlled Hybrid

## Style intent
Use exactly two compatible visual languages. The primary owns subject identity, composition, lighting, palette, realism, and spatial logic. The secondary controls one declared subsystem only.

## Best for
- two clear compatible directions
- router near-tie
- subtle requested hybrid

## Reject when
- incompatible pair
- three or more styles
- uncertain primary
- documentary truth risk

## Style DNA
**Subject / identity behavior**  
Use exactly two compatible visual languages. The primary owns subject identity, composition, lighting, palette, realism, and spatial logic. The secondary controls one declared subsystem only.

**Composition strategy**  
Primary style controls the whole composition; the secondary may refine one subsystem but may not create a competing composition.

**Lighting language**  
Primary style owns lighting unless the one declared secondary subsystem is atmosphere, and even then only subtly.

**Color logic**  
Primary palette remains the common color system.

**Material / texture language**  
Primary material behavior remains dominant; secondary texture stays localized.

**Typography system**  
Primary typography remains active unless typography is the declared secondary subsystem.

**Realism level**  
inherited

**Transformation strength**  
inherited

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
Create a controlled hybrid poster using exactly two compatible PosterLoom styles. The PRIMARY style controls approximately 80% of the image and owns subject treatment, composition, lighting, palette, realism, and spatial logic. The SECONDARY style contributes approximately 20% and is restricted to one declared subsystem such as typography, negative-space behavior, print texture, ink edge treatment, grid alignment, color separation, or atmosphere. Do not blend the two styles uniformly across the whole image. Preserve all identity anchors and keep the source photograph as the factual basis. The result must read immediately as the primary style with one purposeful secondary influence. Never introduce a third style.

## Style-specific negative prompt
No 50/50 mix, no three-style blend, no effect stacking, no random collage, no conflicting light systems, no palette clash, and no subject redesign.

## Variation knobs
- primary share 75–85%
- secondary share 15–25%
- secondary controls exactly one subsystem
- pair must exist in compatibility.json

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
- Does the output read as `Controlled Hybrid` specifically rather than generic “AI art”?

## Acceptance criteria
Use `references/visual-benchmark.md`. A production image should normally score at least 17/20 across identity, composition, lighting, palette, material behavior, edges, typography, source specificity, style specificity, and anti-slop quality.
