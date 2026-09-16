# PosterLoom

**Adaptive Photo-to-Poster Skill｜自适应照片转海报 Skill**

> 读懂照片，自适应风格，把真实场景编织成海报。

[English README](README.en.md)

PosterLoom 是一套面向真实照片的 **Agent Skill**。它不是简单套滤镜，也不是随机挑一种"艺术风格"，而是先分析照片中的主体、空间、光线、色彩、材质和情绪，再保护最重要的识别特征，自动选择更合适的视觉系统，重新组织构图，并用克制的小字号排版完成一张真正的海报。

**PosterLoom 本身不是图像生成模型。**  
它负责的是：**场景分析 + 风格路由 + Prompt 编译 + 视觉约束 + QA**。

当宿主环境具备图像生成或图像编辑能力时，PosterLoom 可以继续完成最终海报生成；如果宿主没有图像工具，它也可以输出完整的 Scene Map、风格选择结果和最终生成 Prompt。

---

## ✨ v1.0.0 包含什么

- **29 个直接视觉风格**
- **1 个 Controlled Hybrid 元风格**
- **74 个明确允许的 Hybrid 配对**
- Scene Analysis｜场景分析
- AutoStyle Router｜自动风格路由
- Prompt Composer｜Prompt 编译器
- Batch Planner｜批量任务规划
- Prompt Validator｜Prompt 校验
- Identity Preservation｜主体识别保护
- Anti-Slop QA｜反 AI 套路化质量控制
- **30 个路由回归测试**
- **10 项真实视觉 Benchmark**
- 完整 `SKILL.md`

---

## 🎯 核心原则

### 1. 一张原图 = 一个独立任务 = 一张海报

批量上传 8 张照片时，默认流程是：

```text
8 张照片
→ 8 个 Scene Map
→ 8 次独立风格路由
→ 8 个独立 Prompt
→ 8 张独立海报
```

不会因为一次上传多张图片，就自动做成九宫格、拼贴、相册、Moodboard 或多图合集，除非用户明确要求。

### 2. 先保护原图，再谈风格

PosterLoom 会优先保护：

- 人物脸部、姿态、手势、服装轮廓
- 建筑屋顶、窗格、立面比例、透视
- 物体数量、轮廓、材质、标签
- 地点中的桥、水面、山体、街道方向
- 茶具、器物、民俗服饰、真实文字等文化识别点

如果某个风格会损害原图身份，系统应该减弱风格，而不是牺牲原图。

### 3. AutoStyle 不是随机抽风格

PosterLoom 会分析主体、光线、情绪、构图几何、材质、主色、写实程度和可接受的重构强度，再从 29 个直接风格中匹配。

`Controlled Hybrid` 不参与普通排名。只有当两个直接风格都非常适合，而且本身明确兼容时，才允许启用。

---

## 🎨 视觉风格体系

| 分类 | 风格 |
|---|---|
| 摄影编辑 | Cinematic Editorial、Moody Night Editorial、Travel Cover、Luxury Still-Life、Documentary |
| 绘画氛围 | Transparent Watercolor、Soft Gouache、Expressive Painting、Ink Wash Minimal、Pastel Atmosphere |
| 印刷图形 | Pop Screenprint、Riso、Relief Print、Retro Lithograph、Paper-Cut Graphic |
| 东方 / 文化 | Neo Ink、Tea-House Minimal、Classical Parchment、Seal & Calligraphy、Folk Narrative Color |
| 概念编辑 | Editorial Surrealism、Abstract Editorial、Minimal Symbolic、Collage-Lite Narrative |
| 现代设计 | Swiss Grid、Brutalist、Neo-Futurist、Geometric Color-Block、Elegant Serif |
| 元风格 | Controlled Hybrid |

每一种 Style 都有独立的 Style Contract，包括：

- 适合什么照片
- 哪些场景应该拒绝
- 主体如何保留
- 构图如何变化
- 光线如何处理
- 色彩如何组织
- 材质与纹理如何表达
- 字体如何使用
- 写实程度与重构强度
- Style-specific Prompt
- Negative Prompt
- 常见失败模式
- Self-check
- Acceptance Criteria

因此它不是"30 个不同名字的滤镜"，而是 30 套不同的视觉生成机制。

---

## 🔀 Controlled Hybrid

`Controlled Hybrid` 是元风格，不是普通第 30 个滤镜。

默认结构：

```text
Primary Style    ≈ 80%
Secondary Style  ≈ 20%
```

Secondary 只能控制 **一个子系统**，例如：

- Typography
- Negative Space
- Print Texture
- Ink Edge
- Grid
- Color Separation
- Atmosphere

不允许 50/50 混合、三种风格同时混、效果堆叠，或者为了"更艺术"而破坏原图身份。

---

## 🪶 排版原则

PosterLoom 默认坚持 **小文字、轻排版、图像主导**：

- 标题通常 1–4 个词
- 副标题可选
- 文字面积尽量控制在画面的 5–10% 以内
- 不覆盖人物脸部、手部、建筑核心结构、重要文字或主体轮廓
- 不自动编造地点、日期、品牌、历史信息
- 不编造中文或其他非拉丁字符

如果图像模型不擅长渲染文字，建议先生成画面，再进行第二次排版。

---

## 🧹 Anti-Slop

PosterLoom 会主动避免常见的"AI 味"：

- 默认蓝紫渐变
- 滥用 Glow / Bloom
- 随机雾气、粒子
- 假胶片边框、假漏光
- 虚构天空、地标
- 重复人物或物体
- 畸形建筑
- 塑料皮肤
- 乱加景深
- 漂浮元素
- 过大的标题
- 与原图无关的装饰图形
- 一键滤镜感

---

## 📁 项目结构

```text
PosterLoom/
├── README.md           # 默认中文
├── README.en.md        # English
├── LICENSE
├── CHANGELOG.md
└── posterloom/
    ├── SKILL.md
    ├── styles/          # 30 个 Style Contract
    ├── references/      # 规范与 QA
    ├── data/            # Router / Hybrid / Style 数据
    ├── scripts/         # Router / Composer / Validator
    ├── evals/           # 回归测试 + Visual Benchmark
    ├── schemas/
    ├── examples/
    └── assets/
```

---

# 🚀 安装

把你的 Agent 指向这个 Skill：

```text
$skill-installer install https://github.com/liuweispace/posterloom/tree/main/posterloom
```

或者直接把 `posterloom/` 文件夹复制到 Agent Skills 目录。

---

# 🖼️ 使用方法

上传一张真实照片，然后说：

```text
Use PosterLoom.

把这张照片做成 3:4 海报。
自动分析画面并选择最合适的风格。
保护原图主体、建筑和真实材质。
标题保持小、轻、克制。
```

批量照片：

```text
Use PosterLoom on these 8 photos.

每张照片独立分析、独立选风格、独立生成。
不要拼贴，不要九宫格，不要做成相册。
最终输出 8 张独立海报。
```

---

# 🛠️ CLI 工具

```bash
python posterloom/scripts/rank_styles.py posterloom/examples/scene-night-teahouse.json
```

```bash
python posterloom/scripts/compose_prompt.py \
  posterloom/examples/scene-night-teahouse.json \
  --output prompt.txt \
  --route-output route.json
```

```bash
python posterloom/scripts/validate_prompt.py prompt.txt
python posterloom/evals/run_evals.py
python posterloom/scripts/validate_repo.py posterloom
```

---

# 📊 关于"真实可用"

PosterLoom 当前的 Skill 结构、Style Contracts、AutoStyle Router、Hybrid Compatibility、Prompt Composer、Batch Rules、QA、Regression Tests 已经完成工程验证。

但最终成图仍然取决于：

- 原始照片
- 宿主模型的图像理解能力
- 实际使用的图像生成 / 编辑模型
- 不同模型对 Prompt 的执行方式

因此仓库提供 10 项 Visual Benchmark：

1. Identity Preservation
2. Composition
3. Lighting
4. Palette
5. Material Behavior
6. Edge Treatment
7. Typography
8. Source Specificity
9. Style Specificity
10. Anti-Slop

默认 **17 / 20** 才算通过。

工程测试通过，不等于所有图片模型、所有照片都一定得到完美结果。

---

# 📄 License

MIT License。

仓库代码和 PosterLoom 原创 Skill 内容按 MIT 发布。

用户自己的原始照片、第三方素材以及最终生成图片的权利，仍然取决于照片本身、相关素材许可，以及所使用图像生成服务的条款。

---

## PosterLoom

**Adaptive Photo-to-Poster Skill**

**Analyze the scene. Adapt the style. Weave the poster.**