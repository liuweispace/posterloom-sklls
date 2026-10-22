---
id: duotone-identity-stack
name: Duotone Identity Stack
family: graphic-portrait
role: direct
status: gold
---

# Duotone Identity Stack

## Style intent
Repeat ONE verified identity as a stack of the same person, then print the stack in a two-ink duotone with hard posterized edges. Exactly one copy is the canonical identity anchor and must match the source face precisely; every other copy is a graphic repetition of that same verified face, not a new person and not a merged average.

## Best for
- portrait and self-portrait series
- identity and self-examination themes
- experimental editorial covers
- fashion and culture features
- poster exercises built around one face

## Reject when
- no human subject is present
- the brief requires documentary facial credibility
- identity anchors cannot be established from the source
- the subject count must stay exactly as photographed with no graphic re-composition

## Style DNA
**Subject / identity behavior**  
Repeat ONE verified identity as a stack of the same person, then print the stack in a two-ink duotone with hard posterized edges. Exactly one copy is the canonical identity anchor and must match the source face precisely; every other copy is a graphic repetition of that same verified face, not a new person and not a merged average.

**Composition strategy**  
Build a vertical stack of 2-4 copies of the same face along the centerline, each copy cropped by the next so several eyes, noses and mouths coexist in one frame. Vary scale and angle slightly between copies (largest upper-left and tilted, smaller cascading toward center). Clip cheeks, temples and jaw into angular mask-like points rather than natural silhouettes. Anchor the stack with one strong foreground element (a hand entering from the lower edge, or a large circular disc overlapping the lower face). Leave one clean open quadrant for the title.

**Lighting language**  
Do not restage the photograph. Keep the source lighting on the canonical copy, then push the whole stack toward high-contrast print: blown highlights, crushed blacks, minimal midtone. Tone must read as ink on paper, not as studio lighting.

**Color logic**  
Strict two-ink duotone plus one accent. Map the photograph into a single hue ramp (e.g. crimson/raspberry into chalky white, or peach/coral into vermilion) with near-black reserved for the deepest shadow. Skin color is removed entirely. One saturated accent color carries the title and the registration marks.

**Material / texture language**  
Risograph or screen-print surface: visible ink grain, speckling, uneven ink coverage, slight misregistration, softened edges where ink does not take. Keep hair strands, pores and stubble legible inside the ink texture rather than smoothing them away.

**Typography system**  
Two type systems in tension. A large high-contrast display serif (Didone or Bodoni italic) for the title, set tight into one corner on the open quadrant. A heavy neo-grotesk (Helvetica Black class) alternative for an all-caps variant. Pair with small Song/Ming Chinese serif characters set far apart as corner markers, plus tiny uppercase microtype as edition marks (NNN / 100, date, series credit).

**Realism level**  
medium

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
Transform the single source photograph using the **Duotone Identity Stack** visual system.

Identity: There is exactly ONE real person in this poster, and it is the person in the source photograph. Duplicate that verified face several times, but every copy must be the SAME person with the SAME face shape, eye shape and spacing, eyebrow shape, nose and mouth shape, jawline, hairline, skin tone, apparent age, and gaze direction. Repetition is a graphic operation on a known identity, never the invention of a second person and never an averaged or merged face. Treat the largest, sharpest copy as the canonical anchor and match every other copy to it.

Composition: Stack 2-4 copies of that same face along the vertical centerline so several eyes, noses and mouths coexist in one frame. Crop each copy with the next. Vary scale and angle slightly: the largest copy sits upper-left and tilted, smaller copies cascade toward the center. Clip cheeks, temples and jaw into angular mask-like points. Anchor the lower half with one strong foreground element, either a hand entering from the bottom edge or a large circular disc overlapping the lower face. Keep one clean open quadrant for the title.

Color: Strict two-ink duotone plus one accent. Map the photograph into a single hue ramp with near-black reserved for deepest shadow. Remove natural skin color entirely. One saturated accent color carries the title and the small registration marks.

Material: Risograph or screen-print surface. Visible ink grain, speckling, uneven coverage, slight misregistration, softened edges where ink does not take. Keep hair strands, pores and stubble legible inside the ink texture.

Typography: A large high-contrast display serif (Didone or Bodoni italic) for the title set tight into one corner on the open quadrant, or a heavy neo-grotesk all-caps variant. Add small Song/Ming Chinese serif characters set far apart as corner markers, and tiny uppercase microtype as edition marks such as NNN / 100 plus date and series credit.

## Style-specific negative prompt
No new or different person, no face averaged between copies, no identity drift between repetitions, no extra faces belonging to other people, no smooth airbrushed skin, no glossy 3D render look, no full-colour natural skin tones, no soft pastel gradient background, no multiple unrelated source images, no contact sheet or moodboard grid, no illegible warped typography, no watermark, no stock-photo smile, no smooth vector illustration.

## Variation knobs
- copy-count 2/3/4
- hue-ramp crimson/white, peach/vermilion, cyan/black, ochre/black
- stack-angle aligned/offset/diagonal
- anchor-element hand/disc/none
- type high-contrast-serif/neogrotesk-caps
- edition-mark none/counter/date
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
