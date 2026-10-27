# Changelog｜更新记录

## 1.8.0 — 2026-10-27

### 三图 = 三种不同设计

`render --count 3` 之前只调用一次 API 的 `n=3`,返回的是**同一个 prompt 的三个随机样本**——
构图完全一样,只有细节抖动。现在每张图使用**独立 prompt + 独立请求**。

- 新增 `scripts/variation.py` —— 按身份模式提供 4 套布局变体池
  (`REPEAT_VARIANTS` / `ABSTRACT_VARIANTS` / `SINGLE_VARIANTS` / `SCENE_VARIANTS`)
- `compact_prompt.py` 新增 `layout_override` 与独立 `ARRANGEMENT:` 段
  - `ARRANGEMENT` 放 LAYOUT 前会被风格默认构图反向覆盖;与 LAYOUT 共用段会被预算裁剪吞掉
- 有变体时 `STYLE` 印刷机制段升级为 required
  —— 否则输出会从平面双色印刷退化为 duotone 照片
- 三张保持同一风格、同一色板、同一媒介、同一身份锁,只改变裁切、主体位置、留白与排列
- prompt 预算检查从 210 组扩到 **630 组**,新增 ARRANGEMENT / STYLE 存在性
  与三 prompt 差异校验
- `posterloom.py selftest` 增至 9 项

### 办公栏目

新增顶层 [`office/`](office/) 目录,收录第一个办公类 Skill:
**参考图片全画布高精度复现为可编辑 PowerPoint**。

- `office/reference-image-to-editable-pptx/` —— 把参考图**重建**为可编辑 PPTX
- 框体、文字、箭头全部为 PPT 原生对象;图标重绘为 SVG,不裁切原图
- 参考图像素画布即唯一坐标系:无 `uniform_scale`、无 `offset_x/offset_y`、无 contain / fit / letterbox
- 页面比例用整数 EMU 构造,宽高比误差**严格为 0**
- 渲染后与参考图做全画布像素比对:占用率 ≤ 0.5%、内容中心 ≤ 0.3%、四个主框体每边 ≤ 3–5 像素
- 端到端自测 **40/40 PASS**(真实渲染 + 全部阈值校验)
- Skill 更名为 `reference-image-to-full-canvas-editable-pptx`
  (Skill 名称 `Reference-Image-to-Full-Canvas-Editable-PPTX`)
- 新增 `references/SPEC-original.md` —— 原始 24 节完整规格书存档,一字未删
- Skill 目录名缩短为 `office/reference-image-to-pptx`
  (Skill 名 `Reference-Image-to-Full-Canvas-Editable-PPTX` 保留在 SKILL.md frontmatter)
- 用户提示词合并为**一条提示词**:同时完成"找 skill + 装 + 干活",
  使用者不需要知道 GitHub 地址长什么样
  (`templates/user-prompt.md` 顶部新增「第 1 段 · 一条提示词搞定」)
- 用户上手路径补全:
  - `templates/user-prompt.md` 改为三段式 —— 第 1 步「找到并装上」(GitHub 地址 /
    仓库内路径 / 装到本机的位置 / 装法 / 自测确认 / 缺依赖排错表)、
    第 2 步「让它干活」(三档提示词)、
    第 3 步「怎么验收」(交付物清单 + 三种自检命令 + 肉眼比对顺序)
  - SKILL.md 新增「我在哪」章节,写明自身路径与"先跑脚本、不要手写"的指引
  - 根 README 办公栏目补「在哪 & 怎么装」表 + 自测确认步骤 +
    "助手说找不到 skill 时的退路"提示词
- 仓库根 README 重构为 **Skills 集合首页**:
  开头先列「这里有什么」(两个 Skill + 分类表),每个 Skill 紧跟「怎么用」,
  再往下才是各 Skill 细节 —— 原来办公栏目埋在第 230 行,用户找不到
- SKILL.md 补回被压缩的四处内容:「输入与输出」(含 11 项必须输出)、
  「推荐导入」代码块、「验收阈值」独立章节、「执行清单(26 步)」

---

## 1.6.0 — 2026-10-23

新增两个纸感拼贴风格,并把人脸身份锁从一种模式扩展为三种。

- 新增 `gathered-scenes-zine`(实景拼贴)—— 照片为事实锚点 + 更大抽象插画场 + 手撕纤维边
- 新增 `scene-distillation-zine`(影像蒸馏)—— 照片仅作语义证据,输出纯插画,无任何照片像素
- 引入 per-style `source_role`(`visual-anchor` / `semantic-reference`),
  全局 prompt 块据此切换"保留照片"与"不得复现照片"
- 身份锁三模式:`single`(复现源脸)/ `repeat`(同一身份重复)/
  `abstract`(派生人物但渲染为插画),后者新增专属负向约束与派生式交付门
- 新增 `abstract_identity_styles` 路由护栏:需要保住长相的人像不会被路由进抽象身份风格
- 比例优先级重排:`requested_ratio` > `style.default_ratio` > 实测源比例 > `3:4`,
  修复照片实测比例覆盖风格设计比例的问题
- 新增 `data/substrates.json` 纸基 `aged cream #F2EBDC` 与 5 个新具名油墨
- 路由回归 35 例全通过;selftest 增至 6 项检查

## 1.5.0 — 2026-10-23

- 新增 `scripts/make_poster.py` 与 `posterloom.py make` —— 一条命令走完
  测量 → 匹配 → 路由 → 编译
- 新增 `scripts/match_reference.py` 与 `posterloom.py match` —— 参考海报匹配内置风格
- SKILL.md 重写收敛为紧凑入口文档,细节下沉到 references
- 删除一次性安装脚本 `add_portrait_styles.py`

## 1.4.0 — 2026-10-23

- 新增 `scripts/scene_analyze.py` —— 从像素测量照片(尺寸、宽高比、主色族、明度、
  对比度、饱和度、边缘密度、显著/安静区域、文字安全区)
- 新增 `scripts/check_analyzer_vocab.py` —— 分析器输出词表与 router 词表一致性校验
- 新增 `data/substrates.json` —— 具名纸基与油墨(带 hex),prompt 直接输出 hex
- 风格新增 `color_system` 字段,编译时生成 `COLOR SYSTEM` 块

## 1.3.0 — 2026-10-23

- 新增艺术向先验(`artistic_prior`)作为同分时的 tie-break
- 新增显式艺术意图开关(`artistic_request_boost`),人像在保持身份锁的同时解锁艺术向风格
- 风格改用 `routing` 子结构声明匹配词表

## 1.2.0 — 2026-09-28

- 新增 `duotone-identity-stack` 风格(同一身份重复的平面海报)
- 引入风格感知的身份锁条款(重复身份白名单)

## 1.1.0 — 2026-09-20

- 合约文件名去除数字前缀,与 `styles.json` 的 style id 一一对应
- `validate_repo.py` 合约数量改为动态计算

## 1.0.0 — 2026-09-16

PosterLoom 首个正式开源版本。

- 完成 29 个直接 Gold Style + 1 个 Controlled Hybrid 元风格
- 完成 Scene Analysis、Identity Preservation、AutoStyle Router
- 完成 74 个 Hybrid Compatibility Pair
- 完成 Prompt Composer、Batch Planner、Prompt Validator
- 完成 30 个路由回归测试
- 完成 10 项 Visual Benchmark
- 完成 GitHub Actions、MIT License、一键安装与一键发布
- 默认 README 改为中文,并保留 `README.en.md`
