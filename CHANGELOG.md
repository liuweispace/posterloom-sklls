# Changelog｜更新记录

## 1.7.0 — 2026-10-23

从"只出 prompt"升级为**直接出图**。一条命令:照片进,成品海报出。

### 新增

- 新增 `posterloom.py render` —— 照片 → 3 张成品海报,一条命令
- 新增 `scripts/render.py` —— 组装 测量 → 路由 → 视觉读图 → 编译 → 生图 流水线
- 新增 `scripts/describe.py` —— 视觉模型读主体身份卡(17 字段 JSON)+ 印刷/照片分类器
- 新增 `scripts/compact_prompt.py` —— 预算感知的 prompt 重建(不是截断)
- 新增 `scripts/generate.py` —— 可插拔生图后端,自带限制声明
- 新增 `data/backends.json` —— 后端能力声明(默认 MiniMax `image-01`)
- 新增 `references/generation-pipeline.md` —— 完整实测记录
- 新增 `scripts/check_prompt_budget.py` —— 210 组合预算与分节保全检查

### 三个实测结论(决定了整个架构)

1. **词表比长度更重要。** 同样结构下,`"features simplified into hard flat
   shapes"` 出印刷品,`"thick tousled black hair and a coral shirt"` 出照片。
   摄影性词汇会把模型拉回连续调。
2. **附参考图会强制照片渲染。** 完全相同的 prompt,不附图出平面印刷,
   附了图出照片,prompt 里明写"不是照片"也无效。
   => 默认改为"视觉模型读图 → 从文字生成"。
3. **像素统计无法区分印刷/照片。** 13 个样本上 flat_ratio、ink_ratio、
   hue_spread 区间几乎完全重叠。改用视觉模型分类(12/13)。

### 修复

- 句中截断会毁掉操作性子句 —— 改为按句取(`_first_sentences`)
- 预算收紧时 LAYOUT / COLOUR / NO PHOTOGRAPHY 被误丢 —— 改为受保护分节
- subject 被砍成 92 字符导致身份锁悬空 —— subject 设 230 字符下限
- 无脸场景因空锁跳过了整个裁剪循环 —— 修复

### 验证

- 210 组合(35 风格 × 3 场景 × 2 主体长度)全部在 1400 字符预算内,
  身份锁 / NO PHOTOGRAPHY / COLOUR / LAYOUT 全部保留
- 路由回归 35/35;selftest 增至 8 项检查
- 实测生成:crimson + chalk white 双色印刷,同一人的 4 张纵向叠印,
  硬边、细线刻与点刻颗粒,无照片像素

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
