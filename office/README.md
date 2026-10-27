# 办公 Office

办公类 Skill 集合。每个 Skill 是一个独立目录，含 `SKILL.md` 与配套脚本。

| Skill | 说明 |
|---|---|
| [参考图片全画布高精度复现为可编辑 PowerPoint 工程](reference-image-to-full-canvas-editable-pptx/) | 把一张参考图**重建**为可编辑 PPTX：框体、文字、箭头全部重建为 PPT 原生对象，图标重绘为 SVG。禁止整页截图贴图、禁止缩放留白。 |

Skill 名称：`Reference-Image-to-Full-Canvas-Editable-PPTX`

核心约束：**参考图的像素画布就是唯一坐标系**。所有对象在参考图像素坐标中测量，
直接映射到页面 —— 没有 `uniform_scale`，没有 `offset_x/offset_y`，没有 contain / fit / letterbox。

验收不是"看起来差不多"，而是渲染 PPT 后与参考图做全画布像素比对：
宽高比误差 0、占用率误差 ≤ 0.5%、内容中心误差 ≤ 0.3%、四个主框体每条边误差 ≤ 3–5 像素。

原始 24 节完整规格书：[`reference-image-to-full-canvas-editable-pptx/references/SPEC-original.md`](reference-image-to-full-canvas-editable-pptx/references/SPEC-original.md)

## 安装

```bash
cp -r office/reference-image-to-full-canvas-editable-pptx ~/.hermes/skills/
```

## 依赖

- Python 3.10+，Pillow、NumPy、python-pptx
- LibreOffice（渲染验收必需）：`brew install --cask libreoffice`
- `poppler`（pdftoppm）：`brew install poppler`
- SVG → PNG：cairosvg / rsvg-convert / qlmanage 三选一自动降级

## 自测

```bash
cd office/reference-image-to-full-canvas-editable-pptx
python3 scripts/selftest.py     # 端到端：真实渲染 + 全部阈值校验
```
