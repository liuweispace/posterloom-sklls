# PosterLoom

**Adaptive Photo-to-Poster Skill** · 自适应照片转海报 Skill

> 读懂照片，自适应风格，把真实场景编织成海报。

---

## 安装

把你的 Agent 指向这个 Skill：

```text
$skill-installer install https://github.com/liuweispace/posterloom/tree/main/posterloom
```

或者直接把 `posterloom/` 文件夹复制到 Agent Skills 目录。

---

## 这是什么

**PosterLoom** 是一个把真实照片转成艺术海报的 Agent Skill。

它 **不是** 图像生成模型。它负责的是：

- 分析画面场景（主体、空间、光线、色彩、材质、情绪）；
- 保护原图的识别特征（人物脸部、建筑几何、材质、真实文字）；
- 在 29 个直接视觉风格中自动选一种，或在两个明确兼容的风格之间启用受控混合（`Controlled Hybrid`）；
- 重新组织构图；
- 应用克制的小字号排版；
- 按反 AI 套路化清单对结果做 QA。

要生成最终海报，宿主 Agent 需要具备图像生成或图像编辑能力。如果没有，PosterLoom 也会返回完整的路由决策和生成 Prompt。

---

## 项目架构

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
    ├── styles/          # 30 个 Style Contract
    ├── references/      # 渐进式加载的规范
    ├── data/            # 路由 + 兼容性数据
    ├── scripts/         # 确定性辅助脚本
    ├── evals/           # 路由回归 + 视觉打分模板
    ├── schemas/
    ├── examples/
    └── assets/
```

---

## License

MIT License。

仓库代码和 PosterLoom 原创 Skill 内容按 MIT 发布。

用户自己的原始照片、第三方素材以及最终生成图片的权利，仍然取决于照片本身、相关素材许可，以及所使用图像生成服务的条款。