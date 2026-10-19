# PosterLoom

**自适应照片转海报 Skill** —— 把真实照片变成经过艺术指导的海报:场景分析、自适应风格路由、
基于原图的 prompt 合成、克制的排版,以及明确的视觉质检。

遵循 [OpenAI Agent Skills](https://agentskills.io/home) 规范,任何能加载 `SKILL.md` 的智能体
都可以直接把目录放进去接入。

## 安装

```bash
curl -fsSL https://github.com/liuweispace/posterloom-sklls/archive/refs/heads/main.tar.gz | tar xz
mv posterloom-sklls-main/posterloom ~/.hermes/skills/posterloom
```

需要 Python 3.9+。仅用标准库 —— 无第三方依赖,无网络访问。

## 快速开始

```bash
cd posterloom

python3 scripts/posterloom.py route   examples/scene-portrait.json   # 风格排序
python3 scripts/posterloom.py prompt  examples/scene-portrait.json   # 编译 prompt
python3 scripts/posterloom.py batch   examples/batch-profiles.json   # 批量规划
python3 scripts/posterloom.py styles --portrait                      # 列出风格
python3 scripts/posterloom.py show    editorial-portrait              # 查看风格合约
python3 scripts/posterloom.py validate                                # schema 校验
python3 scripts/posterloom.py selftest                               # 完整性自检
python3 evals/run_evals.py                                           # 路由回归测试
```

加 `--json` 输出机器可读结果。任何命令失败都会以非零码退出并打印 `ERROR:`。

## 宿主机接入(OpenAI API)

```bash
curl -X POST https://api.openai.com/v1/skills \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F 'files=@posterloom.zip;type=application/zip'
```

zip 必须只含一个顶层 `posterloom/` 目录,内含且仅含一个 `SKILL.md`。

## 能力

- **32 种直接风格**,覆盖纪实摄影、绘画氛围、平面印刷、东方传统、现代设计、概念混合与人像
  家族,外加一个 `controlled-hybrid` 元风格。
- **确定性路由**:置信度相对于该场景可达的最高分计算,避免稀疏 profile 被误判为弱匹配。
- **人脸身份锁定** —— 任何含可识别人脸的源图都会在 prompt 中注入身份锁,并优先选用人像专用
  风格而非通用风格。
- **批量规划**,带软性重复抑制。

## 目录结构

```
posterloom/
  SKILL.md                  清单(OpenAI Agent Skills 规范)
  scripts/posterloom.py     CLI: route | prompt | batch | styles | show | validate | selftest
  data/                     styles.json、routing-rules.json、compatibility.json
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

路由回归(30 例)通过,这只证明路由、prompt 组装、schema 与合约覆盖能正确执行,
**不代表**任何图像后端的渲染质量。

## 许可

MIT
