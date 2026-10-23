# Competitive review — how PosterLoom compares

Reviewed 2026-10-23 against the public agent-skill ecosystem for photo→poster work.

## What PosterLoom already does better than most

- **Routing is a real engine**, not a prompt library. 33 direct styles + 1 meta style,
  scored from scene tags, with an identity guardrail that protects faces.
- **Facial identity locking** is the strongest differentiator. No competitor in the
  surveyed set has anything equivalent.
- **Face-aware style unlock.** `duotone-identity-stack` is the only style that repeats a
  face, and it is the only style allowed to. Every other portrait style keeps the
  "never duplicate faces" rule.
- **Deterministic CLI** with machine-readable output, so another agent can integrate it
  without interpreting prose.
- **Self-verifying**: 34 style contracts, 33 routing regression cases, a repo validator.

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

### 1. PosterLoom has no photo-reading step (biggest gap)

`references/scene-analysis.md` specifies *what fields a scene profile must contain*, and
the profile is filled in by the agent manually. There is no tool that looks at an image
and produces that profile. Every downstream decision — routing, identity anchors, text
safe zones — therefore depends on the agent's own reading of the photo, which is exactly
where it varies run to run.

`scenes-gathered-zine` solves this by making the reading step explicit and structured.
Its "Scene Card" fields are a better schema than PosterLoom's current flat profile.

### 2. Colors are described, not specified

PosterLoom style contracts say things like "source-derived duotone, one saturated
accent". `mono-color-skill` ships named inks with hex values, named substrates
(Neutral White `#FAFAF7`, Cool Gray `#E9E9E5`, Pale Beige `#F5F1E8`), and ink-coverage
ratios (dominant plate 70–85%, accent plate 15–30%).

Word-level color language is what the model has to interpret. Hex values are what it
can execute.

### 3. No reference-poster transfer mode

`poster-style-transfer` treats a poster as a reusable *grammar*, not content. PosterLoom
can route to its own 33 styles but cannot extract a system from an image the user
points at.

### 4. Typography intent is under-specified

The arena result is unambiguous: text legibility separated the top skills from the rest.
PosterLoom's global typography rule ("5–10% of visual area, restrained, short title only")
is good for editorial posters but does nothing for a poster where the title *is* the
design.

### 5. Size is a liability

904K / 79 files. `ai-image-generation` ranked #6 at ~7K context tokens. PosterLoom's
value is in the CLI, not the prose — the SKILL.md is only 145 lines, which is healthy.
The weight is in `styles/` (34 contracts) and `data/styles.json` (132KB), both of which
are loaded on demand, so this is mostly fine. Keep it that way: never inline the style
library into SKILL.md.

## What NOT to copy

- `mono-color-skill` and friends are **one-style** skills — narrow, deep, single-purpose.
  PosterLoom's value is breadth plus a router. Do not collapse into one style.
- Several surveyed skills hardcode a specific image model or API. PosterLoom is
  model-agnostic on purpose and must stay that way.
- `scenes-gathered-zine` ends with a "sharing-credit line" for the first one or two
  generations. PosterLoom is a published skill with its own attribution; it does not
  need per-generation credit lines.
