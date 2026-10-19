---
id: photojournalistic
name: Photojournalistic
family: documentary-portrait
role: direct
status: gold
---

# Photojournalistic

## Style intent
Maximum fidelity to the source moment. Preserve the face exactly as captured, including asymmetry, expression, skin texture, clothing, and the surrounding context. This is the lowest-transformation option available for people.

## Best for
- candid and reportage portraits
- environmental human stories
- street photography posters
- maximum likeness fidelity

## Reject when
- the user wants a designed or art-directed look
- the source is already heavily manipulated
- no human subject is present

## Style DNA
**Subject / identity behavior**  
Maximum fidelity to the source moment. Preserve the face exactly as captured, including asymmetry, expression, skin texture, clothing, and the surrounding context. This is the lowest-transformation option available for people.

**Composition strategy**  
Preserve the source framing and spatial context. Reframe only enough to improve poster proportion. Keep the subject's relationship to their environment legible.

**Lighting language**  
Use available or practical light as captured. Allow realistic imperfection such as mixed color temperature. Do not relight into studio conditions.

**Color logic**  
Honest source color with restrained editorial grading. Preserve environmental color cast and skin-under-light relationships.

**Material / texture language**  
Keep real-world texture: skin pores, hair irregularity, fabric wear, and authentic imperfection. Documentary credibility outranks polish.

**Typography system**  
Minimal. Small sans or serif caption, or none. Never place text over the subject's face.

**Realism level**  
very-high

**Transformation strength**  
low

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
Transform the single source photograph using the **Photojournalistic** visual system. Maximum fidelity to the source moment.

Mechanism: Preserve the face exactly as captured, including natural asymmetry, expression, skin texture, clothing, and surrounding context. This is the lowest-transformation option for people.

Composition: Preserve source framing and spatial context. Reframe only enough to improve poster proportion. Keep the subject's relationship to their environment legible.

Lighting: Available or practical light as captured. Allow realistic imperfection such as mixed color temperature. Do not relight into studio conditions.

Color: Honest source color with restrained editorial grading. Preserve environmental color cast.

Material: Real-world texture - skin pores, hair irregularity, fabric wear, authentic imperfection. Documentary credibility outranks polish.

Typography: Minimal. Small sans or serif caption, or none. Never over the face.

## Style-specific negative prompt
No changed facial features, no beautification, no skin smoothing, no studio relighting, no styled or staged look, no costume change, no age shift, no gender shift, no extra or missing fingers, no duplicate or composite faces, no text across the face, no HDR, no fake bokeh balls, no generic stock-photo aesthetic.

## Variation knobs
- crop conservative/as-is
- grading neutral/editorial
- grain fine/none
- type sans/serif/none
- caption none/tiny
- likeness fidelity exact/strict

## Hybrid behavior
Direct styles may enter `Controlled Hybrid` only if their pair appears in `data/compatibility.json`. The primary keeps subject identity, composition, lighting, palette, and realism. The secondary controls one declared subsystem only.

## Common failure modes
- Generating a new or generic face when the source person must stay recognizable.
- Averaging the face toward a model-default or idealized look.
- Letting the style's medium reinterpret facial structure.
- Smoothing, reshaping, or beautifying the face.
- Losing source-specific anchors: eye shape, brow shape, hairline, skin tone, age cues.
- Placing typography or graphic elements across the face.
- Applying the same texture or effect uniformly to every pixel.
- Replacing source-specific structure with generic AI imagery.
- Oversizing typography until text becomes the subject.
- Inventing content to make a style stereotype more obvious.
- Ignoring material differences between surfaces.
- Turning batch consistency into forced visual sameness.

## Self-check
- Is this the same person as in the source, not a similar-looking invented person?
- Do face shape, eye shape/spacing, eyebrow shape, nose shape, mouth shape, hairline, and skin tone all match?
- Is the expression and gaze direction preserved?
- Are there no added beautifications, age shifts, or makeup?
- Is the face fully inside the frame with margin, and free of graphic overlays?
- Is the source still immediately recognizable?
- Can major stylized elements be traced to the source or this style's mechanism?
- Is the composition materially different from a simple filter?
- Is text small, legible, and outside identity-critical regions?
- Are there invented facts, extra subjects, malformed structures, or fake characters?
- Does the output read as this style specifically rather than generic “AI art”?

## Acceptance criteria
Use `references/visual-benchmark.md`. A production image should normally score at least 17/20 across identity, composition, lighting, palette, material behavior, edges, typography, source specificity, style specificity, and anti-slop quality.
