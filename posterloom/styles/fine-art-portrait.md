---
id: fine-art-portrait
name: Fine Art Portrait
family: painterly-portrait
role: direct
status: gold
---

# Fine Art Portrait

## Style intent
Apply a painted surface while holding the likeness constant. The brushwork describes the existing face; it must never redefine it. Keep facial proportions, feature placement, expression, and age faithful to the source, and confine painterly energy to surface, edge, and light.

## Best for
- classic painted portrait treatment
- cultural and heritage portraits
- editorial illustration of a real person
- portraits where some painterly surface is desired

## Reject when
- the user needs an exact photographic likeness
- no human subject is present
- the subject is a group where individual faces must stay distinguishable

## Style DNA
**Subject / identity behavior**  
Apply a painted surface while holding the likeness constant. The brushwork describes the existing face; it must never redefine it. Keep facial proportions, feature placement, expression, and age faithful to the source, and confine painterly energy to surface, edge, and light.

**Composition strategy**  
Use time-honored portrait composition with a clear value structure and a calm background. Maintain the source head angle and eyeline. Avoid cropping through the top of the head or tight jaw framing unless the source already uses it.

**Lighting language**  
Build painterly light consistent with the source direction, using soft blended transitions and preserved shadow shape. Keep facial modeling readable rather than dramatic.

**Color logic**  
Limited, harmonious painterly palette derived from the source. Modulate skin with adjacent warm and cool tones rather than uniform flesh color. Keep saturation below poster-print intensity.

**Material / texture language**  
Visible but controlled brush direction in background, clothing, and secondary planes. The face stays comparatively smooth and resolved, with detail concentrated in eyes and mouth. Avoid heavy impasto on facial features.

**Typography system**  
Classic serif, small, low-contrast against the painted field. Sits in negative space and never overlaps the face.

**Realism level**  
high

**Transformation strength**  
medium-low

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
Transform the single source photograph using the **Fine Art Portrait** visual system. Apply a painted surface while holding the likeness constant.

Mechanism: The brushwork describes this exact face and must never redefine it. Preserve facial proportions, feature placement, expression, gaze, and apparent age. Confine painterly energy to surface, edge, and light.

Composition: Classic portrait composition with clear value structure and calm background. Keep the source head angle and eyeline. Avoid cropping the top of the head.

Lighting: Painterly light consistent with source direction, soft blended transitions, preserved shadow shape.

Color: Limited harmonious palette derived from the source. Modulate skin with adjacent warm and cool tones rather than uniform flesh color.

Material: Visible controlled brush direction in background and clothing. Face stays comparatively smooth and resolved, with detail concentrated in eyes and mouth. No heavy impasto on facial features.

Typography: Small classic serif in negative space, never overlapping the face.

## Style-specific negative prompt
No changed facial proportions, no rounder or narrower face, no exaggerated painterly features, no melted or smeared eyes, no asymmetric drift between eyes, no doll-like face, no heavy impasto on facial features, no caricature, no age shift, no beautification, no plastic skin, no costume change, no duplicate faces, no anachronistic costume, no text across the face.

## Variation knobs
- painterly energy background/light
- palette warm/cool/muted
- brush texture fine/visible
- type serif/classic/minimal
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
