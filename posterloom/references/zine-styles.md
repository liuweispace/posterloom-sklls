# Zine styles — 纸感拼贴的两条路线

PosterLoom 1.6.0 起新增两个 direct 风格,同属 `paper-collage` 家族。
它们来自对公开 skill `gathered-scenes-zine-skill`(Zeejay0 / @Zeejay0)的方法论学习,
但**不是照搬**:原 skill 是一个独立的工作流(自己读图、自己写命题、自己出图),
PosterLoom 里它们是**可被路由、可被强制、可被验证的样式条目** —— 和其他 33 个风格
走同一套 `routing → prompt → validate` 管线。

参考来源:
- `https://github.com/Zeejay0/gathered-scenes-zine-skill`
  - `skills/scenes-gathered-zine-v1-3/SKILL.md` → `gathered-scenes-zine`
  - `skills/scene-distillation-zine-v1-3/SKILL.md` → `scene-distillation-zine`

**版权边界**:只吸收了可执行的方法结构(场景读取、抽象引擎、边缘处理、色彩结构、
构图家族、文本系统)。原 skill 末尾的署名/推广规则**未**被引入 PosterLoom 的任何输出。

---

## 两个风格的区别(最容易搞混的一点)

| | `gathered-scenes-zine` | `scene-distillation-zine` |
|---|---|---|
| 中文名 | 实景拼贴 | 影像蒸馏 |
| 照片在输出里 | **保留**真实照片像素 | **完全不出现** |
| `source_role` | `visual-anchor` | `semantic-reference` |
| 输出 | 照片 + 插画场 + 撕纸边 | 纯插画 + 纸 + 文字 |
| 适合 | 旅行/风景/建筑/器物 | 情绪表达/概念海报/系列 |
| 人脸 | 正常保留(走常规身份锁) | 抽象化(走 abstract 身份锁) |
| 比例 | 3:5 | 3:5(竖源)/ 5:3(横源) |

一句话:**实景拼贴是"照片 + 插画",影像蒸馏是"照片生插画"。**

---

## `gathered-scenes-zine` — 实景拼贴

核心签名:**真景为锚、插画成场、色彩成结构、撕纸成界、纸面会呼吸**

- 照片作为**事实锚点**保持真实,不被重画
- 一个**更大的**抽象插画场重新解释源图中的元素(不是描线,不是小配角)
- 密集细节(树叶/枝条/人群)压缩成少数几个大块安静形状
- **一个**高彩度色相,与插画共享源生形状,是结构而非装饰
- 照片与纸的交界是**手撕纤维边**
- 一处克制的微文字元素

### 强制使用

```bash
python3 scripts/posterloom.py make photo.jpg --style gathered-scenes-zine
```

### 它在路由里何时胜出

- 主体:风景 / 旅行 / 建筑 / 静物 / 器物 / 茶室
- 情绪:安静 / 沉静 / 冥想 / 温和
- 几何:负空间 / 留白 / 剪影 / 非对称
- 材质:纸 / 纸纹 / 植被 / 石 / 木
- 变换容忍度:medium 或 high

实测:静谧湖景 → `gathered-scenes-zine` 58.57 分,第二名 watercolor 43.58。

---

## `scene-distillation-zine` — 影像蒸馏

核心签名:照片是**语义证据**,不是视觉图层。输出只含原创插画、纸、文字。

**没有照片像素。** 这是硬约束,由三处共同保证:

1. `source_role: "semantic-reference"` → 全局块自动换成"语义证据"版本,
   不再要求模型"保留照片"
2. 风格 `prompt_block` 开头就写死 `NO PHOTOGRAPHY` 与
   `Do not reproduce, embed, crop, collage, trace, or retain photographic pixels`
3. `negative_prompt` 含 `No original photo fragments, no photorealistic regions,
   no photo windows, no tracing, no rotoscoping`

### 表达引擎(这是原 skill 最值钱的部分)

```
source fact → emotional residue → expressive proposition → central tension
            → visual metaphor → formal embodiment → interpretive opening
```

- **命题**:一句话,关系性的、源生具体的(不是"安静""治愈"这种空标签)
- **中央张力**:只选一个 —— 亲密/距离、庇护/禁闭、运动/静止、小/大、
  温暖/寒冷、记忆/消逝、秩序/生长、可见/隐藏、恒久/易碎
- **视觉隐喻**:把一个源生对象**换功能**(器物承载记忆 / 窗成为心理边界 /
  雪既保护又抹除),不要万能符号
- **解释性开口**:故意留一个关系不作答,让观众能进入作品但不被固定解读

### 强制使用

```bash
python3 scripts/posterloom.py make photo.jpg --style scene-distillation-zine
```

---

## 身份锁的三种模式

这是 1.6.0 最重要的安全改动。`scripts/face_identity.py` 现在有三种模式:

| 模式 | 样式 | 锁的内容 |
|---|---|---|
| `single` | 绝大多数风格 | 逐项复现源脸(face shape / eye / brow / nose / mouth / hairline / skin tone) |
| `repeat` | `duotone-identity-stack` | 同一个已验证身份重复 N 次,不得漂移成别人 |
| `abstract` | `scene-distillation-zine` | **派生锁**:必须能追溯到源(头型、头角度、发际线、年龄线索、姿态、视线),但必须渲染成插画而非照片 |

抽象模式不是"关掉身份锁"。它把锁重述成这个风格唯一能兑现的形式:
**泛化的是渲染,不是身份。** 同时加了新的负向约束
(`no photorealistic face`, `no celebrity lookalike`, `no model-default face` …)。

### 路由护栏

抽象身份风格对"需要保住长相的人"和"重绘画面的媒介"同样危险,
所以 `data/routing-rules.json` 新增 `abstract_identity_styles`:

- 默认容差的人像 → **不会**路由到 `scene-distillation-zine`,会被换到 identity-safe 风格
- 只有显式要求 heavy transformation(高容差)才解锁
- 提示语会说明原因:`generalizes the face by design; routed to X to protect likeness`

---

## 比例规则

两个 zine 风格有 `default_ratio: "3:5"`。比例优先级:

```
requested_ratio (用户显式 --ratio)
  > style.default_ratio (风格设计比例)
  > _measured_source_aspect (照片实测比例)
  > output_ratio (旧字段,兼容)
  > "3:4"
```

照片实测比例**不会**盖掉风格设计比例 —— 否则 3:5 的 zine 风格会被竖图/横图
悄悄改成 3:4 或 16:9,风格就没了。

`scene-distillation-zine` 的横源 5:3 由风格自身 prompt_block 的
"preserve source orientation as spatial logic" 条款处理。

---

## 可调旋钮

`gathered-scenes-zine`:
`illustration-grammar`(silhouette/contour/field/rhythm/cut-paper)、
`abstraction`(low/medium/high)、
`accent-hue`(source-resonance/temperature-counterpoint/focused-complement/quiet-harmony)、
`edge`(torn-fiber/layered-grayscale/stippled/natural-isolated)、
`text`(none/word/keyword-sequence/bilingual)、`paper`(warm-cream/cool-gray/white)

`scene-distillation-zine`:
`illustration-grammar`(cut-paper/dry-print/broken-contour/rhythm-field/fragment-stack/orbit)、
`edge`(torn-fiber/layered-grayscale/stippled/mark/natural-isolated)、
`accent-role`(focal-pin/counterweight/bridge/directional-cue/rhythmic-beat)、
`accent`(concentrated/distributed-supporting)、
`text`(none/word/fragment/multi-voice/full-field)、
`tension`(九组对立体,任选一组)

---

## 具名色板

两个风格都带 `color_system`,编译时直接输出 hex 块:

- 纸:`aged cream` `#F2EBDC`
- 墨:`graphite` `#4A4A48`、`warm-gray` `#8C8579`、`faded-black` `#2B2724`
- 强调色候选:`cobalt` `#2148B8`、`tomato-red` `#D6402F`、
  `pear-green` `#5FA845`、`lemon-yellow` `#E8C63F`、`magenta-pink` `#C63A7E`

覆盖率规则:插画场占 45–70%,其中 55–75% 保持未印的安静纸;
强调色 0.8–3%(影像蒸馏)或 2–6%/6–15%/10–20%(实景拼贴,按材质形态)。

---

## 回归覆盖

`evals/routing-cases.json` 新增两条精确主路由用例:

- `route-gathered-scenes-zine` — 静谧湖景
- `route-scene-distillation-zine` — 夜间空路(实验性/心理)

`selftest` 新增一条安全检查:抽象身份风格不得吞掉保脸人像,
且强制使用时身份锁必须切到 abstract 模式。
