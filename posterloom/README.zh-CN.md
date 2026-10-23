# PosterLoom

**自适应照片转海报 Skill** —— 把真实照片变成经过艺术指导的海报:像素级场景测量、确定性风格路由、
基于原图的 prompt 合成、克制的排版,以及明确的视觉质检。

遵循 [OpenAI Agent Skills](https://agentskills.io/home) 规范,任何能加载 `SKILL.md` 的智能体
都可以直接把目录放进去接入。

## 安装

```bash
curl -fsSL https://github.com/liuweispace/posterloom-sklls/archive/refs/heads/main.tar.gz | tar xz
mv posterloom-sklls-main/posterloom ~/.hermes/skills/posterloom
```

需要 Python 3.9+。仅用标准库 —— 无第三方依赖,无网络访问。
PNG 无需 Pillow;JPEG 分析需要它。

## 一条命令

```bash
cd posterloom

python3 scripts/posterloom.py make photo.jpg
```

从像素测量图片、选出风格、打印成品生成 prompt。
它会告诉你测到了什么、选了哪个风格、以及**哪些它决定不了**。

```bash
# 人像 —— 身份锁自动开启
python3 scripts/posterloom.py make photo.jpg --type portrait \
  --summary "Young man, black hair, hard side light" \
  --anchors "face shape,eye shape,hairline,skin tone" \
  --mood "quiet,intimate"

# "再艺术点" —— 解锁艺术向风格,但保住长相
python3 scripts/posterloom.py make photo.jpg --type portrait --tolerance high --tags artistic

# 给一张参考海报,匹配风格
python3 scripts/posterloom.py make photo.jpg --reference ref-poster.jpg

# 自己指定风格
python3 scripts/posterloom.py make photo.jpg --style duotone-identity-stack

# 机器可读输出
python3 scripts/posterloom.py make photo.jpg --json
```

然后把打印出来的 prompt 交给宿主的生图工具。

## 其他命令

```bash
python3 scripts/posterloom.py analyze photo.jpg --out profile.json  # 只测量
python3 scripts/posterloom.py match   ref-poster.jpg                # 只匹配
python3 scripts/posterloom.py route   profile.json                  # 风格排序
python3 scripts/posterloom.py prompt  profile.json                  # 编译 prompt
python3 scripts/posterloom.py batch   batch-profiles.json           # 批量规划
python3 scripts/posterloom.py styles --portrait                     # 列出风格
python3 scripts/posterloom.py show    editorial-portrait             # 查看风格合约
python3 scripts/posterloom.py validate profile.json                 # schema 校验
python3 scripts/posterloom.py selftest                              # 完整性自检
python3 evals/run_evals.py                                           # 路由回归测试
```

`route`、`prompt`、`batch`、`styles`、`make`、`match` 都支持 `--json`。
任何子命令失败都会以非零码退出并打印 `ERROR: ...`。

## 宿主机接入(OpenAI API)

```bash
curl -X POST https://api.openai.com/v1/skills \
  -H "Authorization: Bearer ***" \
  -F 'files=@posterloom.zip;type=application/zip'
```

zip 必须只含一个顶层 `posterloom/` 目录,内含且仅含一个 `SKILL.md`。

## 能力

- **35 种直接风格**,覆盖纪实摄影、绘画氛围、平面印刷、东方传统、现代设计、概念混合、纸感拼贴
  与人像家族,外加一个 `controlled-hybrid` 元风格。
- **像素级场景测量** —— `analyze` 直接从图片读出尺寸、宽高比、主色族、明度、对比度、饱和度、
  边缘密度、显著/安静区域与文字安全区。它只报像素能支撑的结论;主体类型、身份锚点、情绪
  会列进"需要你看",而不是瞎猜。
- **确定性路由**:置信度相对于该场景可达的最高分计算,避免稀疏 profile 被误判为弱匹配。
- **三种模式的人脸身份锁** —— `single`(复现源脸)、`repeat`(同一身份刻意重复)、
  `abstract`(派生人物、渲染成插画)。优先选用人像专用风格;重绘媒介与抽象身份风格在需要
  保脸时会被拒绝,除非显式要求重度变换。
- **具名色板带 hex** —— 纸基和油墨是具体数值,让模型执行颜色而不是理解形容词。
- **参考海报匹配** —— 给一张你喜欢的海报,匹配出最接近的内置风格。
- **批量规划**,带软性重复抑制。

## 目录结构

```
posterloom/
  SKILL.md                  清单(OpenAI Agent Skills 规范)
  scripts/posterloom.py     CLI: make | analyze | match | route | prompt | batch | styles | show | validate | selftest
  scripts/scene_analyze.py  从像素测量照片
  scripts/match_reference.py 参考海报匹配风格
  scripts/rank_styles.py    打分、路由、人像护栏、艺术向开关
  scripts/face_identity.py  人脸身份锁(三种模式)
  scripts/compose_prompt.py prompt 组装
  data/                     styles.json、routing-rules.json、substrates.json、compatibility.json
  styles/                   每个风格一份合约,文件名即风格 id
  references/               方法论笔记
  schemas/                  profile 与路由结果的 JSON Schema
  examples/                 可直接运行的 profile
  evals/                    路由回归用例 + 视觉评分标准
```

## 诚实的边界

PosterLoom 的身份保护是 **prompt 层**的:能显著降低人脸漂移,但**无法消除**,因为图像模型默认
就会重绘五官。要真正保证一致性,后端必须使用参考图条件(IP-Adapter、FaceID、InstantID),
并配合人脸嵌入相似度校验与自动重试。本 skill 会要求智能体出图后比对并重生成,但无法在程序层强制。

路由回归(35 例)通过,这只证明路由、prompt 组装、schema 与合约覆盖能正确执行,
**不代表**任何图像后端的渲染质量。

## 许可

MIT
