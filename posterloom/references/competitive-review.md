# Competitive review — how PosterLoom compares

Reviewed 2026-10-23 against the public agent-skill ecosystem for photo→poster work.

## What PosterLoom already does better than most

- **Routing is a real engine**, not a prompt library. 35 direct styles + 1 meta style,
  scored from scene tags, with an identity guardrail that protects faces.
- **Facial identity locking** is the strongest differentiator. No competitor in the
  surveyed set has anything equivalent.
- **Face-aware style unlock.** `duotone-identity-stack` is the only style that repeats a
  face, and it is the only style allowed to. Every other portrait style keeps the
  "never duplicate faces" rule.
- **Deterministic CLI** with machine-readable output, so another agent can integrate it
  without interpreting prose.
- **Self-verifying**: 36 style contracts, 35 routing regression cases, a repo validator.

## What the zine skills taught us (v1.6.0)

`gathered-scenes-zine-skill` (Zeejay0) is the strongest skill found in the survey, and
its two sibling skills were folded into the library as two direct styles rather than
paraphrased into advice. Four things were worth taking:

1. **The photo can be semantic evidence, not a visual layer.** The distillation skill
   treats the source as a reference for meaning and outputs illustration only. PosterLoom
   previously assumed every style transforms visible photo pixels. That assumption was
   baked into the global prompt block. It is now a per-style `source_role`, so the global
   block can tell the model "keep the photo" or "do not reproduce the photo" correctly.
2. **The abstraction engine, not the aesthetic.** The valuable part is the method:
   retain 1-2 forms, merge repetitions, omit clutter, transform, expose blank paper —
   and separate *field extent* from *printed density*. A large quiet field is not a timid
   illustration. That discipline is now a contract requirement, not a mood word.
3. **Named color with structural job.** The chroma engine's tests ("does removing this
   hue weaken the composition?") are a better rule than "add a pop of color". This
   reinforced the existing hex-value approach and added the structural-removal test to
   the new styles' contracts.
4. **Edge treatment as a semantic object.** The torn-fiber handoff is described as a
   physical paper object with a band width and an affected perimeter, not as a filter.
   That is the difference between "torn paper edge" as an instruction and as a spec.

What was deliberately **not** taken: the output-format block that appends the author's
website and a sharing-credit line. Those are the original author's promotion rules, not
part of the method.

## Competitors surveyed

| Skill | Stars | What it does | What PosterLoom learns from it |
|---|---|---|---|
| `mono-color-skill` (yanliudesign) | 3.4k | One-ink / two-ink editorial print. Named hex inks, named substrates, ink-coverage ratios. | **Named palettes.** `mono-color` ships concrete hex values per ink recipe and substrate. PosterLoom describes color in words only. This is the single clearest gap. |
| `scenes-gathered-zine-v1-3` (Zeejay0) | trending | Photo anchored inside an abstract illustration field, one high-chroma structural hue, hand-torn paper edge. | **Read the photo before styling it.** It builds an internal "Scene Card" (core subjects, spatial invariants, dominant gesture, visual-weight map, native color atmosphere, source-shape candidates, natural quiet areas, semantic minimum) before choosing a path. PosterLoom documents a scene profile but has no tool that actually inspects a photo. |
| `poster-style-transfer` (jiemianduan) | — | Extracts a poster's design *grammar* and transfers it to new content. | **Style-spec schema.** It separates analysis from generation and has a reusable spec schema plus a fidelity rubric. PosterLoom's style contracts are close, but it has no "extract grammar from a reference" mode. |
| `poster-design` / `ai-poster-flyer-designer` | — | HTML/CSS/SVG output with explicit layout archetypes and 4-level typographic hierarchy. | **Explicit layout archetypes.** PosterLoom's style contracts describe composition in prose; an explicit named-archetype vocabulary would be more actionable. |
| `baoyu-image-gen` (JimLiu) | arena #1 | Best overall general-purpose image skill in the blind arena (8.67/10). | **Text legibility is the biggest score differentiator.** The arena found skills that quote exact copy and plan placement render legible type; weak prompts produce garbled text. PosterLoom deliberately keeps type at 5–10% and rarely specifies exact copy. |
| `gpt-image-2` (ConardLi) | arena #2 | 80+ templates across 18 categories. | **Template library.** A fast-start template wins when the brief matches a template. |
| `visual-skills` (smixs) | arena #4 | Art-directed output; won the poster brief. | **Art direction over defaults.** Confirms PosterLoom's artistic dial was the right call. |
| `ai-image-generation` (inference.sh) | arena #5 | Leanest skill (~7K context tokens), still ranked #6. | **Lean wins too.** PosterLoom at 904K / 79 files is heavy; the skill should stay deterministic CLI-first, not prose-heavy. |

## Key findings

> Status note: findings 1–3 were gaps when this review was first written. All three are
> now closed (v1.4–v1.6). Findings 4 and 5 are still open.

### 1. Photo-reading step — CLOSED in v1.4

Was: `references/scene-analysis.md` specified *what fields a scene profile must contain*,
and the profile was filled in by the agent manually. Every downstream decision depended
on the agent's own reading of the photo, which varied run to run.

Now: `scripts/scene_analyze.py` measures the image from pixels — dimensions, aspect,
palette families, luminance, contrast, saturation, edge density, salient and quiet
regions, text-safe candidates, and a structural fingerprint. `posterloom.py analyze`
emits a profile; `posterloom.py make` runs it automatically.

The important constraint: the analyzer reports only what pixels can support. Subject
type, identity anchors, mood and transformation tolerance are semantic and go to
`_needs_vision` rather than being guessed, because a wrong guess poisons routing.

The "Scene Card" idea from `scenes-gathered-zine` is now part of the style contract
for the two zine styles, not a schema change to the whole profile — the flat profile
shape stayed, because it is what the router consumes.

### 2. Colors described, not specified — CLOSED in v1.4

Was: contracts said "source-derived duotone, one saturated accent".

Now: `data/substrates.json` ships named substrates and inks with hex values
(Neutral White `#FAFAF7`, Cool Gray `#E9E9E5`, Pale Beige `#F5F1E8`, Aged Cream
`#F2EBDC`, plus 26 named inks) and ink-coverage ratios. Styles that declare a
`color_system` get a literal `COLOR SYSTEM` block in the compiled prompt, hex included.

### 3. No reference-poster transfer mode — CLOSED in v1.5

Was: PosterLoom could route to its own styles but could not extract a system from an
image the user points at.

Now: `scripts/match_reference.py` matches a reference poster to the closest built-in
style by measurable properties — contrast, saturation, palette family, detail density,
and hue-cluster count. The last one is the decisive signal: a flat two-colour print has
one to three hue families, a photograph has many. Narrow-family and specificity
weighting stop generic styles from tying with the exact match.

### 4. Typography intent is under-specified — STILL OPEN

The arena result is unambiguous: text legibility separated the top skills from the rest.
PosterLoom's global typography rule ("5–10% of visual area, restrained, short title only")
is good for editorial posters but does nothing for a poster where the title *is* the
design.

### 5. Size is a liability

`ai-image-generation` ranked #6 at ~7K context tokens. PosterLoom's value is in the CLI,
not the prose — SKILL.md stays under 200 lines, which is healthy. The weight is in
`styles/` (36 contracts) and `data/styles.json`, both of which are loaded on demand, so
this is mostly fine. Keep it that way: never inline the style library into SKILL.md.

## What NOT to copy

- `mono-color-skill` and friends are **one-style** skills — narrow, deep, single-purpose.
  PosterLoom's value is breadth plus a router. Do not collapse into one style.
- Several surveyed skills hardcode a specific image model or API. PosterLoom is
  model-agnostic on purpose and must stay that way.
- `scenes-gathered-zine` ends with a "sharing-credit line" for the first one or two
  generations. PosterLoom is a published skill with its own attribution; it does not
  need per-generation credit lines.
