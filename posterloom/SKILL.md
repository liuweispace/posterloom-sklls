---
name: posterloom
description: Turn a real photograph into a finished art-directed poster - measure the scene, route to 1 of 35 poster styles, and GENERATE the images. Use when the user wants a photo converted into an editorial, travel, cultural, painterly, print, portrait, paper-collage, or modern-design poster, wants a reference poster matched to a style, or wants a batch of independent posters from many photos. Produces finished images, not just prompts. Enforces facial likeness locking on any source containing a person.
license: MIT
metadata:
  version: "1.8.0"
  tagline: "Adaptive Photo-to-Poster Skill"
---

# PosterLoom

Turn a photograph into a finished poster. One command does the work and returns
**images, not a prompt**.

## The one command

```bash
python3 scripts/posterloom.py render photo.jpg --count 3
```

That measures the photo, picks a style, reads the subject with a vision model,
compiles a prompt that fits the image backend, and saves three finished posters.

**Three posters are three designs, not three samples of one design.** Each sheet
gets its own request with its own arrangement — a different crop, a different
placement, a different use of negative space. The style, the ink palette, the
medium and the identity lock are identical across the set.

```bash
# a person - the identity lock turns on automatically
python3 scripts/posterloom.py render photo.jpg --type portrait \
  --summary "Young man, black hair, hard side light" \
  --anchors "face shape,eye shape,hairline,skin tone" \
  --mood "quiet,intimate" --count 3

# "make it artistic" - unlocks art-directed styles, keeps likeness protection
python3 scripts/posterloom.py render photo.jpg --type portrait --tolerance high --tags artistic

# match a reference poster you like
python3 scripts/posterloom.py render photo.jpg --reference ref-poster.jpg

# override the style yourself
python3 scripts/posterloom.py render photo.jpg --style duotone-identity-stack --count 3

# machine-readable (stdout is pure JSON; the summary goes to stderr)
python3 scripts/posterloom.py render photo.jpg --count 3 --json
```

Images land in `./posterloom-out/` by default. `--out DIR` changes that. Each
file is named `<photo>-<variant>-1.jpg`, so the variant is visible in the
filename and the report.

## Two commands, two jobs

| Command | Produces | Use it when |
|---|---|---|
| `render` | **finished images** | the user wants posters |
| `make` | a generation prompt | the host has its own image tool, or you want to inspect the prompt first |

`make` is the same pipeline up to the prompt. `render` continues it.

```bash
python3 scripts/posterloom.py make photo.jpg
```

## How `render` works, and why

```
photo ──▶ measure ──▶ route ──▶ vision reads the subject ──▶ prompt ──▶ image API ──▶ 3 images
```

Three of those steps are not obvious, and all three were settled by measurement
rather than by preference. See [generation pipeline](references/generation-pipeline.md)
for the evidence.

**The photo is described, not attached.** Attaching the source photo to the image
request makes the model reproduce its continuous tone, and the flat-print style
collapses back into a photograph — the identical prompt returns a print without
the attachment and a photo with it, even when it says "render as a print, not a
photograph". So a vision model reads the photo first, and the image is generated
from words. `--send-reference` restores the attachment if you want maximum
likeness and can accept a photographic result.

**The prompt is rebuilt, not truncated.** A full PosterLoom prompt is 4000-8000
characters; image APIs reject anything over 1500. The compact prompt is rebuilt
from the same structured data so the identity lock, the named inks, the layout
and the colour survive. It never truncates mid-sentence, because a cut clause
loses the operation — that is how "repeat as a stack" turns into a single
portrait.

**Each sheet gets its own request.** One API call with `n=3` returns three
samples of the *same* prompt — the same composition three times, differing only
in grain and edge softness. The API takes one prompt per request, so distinct
designs need distinct requests. Each variant changes the arrangement only:
crop, placement, negative space. The variants are chosen from a pool that
respects the style's identity mode — a `repeat` style gets arrangements of
repeated copies, a `single` style never gains a second face.

## What `render` will not do

It will not guess `subject.type`, identity anchors, or mood — those need eyes. It
lists what is missing under `TODO` and tells you which flag fills it. Inventing
subject data would poison the style routing, which is the one thing this skill
exists to get right.

`realism_value` defaults to `high`; you only override it if you want something else.

## Everything else

```bash
python3 scripts/posterloom.py analyze photo.jpg --out profile.json  # measure only
python3 scripts/posterloom.py match   ref-poster.jpg                # match only
python3 scripts/posterloom.py route   profile.json                  # rank styles
python3 scripts/posterloom.py prompt  profile.json                  # compile the full prompt
python3 scripts/posterloom.py batch   batch-profiles.json           # plan a batch
python3 scripts/posterloom.py styles --portrait                     # list styles
python3 scripts/posterloom.py show    editorial-portrait             # one contract
python3 scripts/posterloom.py validate profile.json                 # schema check
python3 scripts/posterloom.py selftest                              # integrity checks
```

Add `--json` to `route`, `prompt`, `batch`, `styles`, `make`, `match`, and `render`.
Every subcommand exits non-zero and prints `ERROR: ...` on failure.
Zero dependencies — Python 3.9+ standard library only. PNG works without Pillow; JPEG needs it.

## Image backends

Backends are declared in `data/backends.json`. Each one declares its own limits,
because those limits change the workflow:

- **prompt length cap** — MiniMax rejects prompts at or above 1500 characters.
- **supported ratios** — MiniMax does not support `3:5`, which the two zine styles
  are designed around. The ratio is mapped to the nearest supported value and the
  substitution is **reported**, never silent.
- **whether a reference image can be attached**.

The default backend is MiniMax `image-01`. It reads its key from
`MINIMAX_API_KEY` in the environment or `~/.hermes/.env`. The key is never
written into a prompt, a log, the repo, or a generated file.

```bash
python3 scripts/posterloom.py render photo.jpg --backend minimax --ratio 2:3 --count 3
```

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
- `scene-distillation-zine` is the other exception: it renders a non-photographic
  illustration, so its clause becomes "derive, do not invent" - the figure must still
  trace back to the source (head shape, head angle, hairline, age cues, gesture, gaze)
  but must be rendered as illustration, never as a photographic likeness. A portrait
  whose likeness has to survive is not routed there unless heavy transformation was
  explicitly requested.

**The lock is a prompt constraint, not a guarantee.** No image API verifies a face. After
generation, compare the face against the source on the seven identity-critical points.
If any differ, regenerate — `--count 3` gives you variants to choose from.

**Typography stays subordinate.** Text normally occupies 5-10% or less of the visual area,
and never covers a face, key hand gesture, important sign, architectural crown, or defining
contour.

## Style library

35 direct styles plus `controlled-hybrid` (a meta-style that never enters direct ranking).

| Family | Count |
|---|---|
| photographic-editorial | 5 |
| painterly-atmosphere | 5 |
| graphic-print | 5 |
| eastern-heritage | 5 |
| modern-design | 5 |
| conceptual-hybrid | 4 |
| portrait (photographic / painterly / documentary) | 3 |
| paper-collage (gathered scenes / scene distillation) | 2 |
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
  scripts/render.py            photo -> finished images
  scripts/make_poster.py       photo -> prompt
  scripts/describe.py          vision: read a subject, classify a print
  scripts/compact_prompt.py    budget-aware prompt builder
  scripts/variation.py         per-variant layout directives
  scripts/generate.py          image backends
  scripts/scene_analyze.py     measure a photo from pixels
  scripts/match_reference.py   match a reference poster to a style
  scripts/rank_styles.py       scoring, routing, portrait guardrail, artistic dial
  scripts/face_identity.py     facial likeness lock
  scripts/compose_prompt.py    full prompt assembly
  scripts/batch_plan.py        batch planning with repetition damping
  scripts/check_prompt_budget.py  budget and section-preservation check
  scripts/validate_repo.py     repo integrity
  scripts/gen_style_contracts.py  regenerate contracts from styles.json
  data/styles.json             style library (single source of truth)
  data/backends.json           image backends and their limits
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

- [Generation pipeline](references/generation-pipeline.md) — how images are made, and the measurements behind each choice
- [Scene analysis](references/scene-analysis.md) — profile fields, identity anchors, the analyzer
- [Style router](references/style-router.md) — ranking, artistic dial, portrait guard, hybrid rules
- [Identity preservation](references/identity-preservation.md) — likeness enforcement and QA
- [Prompt composer](references/prompt-composer.md) — how prompts are assembled
- [Composition](references/composition.md) and [typography](references/typography.md)
- [Anti-slop](references/anti-slop.md) — failure modes to actively avoid
- [Competitive review](references/competitive-review.md) — how this compares to other poster skills
- [Zine styles](references/zine-styles.md) — the two paper-collage styles, and the three identity-lock modes
- [Visual benchmark rubric](evals/rubric.md) — 0-2 scoring across 10 axes, 17/20 to pass
