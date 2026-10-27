# 办公 Office

办公类 Skill 集合。每个 Skill 是一个独立目录，含 `SKILL.md` 与配套脚本。

| Skill | 说明 |
|---|---|
| [reference-image-to-editable-pptx](reference-image-to-editable-pptx/) | 参考图片全画布高精度复现为可编辑 PowerPoint。框体、文字、箭头全部重建为 PPT 原生对象，图标重绘为 SVG，禁止整页截图贴图。 |

## 安装

把 Skill 目录复制到 Hermes 的 skills 目录：

```bash
cp -r office/reference-image-to-editable-pptx ~/.hermes/skills/
```

## 依赖

- Python 3.10+，Pillow、NumPy、python-pptx
- LibreOffice（渲染验收必需）：`brew install --cask libreoffice`
- `poppler`（pdftoppm）：`brew install poppler`
- SVG → PNG：cairosvg / rsvg-convert / qlmanage 三选一自动降级
