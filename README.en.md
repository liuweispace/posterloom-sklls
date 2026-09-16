# PosterLoom

**Adaptive Photo-to-Poster Skill** · 自适应照片转海报 Skill

> Analyze the scene. Adapt the style. Weave the poster.

---

## Install

Point your agent at this skill:

```text
$skill-installer install https://github.com/liuweispace/posterloom/tree/main/posterloom
```

Or copy the `posterloom/` folder into your agent's skills directory.

---

## What it is

**PosterLoom** is an Agent Skill that turns a real photograph into an art-directed poster.

It is **not** an image model. It is the layer that:

- analyzes the scene (subject, space, light, color, material, mood);
- protects the source's identity anchors (faces, geometry, materials, real text);
- routes the image to one of 29 direct visual styles — or to a constrained `Controlled Hybrid` of two compatible styles;
- recompiles the composition;
- applies restrained typography;
- quality-checks the result against an anti-slop checklist.

To produce a final poster, the host agent needs an image-generation or image-editing backend. Without one, PosterLoom still returns the route decision and the full generation prompt.

---

## Project layout

```text
PosterLoom/
├── README.md
├── README.en.md
├── README.zh-CN.md
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

---

## License

MIT for repository code and authored skill content. Source photographs and generated images remain subject to their own rights and the terms of the image-generation provider used by the host.