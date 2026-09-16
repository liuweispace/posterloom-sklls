# PosterLoom

**Adaptive Photo-to-Poster Skill** · 自适应照片转海报 Skill

> Analyze the scene. Adapt the style. Weave the poster.

![PosterLoom](posterloom/assets/posterloom-mark.svg)

---

## 📦 Install

```text
$skill-installer install https://github.com/liuweispace/posterloom-sklls/tree/main/posterloom
```

---

## 🧵 What it is

**PosterLoom** is an Agent Skill that turns a real photograph into an art-directed poster.

It is **not** an image model. It is the layer that:

- analyzes the scene — subject, space, light, color, material, mood;
- protects the source's identity anchors — faces, geometry, materials, real text;
- routes the image to one of 29 direct visual styles, or to a constrained `Controlled Hybrid` of two compatible styles;
- recompiles the composition;
- applies restrained typography;
- quality-checks the result against an anti-slop checklist.

To produce a final poster, the host agent needs an image-generation or image-editing backend. Without one, PosterLoom still returns the route decision and the full generation prompt.

## 🎨 Style library

PosterLoom ships **30 style contracts** in **7 families**. Every style is a complete visual system — best-fit conditions, identity behavior, composition strategy, lighting language, color logic, material behavior, typography rules, a style-specific prompt block, a style-specific negative prompt, failure modes, and acceptance checks.

### 📷 Photographic Editorial — 5

For shots that should still feel like photographs but read as posters.

| Style | Use when |
|---|---|
| Cinematic Editorial | Narrative-driven photo, anamorphic mood, magazine cover feel |
| Moody Night Editorial | Low-light, warm practicals, dark negative space, cultural intimacy |
| Travel Cover Poster | Place + season + one subject, evocative not literal |
| Luxury Still-Life Editorial | Product / object study, premium materials, calm lighting |
| Documentary Poster | Field photo with editorial weight, restraint over decoration |

### 🎨 Painterly Atmosphere — 5

For photos that should shift toward painted or atmospheric media.

| Style | Use when |
|---|---|
| Transparent Watercolor | Soft travel / botanical / quiet outdoor scenes |
| Soft Gouache | Children, animals, warm interiors, gentle color |
| Expressive Painting | Strong subject with emotional weight, visible brush energy |
| Ink Wash Minimal | Solitary subjects, large empty space, poetic mood |
| Pastel Atmosphere | Soft daylight, dream-like, fashion / still-life mood |

### 🖨️ Graphic Print — 5

For posterized, process-driven, mid-century or riso aesthetics.

| Style | Use when |
|---|---|
| Pop Screenprint | High-contrast subject, flat color, bold poster feel |
| Riso Poster | Slight misregistration, limited palette, indie zine mood |
| Relief Print | Woodblock / linocut look, hand-made texture |
| Retro Lithograph | Vintage editorial / travel-poster feel, layered stone-print look |
| Paper-Cut Graphic | Bold shapes, illustrative subject, narrative scene |

### 🏯 Eastern Heritage — 5

For subjects tied to Chinese, Japanese, or broader East-Asian visual culture.

| Style | Use when |
|---|---|
| Neo Ink Poster | Modern ink composition, big negative space, restrained type |
| Tea-House Minimal | Tea / wood / night interiors, cultural quiet mood |
| Classical Parchment | Calligraphic or literary subject, aged-paper warmth |
| Seal & Calligraphy Poster | Subject paired with real or stylized seal / text element |
| Folk Narrative Color | Folk-craft palette, narrative scene, generous color |

### 🌀 Conceptual Hybrid — 4

For photos that should become a conceptual or editorial statement.

| Style | Use when |
|---|---|
| Editorial Surrealism | Strong subject with one shifted conceptual element |
| Abstract Editorial | Reduce subject to shape / color blocks, magazine-cover logic |
| Minimal Symbolic Poster | One subject as a near-monogram symbol |
| Collage-Lite Narrative | Two layered ideas kept visually clean (not a moodboard) |

### 🧱 Modern Design — 5

For posters rooted in 20th / 21st-century design languages.

| Style | Use when |
|---|---|
| Swiss Grid Poster | Strong grid, sans-serif typography, geometric color |
| Brutalist Poster | Raw, large, asymmetric, anti-pretty intent |
| Neo-Futurist Layout | Architectural subject, technical-line language |
| Geometric Color-Block | Bold field / fashion / architectural subject, flat color |
| Elegant Serif Poster | Magazine-cover, fashion, beauty, premium feel |

### 🧬 Meta-Style — 1

| Style | Use when |
|---|---|
| Controlled Hybrid | Two compatible direct styles both rank closely; the secondary controls one subsystem only (typography, negative space, print texture, ink edge, grid, color separation, or atmosphere). Default weight ≈ 80% primary / 20% secondary. No 50/50 split. |

## 🧭 How routing works

1. Read the source image and build a **scene profile** — subject type, lighting, palette, mood, geometry, materials, text-safe zones, realism.
2. Lock **identity anchors** that must survive any style change.
3. Score all 29 direct styles against the scene profile.
4. Pick the top style. Activate `Controlled Hybrid` only if the second-place style is explicitly compatible and the user (or default) allows it.
5. Load only the chosen style's contract — not all 30 at once.
6. Compose the final prompt and negative prompt.
7. Generate one poster, then run the **anti-slop QA** check (no blue-purple gradient, no random fog, no fake film borders, no invented landmarks, etc.).

---

## 🗂️ Project layout

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

## ⚖️ License

MIT for repository code and authored skill content. Source photographs and generated images remain subject to their own rights and the terms of the image-generation provider used by the host.