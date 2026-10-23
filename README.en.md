# PosterLoom

**Adaptive Photo-to-Poster Skill** · 自适应照片转海报 Skill

> Analyze the scene. Adapt the style. Weave the poster.

![PosterLoom](posterloom/assets/posterloom-mark.svg)

---

## 📦 Install

```text
Install posterloom-sklls from GitHub for me, and use this skill for all
 image-generation tasks from now on.
```

Or manually:

```bash
curl -fsSL https://github.com/liuweispace/posterloom-sklls/archive/refs/heads/main.tar.gz | tar xz
mv posterloom-sklls-main/posterloom ~/.hermes/skills/posterloom
```

Requires Python 3.9+. Standard library only — no dependencies, no network access.

---

## ⚡ The one command

```bash
cd posterloom
python3 scripts/posterloom.py make photo.jpg
```

Measure from pixels → pick a style → print the finished generation prompt.
It reports what it measured, which style it chose, and **what it could not decide**
(subject type, identity anchors and mood need eyes).

Common variants:

```bash
# a person — the identity lock turns on automatically
python3 scripts/posterloom.py make photo.jpg --type portrait \
  --anchors "face shape,eye shape,hairline" --mood "quiet,intimate"

# "make it artistic" — unlocks art-directed styles, keeps likeness protection
python3 scripts/posterloom.py make photo.jpg --type portrait --tolerance high --tags artistic

# match a reference poster you like
python3 scripts/posterloom.py make photo.jpg --reference ref-poster.jpg

# machine-readable
python3 scripts/posterloom.py make photo.jpg --json
```

---

## 🧵 What it is

**PosterLoom** is an Agent Skill that turns a real photograph into an art-directed poster.

It is **not** an image model. It is the layer that:

- measures the scene from pixels — dimensions, aspect, palette families, luminance, contrast, saturation, edge density, salient and quiet regions, text-safe zones;
- hands back the fields pixels cannot decide (subject type, identity anchors, mood) instead of inventing them;
- protects the source's identity anchors — faces, geometry, materials, real text;
- routes the image to one of 35 direct visual styles, or to a constrained `Controlled Hybrid` of two compatible styles;
- recompiles the composition;
- applies restrained typography;
- quality-checks the result against an anti-slop checklist.

To produce a final poster, the host agent needs an image-generation or image-editing backend. Without one, PosterLoom still returns the route decision and the full generation prompt.

## 🎨 Style library

PosterLoom ships **36 style contracts** (35 direct + 1 meta) in **8 families**. Every style is a complete visual system — best-fit conditions, identity behavior, composition strategy, lighting language, color logic, material behavior, typography rules, a style-specific prompt block, a style-specific negative prompt, failure modes, and acceptance checks.

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

### 📄 Paper Collage — 2

Learned from the public `gathered-scenes-zine-skill` methodology, turned into routable, enforceable, verifiable style entries.

| Style | Use when |
|---|---|
| Gathered Scenes Zine | Travel / landscape / architecture / objects. The photo stays as the factual anchor, a larger abstract illustration field reinterprets source elements, a hand-torn fibrous edge, one high-chroma hue used as structure |
| Scene Distillation Zine | Emotional or conceptual posters, series work. The photo is semantic evidence only; the output is original illustration + paper + typography with no photographic pixels at all |

### 🧍 Portrait — 4

Preferred when a likeness has to survive.

| Style | Use when |
|---|---|
| Editorial Portrait | Magazine / interview likeness, natural skin |
| Photojournalistic | Maximum fidelity, captured moment |
| Fine-Art Portrait | Painted surface, likeness held constant |
| Duotone Identity Stack | One verified identity deliberately repeated as a print poster |

### 🧬 Meta-Style — 1

| Style | Use when |
|---|---|
| Controlled Hybrid | Two compatible direct styles both rank closely; the secondary controls one subsystem only (typography, negative space, print texture, ink edge, grid, color separation, or atmosphere). Default weight ≈ 80% primary / 20% secondary. No 50/50 split. |

## 🔒 Facial identity lock — three modes

Any source with a recognizable face gets an identity lock injected into its prompt. The mode is decided by the **routed style**, never by the model:

| Mode | Applies to | What the lock demands |
|---|---|---|
| `single` | most styles | reproduce the face: shape, eye shape and spacing, brow, nose and mouth, jawline, hairline, skin tone, age, expression, gaze |
| `repeat` | Duotone Identity Stack | every copy is the same verified person — no drift into another face, no averaged face |
| `abstract` | Scene Distillation Zine | **derive, do not invent**: head shape, head angle, hairline, age cues, gesture and gaze must trace to the source, but must be rendered as illustration, never as a photographic likeness |

`abstract` is not a weakened lock. It is the same guarantee restated in the only form that style can honour: generalize the rendering, never the identity.

The guardrail behind it: a portrait whose likeness must survive is not routed into a face-repainting medium or an abstract-identity style unless heavy transformation was explicitly requested. The reason is reported in the route.

## 🧭 How routing works

1. **Measure** — `analyze` reads dimensions, aspect, palette families, luminance, contrast, saturation, edge density, salient and quiet regions, and text-safe zones straight from the pixels.
2. **Hand back the semantic fields** — subject type, identity anchors, mood and transformation tolerance cannot be derived reliably from pixels, so they go to a `TODO` list instead of being invented.
3. **Score** — all 35 direct styles, weighted across subject / lighting / mood / geometry / materials / palette / realism / transform.
4. **Guard** — portraits get a likeness-protection boost; face-repainting and abstract-identity styles are excluded when likeness must survive.
5. **Pick the top style** — activate `Controlled Hybrid` only if the second-place style is explicitly compatible and allowed.
6. **Load only the chosen style's contract** — not all 36 at once.
7. **Compose the final prompt and negative prompt** — including hex values from the named colour system.
8. **Generate one poster, then run the anti-slop QA** (no blue-purple gradient, no random fog, no fake film borders, no invented landmarks, etc.).

## 🔬 Optional tools

| Command | Purpose |
|---|---|
| `posterloom.py analyze` | measure only, emit a profile |
| `posterloom.py match` | reference poster → closest built-in style |
| `posterloom.py make` | the whole workflow in one command |
| `posterloom.py route / prompt / batch` | rank / compile / plan a batch |
| `posterloom.py styles / show` | list styles / read one contract |
| `posterloom.py selftest` | 6 integrity checks |
| `evals/run_evals.py` | 35 routing regression cases |

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
    ├── styles/          # 36 style contracts
    ├── references/      # progressive-disclosure guidance
    ├── data/            # routing + compatibility + named substrates and inks
    ├── scripts/         # deterministic helpers
    ├── evals/           # routing regressions + visual rubric
    ├── schemas/
    ├── examples/
    └── assets/
```

---

## ⚖️ License

MIT for repository code and authored skill content. Source photographs and generated images remain subject to their own rights and the terms of the image-generation provider used by the host.
