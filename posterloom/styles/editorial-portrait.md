---
id: editorial-portrait
name: Editorial Portrait
family: photographic-portrait
role: direct
status: gold
---

# Editorial Portrait

## Style intent
Render the existing face, not a new one. Treat facial geometry as fixed input: preserve face shape, bone structure, eye shape and spacing, eyebrow shape, nose and mouth shape, jawline, hairline, skin tone and texture, apparent age, expression, and gaze direction. Change only framing, lighting refinement, background treatment, and typography.

## Best for
- portrait and headshot
- magazine and interview features
- human-interest stories
- founder and team portraits

## Reject when
- no human subject is present
- the user explicitly wants a painterly reinterpretation
- identity anchors cannot be established from the source

## Style DNA
**Subject / identity behavior**  
Render the existing face, not a new one. Treat facial geometry as fixed input: preserve face shape, bone structure, eye shape and spacing, eyebrow shape, nose and mouth shape, jawline, hairline, skin tone and texture, apparent age, expression, and gaze direction. Change only framing, lighting refinement, background treatment, and typography.

**Composition strategy**  
Use editorial portrait framing with a clean headroom relationship and generous negative space. Separate the subject from the background through depth, tone, or restrained environmental context. Keep the face unobstructed and free of overlaid graphic elements.

**Lighting language**  
Preserve the source light direction. Refine into soft directional key with gentle falloff and clean shadow separation. Do not add rim lights, catchlights, or dramatic contrast that the source does not motivate.

**Color logic**  
Source-derived skin rendering with believable subsurface tone. Keep highlights soft on skin, avoid orange oversaturation, and preserve natural lip, hair, and fabric color relationships.

**Material / texture language**  
Render skin with visible but restrained texture: pores, fine lines, natural variation. Hair keeps strand direction and density. Fabric keeps weave and weight. Avoid plastic smoothing, beauty filters, and airbrushed skin.

**Typography system**  
Small editorial serif or grotesk, usually 3-6% of poster height, placed in a text-safe zone that never crosses the face or hands.

**Realism level**  
high

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
Transform the single source photograph using the **Editorial Portrait** visual system. The photograph is the factual anchor and the face is FIXED GEOMETRY, not content to reinterpret.

Mechanism: Reproduce this exact person's face. Preserve face shape, bone structure, eye shape and spacing, eyebrow shape, nose and mouth shape, jawline, hairline, skin tone and texture, apparent age, expression, and gaze direction. Do not beautify, de-age, age-shift, or gender-shift.

Composition: Editorial portrait framing with clean headroom and generous negative space. Keep the face unobstructed and free of graphic overlays.

Lighting: Preserve the source light direction. Refine into soft directional key with gentle falloff. No unmotivated rim lights or catchlights.

Color: Source-derived skin rendering, believable subsurface tone, soft highlights on skin, natural lip and hair color.

Material: Skin texture with restrained visible pores and fine lines. Hair keeps strand direction and density. Fabric keeps weave and weight. No plastic smoothing or beauty filter.

Typography: Small editorial serif or grotesk in a text-safe zone that never crosses the face or hands.

## Style-specific negative prompt
No changed facial features, no altered face shape or jawline, no eye-shape or eyebrow drift, no age shift, no gender shift, no beautification or plastic skin, no airbrushing, no heavy makeup addition, no changed hairline or hairstyle, no costume change, no extra or missing fingers, no duplicate or composite faces, no glamor retouch, no fantasy lighting, no dramatic rim light, no oversaturated HDR skin, no text across the face.

## Variation knobs
- crop tight-bust/half-body
- background simplification subtle/moderate
- grain fine/none
- type serif/grotesk/minimal
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
