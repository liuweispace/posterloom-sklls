
# Typography

PosterLoom typography is intentionally restrained.

## Color as values, not adjectives

Word-level color language is what the model has to interpret; hex values are what it
can execute. `data/substrates.json` is the named substrate and ink library:

- **Substrates**: neutral white `#FAFAF7`, cool gray `#E9E9E5`, pale beige `#F5F1E8`,
  ink black `#101010` — each with the subjects it supports.
- **Inks**: 19 named values from crimson `#C83232` to mint `#5EB783`.
- **Two-ink recipes**: 10 tested pairings, e.g. cobalt `#2148B8` + terracotta `#C65F38`.
- **Coverage**: dominant plate 70-85%, accent plate 15-30%. The accent must have a job
  (dates, annotations, one object, overprint intersections).

When a style declares a `color_system`, compile it into the prompt as explicit values.
Do not paraphrase a named ink into "warm" or "muted".

## Default
- Title: 1–4 words.
- Subtitle: optional; at most one short line.
- Text normally occupies **5–10% or less** of the visual area.
- Never cover faces, key hands, architectural crowns, important signs, or defining object contours.

## Language and facts
- Do not invent place names, dates, brands, catalog numbers, historical claims, or signatures.
- Do not invent Chinese or other non-Latin characters.
- Use verified source text or user-provided wording.
- If factual text is unavailable, prefer a mood-based title.

## Placement
Prefer:
- quiet sky;
- dark wall;
- water void;
- paper margin;
- low-detail shadow;
- simple color field.

## Fallback for weak text rendering
If the image generator renders text poorly, generate the artwork without critical text and apply typography in a second deterministic design pass when tooling allows it.
