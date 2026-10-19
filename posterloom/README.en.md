# PosterLoom

**Adaptive Photo-to-Poster Skill** — turns a real photograph into an art-directed poster:
scene analysis, adaptive style routing, source-aware prompt composition, restrained typography,
and explicit visual QA.

Built to the [OpenAI Agent Skills](https://agentskills.io/home) specification, so any agent that
can load a `SKILL.md` can adopt it by dropping the folder in.

## Install

```bash
curl -fsSL https://github.com/liuweispace/posterloom-sklls/archive/refs/heads/main.tar.gz | tar xz
mv posterloom-sklls-main/posterloom ~/.hermes/skills/posterloom
```

Requires Python 3.9+. Standard library only — no dependencies, no network access.

## Quick start

```bash
cd posterloom

python3 scripts/posterloom.py route   examples/scene-portrait.json   # rank styles
python3 scripts/posterloom.py prompt  examples/scene-portrait.json   # compile prompt
python3 scripts/posterloom.py batch   examples/batch-profiles.json   # plan a batch
python3 scripts/posterloom.py styles --portrait                      # list styles
python3 scripts/posterloom.py show    editorial-portrait              # one contract
python3 scripts/posterloom.py validate                                # schema check
python3 scripts/posterloom.py selftest                               # integrity checks
python3 evals/run_evals.py                                           # routing regression
```

Add `--json` for machine-readable output. Every command exits non-zero on failure.

## Host integration (OpenAI API)

```bash
curl -X POST https://api.openai.com/v1/skills \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F 'files=@posterloom.zip;type=application/zip'
```

The zip must contain a single top-level `posterloom/` folder with exactly one `SKILL.md`.

## What it does

- **32 direct styles** across photographic-editorial, painterly, graphic-print, eastern-heritage,
  modern-design, conceptual, and portrait families, plus a `controlled-hybrid` meta-style.
- **Deterministic routing** with confidence measured relative to what each profile can achieve,
  so a sparse scene profile is not mislabelled as a weak match.
- **Facial likeness locking** — any source containing a recognizable face gets an identity lock
  injected into its prompt, and face-designed styles are preferred over general-purpose ones.
- **Batch planning** with soft repetition damping.

## Layout

```
posterloom/
  SKILL.md                  manifest (OpenAI Agent Skills spec)
  scripts/posterloom.py     CLI: route | prompt | batch | styles | show | validate | selftest
  data/                     styles.json, routing-rules.json, compatibility.json
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

Routing regression (30 cases) passes, and that only proves routing, prompt assembly, schemas, and
contract coverage execute correctly. It says nothing about how a given image backend will render.

## License

MIT
