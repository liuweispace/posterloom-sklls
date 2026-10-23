---
name: posterloom
description: Turn a real photograph into an art-directed poster - measure the scene, route to 1 of 33 poster styles, and compile a locked generation prompt. Use when the user wants a photo converted into an editorial, travel, cultural, painterly, print, portrait, or modern-design poster, wants a reference poster matched to a style, or wants a batch of independent posters from many photos. Enforces facial likeness locking on any source containing a person.
license: MIT
metadata:
  version: "1.5.0"
  tagline: "Adaptive Photo-to-Poster Skill"
---

# PosterLoom

Turn a photograph into an art-directed poster. One command does the work.

## The one command

```bash
python3 scripts/posterloom.py make photo.jpg
```

That measures the image, picks a style, and prints the finished generation prompt.
It tells you what it measured, which style it chose, and what it could not decide.

Add context only where you have it:

```bash
# a person - the identity lock turns on automatically
python3 scripts/posterloom.py make photo.jpg --type portrait \
  --summary "Young man, black hair, hard side light" \
  --anchors "face shape,eye shape,hairline,skin tone" \
  --mood "quiet,intimate"

# "make it artistic" - unlocks art-directed styles, keeps likeness protection
python3 scripts/posterloom.py make photo.jpg --type portrait --tolerance high --tags artistic

# match a reference poster you like
python3 scripts/posterloom.py make photo.jpg --reference ref-poster.jpg

# override the style yourself
python3 scripts/posterloom.py make photo.jpg --style duotone-identity-stack

# machine-readable
python3 scripts/posterloom.py make photo.jpg --json
```

Then generate with the host's image tool and send it the printed prompt.

## What `make` will not do

It will not guess `subject.type`, identity anchors, or mood — those need eyes. It lists
what is missing under `TODO` and tells you which flag fills it. Inventing subject data
would poison the style routing, which is the one thing this skill exists to get right.

`realism_value` defaults to `high`; you only override it if you want something else.

## Everything else

```bash
python3 scripts/posterloom.py analyze photo.jpg --out profile.json  # measure only
python3 scripts/posterloom.py match   ref-poster.jpg                # match only
python3 scripts/posterloom.py route   profile.json                  # rank styles
python3 scripts/posterloom.py prompt  profile.json                  # compile prompt
python3 scripts/posterloom.py batch   batch-profiles.json           # plan a batch
python3 scripts/posterloom.py styles --portrait                     # list styles
python3 scripts/posterloom.py show    editorial-portrait             # one contract
python3 scripts/posterloom.py validate profile.json                 # schema check
python3 scripts/posterloom.py selftest                              # integrity checks
```

Add `--json` to `route`, `prompt`, `batch`, `styles`, `make`, and `match`.
Every subcommand exits non-zero and prints `ERROR: ...` on failure.
Zero dependencies — Python 3.9+ standard library only. PNG works without Pillow; JPEG needs it.

## Use when

- A user wants a photo turned into a finished poster rather than a simple filter.
- A source should be matched automatically to a visual direction.
- A user supplies a reference poster and wants that look applied to a new photo.
- A batch of photos should become independent poster artworks.
- A real person's likeness must survive the transformation.

## Don't use when

- The user only wants exposure, crop, denoise, or color correction.
- The request is explicitly a collage or moodboard — follow that instead.
- No source image exists and the request is pure text-to-image.

## Non-negotiable rules

**One source, one poster.** Never a collage, contact sheet, moodboard, or multi-panel
composite from unrelated sources.

**Source truth beats style.** Never invent a person, place name, date, brand, landmark,
signature, or historical claim from appearance alone. If factual text is not supplied or
legible, omit it.

**Facial likeness is enforced, not requested.** Any source with a recognizable face gets
an identity lock injected into its prompt, independent of the routed style:

- Face-designed styles are preferred over general-purpose ones.
- Face-repainting media (watercolor, gouache, ink wash, screenprint, riso, lithograph,
  paper-cut, relief print, pastel, neo-ink) are refused unless the user explicitly asks
  for heavy transformation.
- The lock binds face shape, eye shape and spacing, eyebrow shape, nose and mouth shape,
  jawline, hairline, skin tone, apparent age, expression, and gaze as fixed geometry.
- `duotone-identity-stack` is the one exception: it repeats the face on purpose, so its
  clause reads "repeat one identity" instead of "never duplicate faces". Every copy must
  still be the same verified person.

**Prompting is necessary but not sufficient.** Text constraints reduce drift; they cannot
eliminate it. Before delivering a portrait, compare the generated face against the source on
the seven identity-critical points. If any differ, regenerate. When the backend supports
reference-image conditioning (IP-Adapter, FaceID, InstantID), prefer it — it is the only
reliable mechanism.

**Typography stays subordinate.** Text normally occupies 5-10% or less of the visual area,
and never covers a face, key hand gesture, important sign, architectural crown, or defining
contour.

## Style library

33 direct styles plus `controlled-hybrid` (a meta-style that never enters direct ranking).

| Family | Count |
|---|---|
| photographic-editorial | 5 |
| painterly-atmosphere | 5 |
| graphic-print | 5 |
| eastern-heritage | 5 |
| modern-design | 5 |
| conceptual-hybrid | 4 |
| portrait (photographic / painterly / documentary) | 3 |
| graphic-portrait (duotone identity stack) | 1 |

Routing is deterministic and never randomizes. Confidence is measured relative to the best
score achievable for that profile; a conservative override fires only when a genuinely weak
signal is matched closely by an editorial style.

An **artistic dial** responds to intent: an `artistic` / `painterly` / `experimental` tag or
an expressive mood unlocks art-directed styles. For a face, only the art-directed set is
unlocked and the face-repainting family stays excluded. An unannotated photo still routes
conservatively.

## Batch behaviour

Route every source independently. A soft penalty damps a style once it exceeds 3 uses in one
batch, so near-identical scenes spread out — but it never overrides a clear fit. Report
`style_repetition` and `unique_styles` from `batch` output.

## Project layout

```
posterloom/
  SKILL.md                     this manifest
  scripts/posterloom.py        CLI entrypoint
  scripts/make_poster.py       the one-command workflow
  scripts/scene_analyze.py     measure a photo from pixels
  scripts/match_reference.py   match a reference poster to a style
  scripts/rank_styles.py       scoring, routing, portrait guardrail, artistic dial
  scripts/face_identity.py     facial likeness lock
  scripts/compose_prompt.py    prompt assembly
  scripts/batch_plan.py        batch planning with repetition damping
  scripts/validate_repo.py     repo integrity
  scripts/gen_style_contracts.py  regenerate contracts from styles.json
  data/styles.json             style library (single source of truth)
  data/routing-rules.json      weights, thresholds, safety lists, artistic prior
  data/substrates.json         named substrates and inks with hex values
  data/compatibility.json      permitted hybrid pairs
  styles/<style-id>.md         one contract per style
  references/                  method notes
  schemas/                     JSON Schema for profiles and routes
  examples/                    runnable profiles
  evals/                       routing regression + visual rubric
```

## References

- [Scene analysis](references/scene-analysis.md) — profile fields, identity anchors, the analyzer
- [Style router](references/style-router.md) — ranking, artistic dial, portrait guard, hybrid rules
- [Identity preservation](references/identity-preservation.md) — likeness enforcement and QA
- [Prompt composer](references/prompt-composer.md) — how prompts are assembled
- [Composition](references/composition.md) and [typography](references/typography.md)
- [Anti-slop](references/anti-slop.md) — failure modes to actively avoid
- [Competitive review](references/competitive-review.md) — how this compares to other poster skills
- [Visual benchmark rubric](evals/rubric.md) — 0-2 scoring across 10 axes, 17/20 to pass
