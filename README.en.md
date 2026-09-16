# PosterLoom

**Adaptive Photo-to-Poster Skill**

> Analyze the scene. Adapt the style. Weave the poster.

PosterLoom is a source-aware Agent Skill for turning real photographs into art-directed posters. It analyzes each source, protects identity anchors, selects a fitting visual system, recompiles the composition, keeps typography restrained, and quality-checks the result.

**It is not an image model.** PosterLoom is the art-direction, routing, prompt-composition, and QA layer. To render final images, the host needs an image-generation or image-editing backend. Without one, PosterLoom still returns a structured route decision and a complete generation prompt.

## What ships in v1.0.0

- 29 direct visual styles
- 1 `Controlled Hybrid` meta-style
- 74 explicit compatible hybrid pairs
- source-scene analysis workflow
- deterministic AutoStyle ranking helper
- prompt compiler
- batch planner
- prompt validator
- identity-preservation rules
- anti-AI-slop rules
- 30 routing regression cases
- 10-axis visual benchmark rubric
- Agent Skills `SKILL.md`

## Style families

| Family | Styles |
|---|---|
| Photographic Editorial | Cinematic Editorial, Moody Night Editorial, Travel Cover, Luxury Still-Life, Documentary |
| Painterly Atmosphere | Transparent Watercolor, Soft Gouache, Expressive Painting, Ink Wash Minimal, Pastel Atmosphere |
| Graphic Print | Pop Screenprint, Riso, Relief Print, Retro Lithograph, Paper-Cut Graphic |
| Eastern Heritage | Neo Ink, Tea-House Minimal, Classical Parchment, Seal & Calligraphy, Folk Narrative Color |
| Conceptual | Editorial Surrealism, Abstract Editorial, Minimal Symbolic, Collage-Lite Narrative |
| Modern Design | Swiss Grid, Brutalist, Neo-Futurist, Geometric Color-Block, Elegant Serif |
| Meta | Controlled Hybrid |

## Why it is different

PosterLoom does not randomly choose a style and does not treat style names as presets. Each style has its own contract defining:
- best-fit and rejection conditions;
- source/identity behavior;
- composition strategy;
- lighting language;
- color logic;
- material/texture behavior;
- typography;
- transformation strength;
- a style-specific prompt mechanism;
- a style-specific negative prompt;
- failure modes and acceptance checks.

The router first builds a scene map, then scores direct styles. Controlled Hybrid can activate only after two compatible direct styles rank closely, and the secondary style may control one subsystem only.

## Repository layout

```text
PosterLoom/
├── README.md
├── README.zh-CN.md
├── README.en.md
├── LICENSE
├── CHANGELOG.md
├── VERSION
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── SECURITY.md
└── posterloom/
    ├── SKILL.md
    ├── styles/          # 30 style contracts
    ├── references/      # progressive-disclosure guidance
    ├── data/            # routing + compatibility data
    ├── scripts/         # deterministic helpers
    ├── evals/           # routing regressions + visual rubric
    ├── schemas/
    ├── examples/
    └── assets/
```

## Install

### From GitHub in Codex

```text
$skill-installer install https://github.com/YOUR_USERNAME/posterloom/tree/main/posterloom
```

### Manual

Copy the repository's `posterloom/` folder into your agent's skills directory.

## Example usage

Upload one photo and ask:

```text
Use PosterLoom.
Turn this image into a 3:4 poster.
Choose the style automatically, preserve the source identity,
and keep the title small and restrained.
```

For a batch:

```text
Use PosterLoom on these 8 photos.
Treat every photo as an independent job.
Do not create a collage.
Auto-route each image and return 8 independent posters.
```

## CLI helpers

```bash
python posterloom/scripts/rank_styles.py posterloom/examples/scene-night-teahouse.json
python posterloom/scripts/compose_prompt.py posterloom/examples/scene-night-teahouse.json --output prompt.txt --route-output route.json
python posterloom/scripts/validate_prompt.py prompt.txt
python posterloom/evals/run_evals.py
python posterloom/scripts/validate_repo.py posterloom
```

## Visual quality claims

The repository includes deterministic engineering tests for structure, routing, prompt composition, and compatibility. Those tests do **not** prove every image-generation backend will produce beautiful results.

Actual generated images should be scored with the included 10-axis benchmark:
identity, composition, lighting, palette, material, edges, typography, source specificity, style specificity, and anti-slop. Default pass threshold: **17/20**.

## Compatibility

`posterloom/SKILL.md` follows the open Agent Skills folder model: `SKILL.md` with required routing metadata plus progressively loaded resources.

## License

MIT for repository code and authored skill content. Source photographs and generated images remain subject to their own rights and the terms of the image-generation provider used by the host.