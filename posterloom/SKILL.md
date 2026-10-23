---
name: posterloom
description: Turn a real photograph into an art-directed poster - analyze the scene, preserve identity anchors, route to 1 of 33 poster styles, and compile a locked generation prompt. Use when the user wants a photo converted into an editorial, travel, cultural, painterly, print, portrait, or modern-design poster, or wants a batch of independent posters from many photos. Enforces facial likeness locking on any source containing a person.
license: MIT
metadata:
  version: "1.4.0"
  tagline: "Adaptive Photo-to-Poster Skill"
---

# PosterLoom

Turn a real source photograph into an art-directed poster: scene analysis, adaptive style
routing, source-aware prompt composition, restrained typography, and explicit visual QA.

## Use when

- A user wants a photo turned into a finished poster rather than a simple filter.
- A source image should be matched automatically to an appropriate visual direction.
- A batch of photos should become independent poster artworks.
- The task must preserve a real person's likeness.
- The user wants small, refined typography instead of oversized headline treatment.

## Don't use when

- The user only wants exposure, crop, denoise, or color correction with no poster transformation.
- The request is explicitly a collage or moodboard - follow that request instead.
- No source image exists and the request is pure text-to-image.
- The host cannot inspect images and the user expects automatic scene-aware routing.

## Quick start

Everything runs through one dependency-free CLI (Python 3.9+ standard library only):

```bash
python3 scripts/posterloom.py analyze photo.jpg --out profile.json   # 从图片测量场景
python3 scripts/posterloom.py route   examples/scene-portrait.json      # rank styles
python3 scripts/posterloom.py prompt  examples/scene-portrait.json      # compile prompt
python3 scripts/posterloom.py batch   examples/batch-profiles.json      # plan a batch
python3 scripts/posterloom.py styles --portrait                        # list styles
python3 scripts/posterloom.py show    editorial-portrait                # style contract
python3 scripts/posterloom.py validate examples/scene-portrait.json     # schema check
python3 scripts/posterloom.py selftest                                 # integrity checks
```

Add `--json` to `route`, `prompt`, `batch`, and `styles` for machine-readable output.
Every subcommand exits non-zero and prints `ERROR: ...` on failure.

## Workflow

1. **Analyze the source.** Build the scene profile described in
   [references/scene-analysis.md](references/scene-analysis.md). Record `subject.identity_anchors`
   - the smallest set of details that make this exact source recognizable. For a person, this is
   mandatory and must include facial specifics.
2. **Validate.** `posterloom.py validate <profile>` catches malformed profiles before routing.
3. **Route the style.** Run `posterloom.py route`. Read [references/style-router.md](references/style-router.md)
   to interpret the ranking, confidence, and any override.
4. **Load the chosen contract.** Read `styles/<style-id>.md`. Never bulk-load all 33.
5. **Compile the prompt.** Run `posterloom.py prompt <profile>`. Facial-identity constraints are
   injected automatically whenever the source contains a recognizable face.
6. **Generate** with the host's image-generation or image-editing tool.
7. **Verify.** Apply `evals/rubric.md`. For a person, the likeness check is mandatory - see
   [references/identity-preservation.md](references/identity-preservation.md).

## Non-negotiable rules

**One source, one poster.** Never produce a collage, contact sheet, moodboard, scrapbook, album,
or multi-panel composite from unrelated sources.

**Source truth beats style.** Never invent a person, place name, date, brand, landmark, signature,
or historical claim from appearance alone. If factual text is not supplied or legible, omit it.

**Facial likeness is enforced, not requested.** Any source containing a recognizable human face
gets an identity lock injected into its prompt, independent of the routed style:

- A face-designed style (`editorial-portrait`, `photojournalistic`, `fine-art-portrait`) is
  preferred over general-purpose styles.
- Face-repainting media (watercolor, gouache, ink wash, screenprint, riso, lithograph,
  paper-cut, relief print, pastel, neo-ink) are refused unless the user explicitly requests
  heavy transformation.
- The lock binds face shape, eye shape and spacing, eyebrow shape, nose and mouth shape, jawline,
  hairline, skin tone, apparent age, expression, and gaze as fixed geometry.

**Prompting is necessary but not sufficient.** Text constraints reduce drift; they cannot
eliminate it. Before delivering a portrait, compare the generated face against the source on the
seven identity-critical points (face shape, eye shape/spacing, eyebrow shape, nose shape, mouth
shape, hairline, skin tone). If any differ, regenerate. When the backend supports reference-image
conditioning (IP-Adapter, FaceID, InstantID), prefer it - it is the only reliable mechanism.

**Typography stays subordinate.** Text normally occupies 5-10% or less of the visual area, and
never covers a face, key hand gesture, important sign, architectural crown, or defining contour.

## Style library

32 direct styles plus `controlled-hybrid` (a meta-style that never enters direct ranking).

| Family | Count |
|---|---|
| photographic-editorial | 5 |
| painterly-atmosphere | 5 |
| graphic-print | 5 |
| eastern-heritage | 5 |
| modern-design | 5 |
| conceptual-hybrid | 4 |
| portrait (photographic / painterly / documentary) | 3 |

Routing is deterministic and never randomizes. Confidence is measured relative to the best score
achievable for that specific profile, and a conservative override fires only when a genuinely weak
signal is matched closely by an editorial style.

## Project layout

```
posterloom/
  SKILL.md                     this manifest
  scripts/posterloom.py        CLI entrypoint (route/prompt/batch/styles/show/validate/selftest)
  scripts/rank_styles.py       scoring + routing + portrait guardrail
  scripts/face_identity.py     facial likeness lock
  scripts/compose_prompt.py    prompt assembly
  scripts/batch_plan.py        batch planning with repetition damping
  scripts/gen_style_contracts.py  regenerate contracts from styles.json
  scripts/add_portrait_styles.py  one-off portrait style installer
  data/styles.json             style library (single source of truth)
  data/routing-rules.json      weights, thresholds, safety lists
  data/compatibility.json      permitted hybrid pairs
  styles/<style-id>.md         one contract per style
  references/                  method notes
  schemas/                     JSON Schema for profiles and routes
  examples/                    runnable profiles
  evals/                       routing regression + visual rubric
```

## Batch behaviour

Route every source independently. A soft penalty damps a style once it exceeds 3 uses in one
batch, so near-identical scenes spread out - but it never overrides a clear fit. Report
`style_repetition` and `unique_styles` from `batch` output.

## References

- [Scene analysis](references/scene-analysis.md) - required profile fields and identity anchors
- [Style router](references/style-router.md) - ranking, confidence, portrait guard, hybrid rules
- [Identity preservation](references/identity-preservation.md) - likeness enforcement and QA
- [Prompt composer](references/prompt-composer.md) - how prompts are assembled
- [Composition](references/composition.md) and [typography](references/typography.md)
- [Anti-slop](references/anti-slop.md) - failure modes to actively avoid
- [Visual benchmark rubric](evals/rubric.md) - 0-2 scoring across 10 axes, 17/20 to pass
