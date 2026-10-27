# 办公 Office

办公类 Skill 集合。每个 Skill 是一个独立目录，含 `SKILL.md` 与配套脚本。

| Skill | 说明 |
|---|---|
| [参考图片全画布高精度复现为可编辑 PowerPoint 工程](reference-image-to-pptx/) | 把一张参考图**重建**为可编辑 PPTX：框体、文字、箭头全部重建为 PPT 原生对象，图标重绘为 SVG。禁止整页截图贴图、禁止缩放留白。 |

Skill 名称：`Reference-Image-to-Full-Canvas-Editable-PPTX`
调用名（目录名）：`reference-image-to-pptx`

核心约束：**参考图的像素画布就是唯一坐标系**。所有对象在参考图像素坐标中测量，
直接映射到页面 —— 没有 `uniform_scale`，没有 `offset_x/offset_y`，没有 contain / fit / letterbox。

验收不是"看起来差不多"，而是渲染 PPT 后与参考图做全画布像素比对：
宽高比误差 0、占用率误差 ≤ 0.5%、内容中心误差 ≤ 0.3%、四个主框体每条边误差 ≤ 3–5 像素。

原始 24 节完整规格书：[`reference-image-to-pptx/references/SPEC-original.md`](reference-image-to-pptx/references/SPEC-original.md)

用户提示词模板（一条提示词完成安装+干活）：
[`reference-image-to-pptx/templates/user-prompt.md`](reference-image-to-pptx/templates/user-prompt.md)

## 安装

```bash
curl -fsSL https://github.com/liuweispace/posterloom-sklls/archive/refs/heads/main.tar.gz | tar xz
mv posterloom-sklls-main/office/reference-image-to-pptx ~/.hermes/skills/reference-image-to-pptx
cd ~/.hermes/skills/reference-image-to-pptx && python3 scripts/selftest.py
```

⚠️ 装到顶层 `~/.hermes/skills/`，**不要**装在 `posterloom/office/` 嵌套层 ——
嵌套会让 Hermes 把同名 Skill 加载两次（既浪费上下文，也可能触发
「找不到这个技能」的判断）。

验收标准：`40/40 PASS  SELFTEST OK`

## 依赖

- Python 3.10+，Pillow、NumPy、python-pptx
- LibreOffice（渲染验收必需）：`brew install --cask libreoffice`
- `poppler`（pdftoppm）：`brew install poppler`
- SVG → PNG：cairosvg / rsvg-convert / qlmanage 三选一自动降级

## 自测

```bash
cd ~/.hermes/skills/reference-image-to-pptx
python3 scripts/selftest.py     # 端到端：真实渲染 + 全部阈值校验
```

## 目录结构

```text
office/
├── README.md                          ← 本文件（栏目索引）
└── reference-image-to-pptx/
    ├── SKILL.md                       ← 正式执行版（Agent 读这个）
    ├── references/
    │   ├── SPEC-original.md           ← 原始 24 节完整规格书
    │   └── field-notes.md             ← 实测踩坑记录
    ├── scripts/
    │   ├── build_editable_ppt.py      ← 核心 PPT 引擎
    │   ├── validate_spec.py           ← scene_spec 校验器
    │   ├── redraw_icon.py             ← 9 类 SVG 图标重绘
    │   ├── make_manifest.py           ← manifest 生成
    │   ├── package_outputs.py         ← PPTX/ZIP 打包
    │   └── selftest.py                ← 40 项端到端自测
    └── templates/
        └── user-prompt.md             ← 用户提示词模板
```
