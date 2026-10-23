# Changelog｜更新记录

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
