# PosterLoom

**Adaptive Photo-to-Poster Skill** — turns a real photograph into an art-directed poster:
pixel-measured scene analysis, deterministic style routing, source-aware prompt composition,
restrained typography, and explicit visual QA.

Built to the [OpenAI Agent Skills](https://agentskills.io/home) specification, so any agent that
can load a `SKILL.md` can adopt it by dropping the folder in.

## Install

```bash
curl -fsSL https://github.com/liuweispace/posterloom-sklls/archive/refs/heads/main.tar.gz | tar xz
mv posterloom-sklls-main/posterloom ~/.hermes/skills/posterloom
```

Requires Python 3.9+. Standard library only — no dependencies, no network access.
PNG works without Pillow; JPEG analysis needs it.

## The one command

```bash
cd posterloom

python3 scripts/posterloom.py make photo.jpg
```

That measures the image from pixels, picks a style, and prints the finished generation prompt.
It reports what it measured, which style it chose, and what it could **not** decide.

```bash
# a person — the identity lock turns on automatically
python3 scripts/posterloom.py make photo.jpg --type portrait \
  --summary "Young man, black hair, hard side light" \
  --anchors "face shape,eye shape,hairline,skin tone" \
  --mood "quiet,intimate"

# "make it artistic" — unlocks art-directed styles, keeps likeness protection
python3 scripts/posterloom.py make photo.jpg --type portrait --tolerance high --tags artistic

# match a reference poster you like
python3 scripts/posterloom.py make photo.jpg --reference ref-poster.jpg

# override the style yourself
python3 scripts/posterloom.py make photo.jpg --style duotone-identity-stack

# machine-readable
python3 scripts/posterloom.py make photo.jpg --json
```

Then hand the printed prompt to the host's image tool.

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
python3 evals/run_evals.py                                           # routing regression
```

Add `--json` to `route`, `prompt`, `batch`, `styles`, `make`, and `match`.
Every subcommand exits non-zero and prints `ERROR: ...` on failure.

## Host integration (OpenAI API)

```bash
curl -X POST https://api.openai.com/v1/skills \
  -H "Authorization: Bearer ***" \
  -F 'files=@posterloom.zip;type=application/zip'
```

The zip must contain a single top-level `posterloom/` folder with exactly one `SKILL.md`.

## What it does

- **35 direct styles** across photographic-editorial, painterly, graphic-print, eastern-heritage,
  modern-design, conceptual, paper-collage and portrait families, plus a `controlled-hybrid`
  meta-style.
- **Pixel-measured scene analysis** — `analyze` reads dimensions, aspect, palette families,
  luminance, contrast, saturation, edge density, salient/quiet regions and text-safe zones
  straight from the image. It reports only what pixels can support; subject type, identity
  anchors and mood are listed as needing a vision model instead of being guessed.
- **Deterministic routing** with confidence measured relative to what each profile can achieve,
  so a sparse scene profile is not mislabelled as a weak match.
- **Facial likeness locking** in three modes — `single` (reproduce the face), `repeat`
  (one verified identity duplicated on purpose), and `abstract` (derive the figure, render it
  as illustration). Face-designed styles are preferred over general-purpose ones, and
  face-repainting and abstract-identity media are refused for a portrait unless heavy
  transformation was explicitly requested.
- **Named colour with hex values** — substrates and inks ship as concrete values, so the model
  executes a colour instead of interpreting an adjective.
- **Reference-poster matching** — point it at a poster you like and it picks the closest
  built-in style by measurable properties.
- **Batch planning** with soft repetition damping.

## Layout

```
posterloom/
  SKILL.md                  manifest (OpenAI Agent Skills spec)
  scripts/posterloom.py     CLI: make | analyze | match | route | prompt | batch | styles | show | validate | selftest
  scripts/scene_analyze.py  measure a photo from pixels
  scripts/match_reference.py match a reference poster to a style
  scripts/rank_styles.py    scoring, routing, portrait guardrail, artistic dial
  scripts/face_identity.py  facial likeness lock (three modes)
  scripts/compose_prompt.py prompt assembly
  data/                     styles.json, routing-rules.json, substrates.json, compatibility.json
  styles/                   one contract per style, named by style id
  references/               method notes
  schemas/                  JSON Schema for profiles and routes
  examples/                 runnable profiles
  evals/                    routing regression + visual rubric
```

## Honest limits

PosterLoom's likeness protection is prompt-level. It substantially reduces facial drift but cannot
eliminate it, because image models redraw faces by default. For guaranteed likeness you need
reference-image conditioning in the backend (IP-Adapter, FaceID, InstantID) plus a face-embedding
similarity check with automatic retry. The skill tells the agent to verify and regenerate, but it
cannot enforce that programmatically.

Routing regression (35 cases) passes, and that only proves routing, prompt assembly, schemas, and
contract coverage execute correctly. It says nothing about how a given image backend will render.

## License

MIT
