---
name: reference-image-to-pptx
description: Use when a user provides a reference image (infographic, scientific diagram, slide screenshot, PDF page) and wants it rebuilt as an editable PowerPoint. Rebuilds every element as a native PPT object on the reference's exact pixel canvas — no screenshot-as-slide, no letterboxing, no auto-layout. 中文名：参考图片全画布高精度复现为可编辑 PowerPoint 工程。
version: 1.0.0
license: MIT
---

# 参考图片全画布高精度复现为可编辑 PowerPoint 工程

**Skill 名称**：Reference-Image-to-Full-Canvas-Editable-PPTX
**中文名称**：参考图片全画布高精度复现为可编辑 PowerPoint 工程

> 原始 24 节完整规格书见 [`references/SPEC-original.md`](references/SPEC-original.md)。
> 本文件是它的 Agent Skill 化改写版；两者措辞冲突时以规格书为准。

把一张参考图片**重建**成真正可编辑的 PPTX。不是重新设计，不是生成相似风格页面，
更不是把参考图缩小后塞进 PPT。

## 我在哪

| | |
|---|---|
| **GitHub** | `https://github.com/liuweispace/posterloom-sklls` |
| **仓库内路径** | `office/reference-image-to-pptx/` |
| **装到本机** | `~/.hermes/skills/reference-image-to-pptx/`（顶层，**不要**装在 `posterloom/office/` 嵌套层 —— 嵌套会让 Hermes 重复加载同名 Skill） |
| **正式 Skill 名** | `Reference-Image-to-Full-Canvas-Editable-PPTX` |
| **目录名（调用用这个）** | `reference-image-to-pptx` |

本 Skill 自带**可执行脚本**，不要只凭这份文档手写流程：

```bash
# 1. 校验对象表
python3 scripts/validate_spec.py scene_spec.json --ref source/reference_image.png

# 2. 生成 PPT + 渲染 + 三种对比图 + report.json
python3 scripts/build_editable_ppt.py \
    --reference source/reference_image.png --spec scene_spec.json \
    --out ppt --render preview --icons icons

# 3. 重绘图标 SVG（9 种）
python3 scripts/redraw_icon.py --kind trophy --out icons/svg/trophy_blue.svg --color "#1B7FBF"

# 4. 生成 manifest.txt
python3 scripts/make_manifest.py --project . --reference source/reference_image.png

# 5. 打包（工程 ZIP + 图标 ZIP + PPTX）
python3 scripts/package_outputs.py --project . --out .

# 自测（真实渲染 + 全部阈值）
python3 scripts/selftest.py
```

**先跑脚本，不要从零手写 PPT 生成代码** —— 坐标映射、Alpha 定位、原生箭头、
占用率测量这些都已经实现并验证过（自测 40 项）。

---

## 角色

你是一名 PowerPoint 工程重建专家、视觉测量工程师、矢量图标绘制师和
PPT 渲染质量检查工程师。

## 核心原则

**参考图的像素画布就是唯一坐标系。**

所有对象在参考图像素坐标中测量，然后直接映射到 PPT 页面。不存在
`uniform_scale`、不存在 `offset_x/offset_y`、不存在 contain / fit / letterbox /
shrink-to-fit。`X(0)` 就是 PPT 左上角，`X(REF_W)` 就是右下角。

这一条是整个任务成败的分水岭。本仓库里所有"看起来对但交付就是不对"的失败，
根因都是三个词之一：`uniform_scale`、`offset_x`、`offset_y`。

## 输入与输出

**输入可能包括**：一张参考图片；多张参考图片；PNG / JPEG / WEBP；PDF 页面或演示文稿截图；
中文或英文信息图；包含框体、图标、箭头和流程结构的科研图表。

**默认规则**

1. 每张参考图片对应一页 PPT。
2. 多张图片按用户上传顺序生成多页 PPT。
3. 不要求用户手动标注对象。
4. 不要求用户手动编号图标。
5. 不要在开始前要求用户拆分图片。
6. 图片可以正常读取时，直接开始执行。

**必须输出**（11 项）

1. 可编辑 PPTX
2. 完整工程 ZIP
3. 图标素材 ZIP
4. 每个图标的 SVG
5. 每个图标的 128×128 透明 PNG
6. PPT 渲染图
7. 参考图与 PPT 的并排对比图
8. 参考图与 PPT 的透明叠加图
9. 像素差异图
10. 图标总览图
11. manifest.txt

---

## 工具链

| 用途 | 工具 | 备注 |
|---|---|---|
| 图像处理 | Pillow + NumPy | 必需 |
| PPT 生成 | python-pptx | 必需 |
| SVG → PNG | CairoSVG（首选）/ rsvg-convert / qlmanage | 三选一自动降级 |
| PPT 渲染 | LibreOffice (`soffice`) + pdftoppm | **必需**，缺失则无法验收 |
| 打包 | zipfile | 必需 |

推荐导入：

```python
from pathlib import Path
import shutil
import zipfile
import subprocess
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops
import cairosvg
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.dml.color import RGBColor
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import qn
```

安装 LibreOffice：

```bash
brew install --cask libreoffice
```

没有 LibreOffice 就只能生成 PPTX、无法渲染、无法比对、无法验收 —— 这种情况下
**必须明确告知用户缺少验收环节**，不能声称已完成。

## 执行流程

严格按阶段执行。不要跳到第 13 步直接生成 PPT。

### 阶段 1 — 建立项目目录

```
editable_ppt_project/
├── ppt/          # editable_reproduction.pptx
├── icons/
│   ├── svg/      # 重绘的矢量图标
│   └── png_128/  # 128×128 透明 PNG
├── preview/      # 渲染图 + 三种对比图 + icons_preview.png
├── source/       # reference_image.png
└── manifest.txt
```

### 阶段 2 — 读取参考图真实尺寸

用 Pillow 读文件，绝不根据界面缩略图猜测。

```python
reference = Image.open(reference_path).convert("RGB")
REF_W, REF_H = reference.size
```

### 阶段 3 — 创建同比例页面

```python
SLIDE_W_IN = 16
SLIDE_H_IN = SLIDE_W_IN * REF_H / REF_W
prs.slide_width = Inches(SLIDE_W_IN)
prs.slide_height = Inches(SLIDE_H_IN)
```

> **实现提示**：`build_editable_ppt.py` 用整数 EMU 构造页面，并把参考比例约分后
> 取整数倍，保证**宽高比误差精确为 0**。直接用 float 英寸会让比例差几个
> ppm，肉眼看不见，但"宽高比误差 0"的验收项就永远只是"碰巧成立"。

### 阶段 4 — 建立唯一坐标映射

```python
def X(px): return Inches(px / REF_W * SLIDE_W_IN)
def Y(py): return Inches(py / REF_H * SLIDE_H_IN)
```

所有 x / y / w / h 一律经此转换。**在坐标映射之外禁止再叠加任何全局偏移或缩放。**

### 阶段 5 — 先建对象表，再动 PPT

不要一边观察一边随手加形状。先写出完整的 `scene_spec`：

```json
{
  "page": {"width_px": 2048, "height_px": 1152, "background": "#FDFEFF"},
  "frames": [], "texts": [], "icons": [], "connectors": []
}
```

**框体**：`name / type / x / y / w / h / fill / line / line_width_px / corner_radius / dash / z`

**文字**：`name / text / x / y / w / h / font / font_size_px / bold / color / align / vertical_align / margin_*_px / z`

**图标**：`name / asset / target_visible_x / target_visible_y / target_visible_w / target_visible_h / z`
（图标坐标是**参考图中的可见轮廓框**，不是 PNG 完整框）

**箭头**：`name / type / x1 / y1 / x2 / y2 / line / line_width_px / end_arrow / start_arrow / layer / z`
（`layer` 取 `outer`（跨模块，画在框体之下）或 `inner`（模块内部））

用 `scripts/validate_spec.py` 校验后再生成。

### 阶段 6 — 坐标测量

所有主要对象都在参考图像素坐标中测量：页面边界、主标题、四个主模块外框、
每个标题栏、每个子卡片、每个圆形容器、每个虚线框、每个图标可见轮廓、
每个文字框、每条箭头的起止点与转向关系。

**不得假设卡片等宽，不得假设间距相等，不得用自动平均分布代替原图位置。**

若初步测量在缩小预览图上完成，用中间工程坐标系再映射回真实参考图：

```python
ENG_W, ENG_H = 1686, 945
def sx(x): return x * REF_W / ENG_W
def sy(y): return y * REF_H / ENG_H
```

但进入 PPT 的坐标**必须**再经 `X()/Y()` 全画布映射。

### 阶段 7 — 图标处理

**优先复用已批准的重绘 SVG**（`icons/svg/*.svg`），不重复裁切。

没有可复用 SVG 时**重新绘制**。必须画出外轮廓、内部结构、圆角、线帽、
线连接、镂空、实心区域和颜色。

**禁止**：裁切参考图、截图去背景、AI 放大后使用、SVG 内嵌位图、用图库相似图标替换。

用 `scripts/redraw_icon.py` 生成 SVG：

```bash
python3 scripts/redraw_icon.py --kind trophy --out icons/svg/trophy_blue.svg --color "#1B7FBF"
```

可用 kind：`trophy / flask / brain / gear / document / chart / database / shield / target`

渲染成 128×128 透明 PNG（`build_editable_ppt.py` 的 `svg_to_png_128()` 自动选工具）：

```python
cairosvg.svg2png(url=str(svg_path), write_to=str(png_path),
                 output_width=128, output_height=128)
```

PNG 必须是 128×128、RGBA、真透明、四角 Alpha 为 0、不贴边、不裁切、无矩形底色、无白边、无缺线。

### 阶段 8 — 按可见轮廓插入图标

```python
fx, fy, fw, fh = alpha_bbox_fraction(png_path)   # 可见轮廓占 128×128 的比例
visible_px_w = fw * 128
visible_px_h = fh * 128
scale = min(target_w / visible_px_w, target_h / visible_px_h)
shape_w = 128 * scale
shape_h = 128 * scale
shape_x = target_x + (target_w - visible_px_w * scale) / 2 - fx * 128 * scale
shape_y = target_y + (target_h - visible_px_h * scale) / 2 - fy * 128 * scale
slide.shapes.add_picture(str(icon_path), X(shape_x), Y(shape_y),
                         X(shape_w), Y(shape_h))
```

**不得**把 128×128 整体框直接对齐到可见框，**不得**拉伸图标。

### 阶段 9 — 生成 PPT 原生对象

- 背景：`slide.background.fill.solid()` + RGBColor。**不得用参考图当背景。**
- 框体：`add_shape(MSO_SHAPE.ROUNDED_RECTANGLE / RECTANGLE / OVAL / ...)`
- 文字：`add_textbox()`，必须设 `margin_left/right/top/bottom` 和 `vertical_anchor`；
  每个段落 `space_before = space_after = Pt(0)`；每个 run 设 `font.name/size/bold/color.rgb`
- 箭头：`add_connector(MSO_CONNECTOR.STRAIGHT / ELBOW / CURVE)`，
  箭头头部用 Open XML 的 `a:tailEnd` / `a:headEnd`（`type="triangle"`）

> **实现提示**：`python-pptx` 的 `add_shape()` 会挂一个主题 `<p:style>`，在
> PowerPoint 里就是**默认投影**。参考图没有阴影，所以必须剥掉它
> （`strip_theme_style()`）。同理，字体和线宽要用 `font_size_px` /
> `line_width_px` 按画布比例换算成 pt，否则文字和边框会整体偏大偏粗。

**禁止** Freeform、PNG 箭头、SVG 箭头、多段普通线拼接、三角形加线段。

### 阶段 10 — 固定图层顺序

PowerPoint 中后添加的在上层。按此顺序添加：

1. 页面背景
2. 跨模块连接符和箭头（`layer: outer`）
3. 主模块外框
4. 模块标题栏
5. 子模块和卡片
6. 内部连接符（`layer: inner`）
7. 图标
8. 文字
9. 顶层说明标签

不要先放文字再放覆盖文字的色块；不要最后加跨模块箭头盖住文字和图标。

### 阶段 11 — 至少三轮构建

| 轮次 | 目标 |
|---|---|
| 第 1 轮 · 结构版 | 页面尺寸、主框体、标题栏、卡片、原生箭头、初步文字与图标 —— 验证整体结构与占用率 |
| 第 2 轮 · 视觉精调版 | 按渲染对比调整文字位置、文本框尺寸、图标可见大小与中心、卡片尺寸、标题栏高度、箭头端点与弧度 |
| 第 3 轮 · 全画布验收版 | 验证整体未被缩小、右侧无大块空白、底部无大块空白、内容居中正确、四边占用率正确、主框体匹配、无对象越界、无文字溢出 |

**只有第 3 轮通过才允许交付。** 验收阈值见下方「验收阈值」章节。

文字必须做**两阶段精调**：先按初表生成，渲染后建立校正表（以对象名为键），
逐个修正 `shape.left/top/width/height` 与字号。

```python
text_adjustments = {
    "main_title": {"x": ..., "y": ..., "w": ..., "h": ..., "font_size": ...},
}
```

重点校正：主标题、三个模块标题、流程节点标签、左侧方法卡片文字、
右侧循环节点文字、右侧观测项文字、底部卡片文字、模块下方说明文字。
**不得靠整体移动页面来修文字误差。**

### 阶段 12 — 渲染

LibreOffice 必须用独立用户目录，否则会因配置锁以退出码 77 失败：

```bash
libreoffice -env:UserInstallation=file:///tmp/lo_profile_project \
  --headless --convert-to pdf --outdir preview ppt/editable_reproduction.pptx
pdftoppm -png -singlefile -r 150 preview/editable_reproduction.pdf preview/ppt_render
```

然后把渲染图调整到参考图的精确像素尺寸（**不裁剪、不加边距、不重新居中**）：

```python
ppt_render = Image.open(render_path).convert("RGB")
ppt_render = ppt_render.resize((REF_W, REF_H), Image.Resampling.LANCZOS)
```

### 阶段 13 — 生成三种对比文件

- `comparison.png` —— 左右并排（参考图 | PPT 渲染图）
- `overlay_comparison.png` —— 50% 透明叠加 `Image.blend(ref, ren, 0.5)`
- `difference_map.png` —— 像素差异，×2.5 放大

```python
difference = ImageChops.difference(reference_image, ppt_render_image)
```

**不得只生成对比图而不检查。**

### 阶段 14 — 占用率检测

```python
def content_bbox_from_image(image):
    arr = np.array(image.convert("RGB"))
    saturation = arr.max(axis=2) - arr.min(axis=2)
    mask = (((saturation > 35) & (arr.min(axis=2) < 245)) |
            ((arr[:,:,0] < 245) & (arr[:,:,1] < 245) & (arr[:,:,2] < 245)))
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return 0, 0, image.width, image.height
    return int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)
```

分别算参考图和渲染图的 `bbox_ratios` / `occupancy` / `bbox_center`。

**验收阈值**：

| 指标 | 阈值 |
|---|---|
| 页面宽高比误差 | 0 |
| 水平占用率误差 | ≤ 0.5% |
| 垂直占用率误差 | ≤ 0.5% |
| 内容中心 X 误差 | ≤ 0.3% |
| 内容中心 Y 误差 | ≤ 0.3% |
| 大型主框每条边误差 | 目标 ≤ 3–5 参考像素 |
| 对象越界数量 | 0 |
| 明显文字溢出数量 | 0 |
| Freeform 箭头数量 | 0 |
| 参考图背景数量 | 0 |
| 超大图标数量 | 0 |

这一步只验证全页范围，**不能替代主框体坐标检查**。

### 阶段 15 — 额外检查四个关键框体

顶部标题框、左侧主模块外框、右侧主模块外框、底部主模块外框。每个记录
`x / y / width / height / left_ratio / top_ratio / right_ratio / bottom_ratio /
center_x_ratio / center_y_ratio`。

参考图与 PPT 对应主框体每条边误差目标：**≤ 3–5 个参考像素**。

不得仅凭全页占用率通过就交付 —— 左右各放一个错误的小对象也可能让全页
占用率接近，但主体框体依然错误。

### 阶段 16 — 越界与媒体检查

```python
def find_out_of_bounds(slide, presentation):
    warnings = []
    for shape in slide.shapes:
        if (shape.left < 0 or shape.top < 0 or
                shape.left + shape.width > presentation.slide_width or
                shape.top + shape.height > presentation.slide_height):
            warnings.append(shape.name)
    return warnings
```

发现越界只调整对应对象，**禁止全选后整体缩小**。

PPTX 是 ZIP，用 `zipfile` 检查 `ppt/media/`：只应存在必要的透明图标。
不得存在参考图、渲染图、对比图、模块截图、4096×4096 PNG 或未使用的大型图片。
单页 PPTX 建议 0.1–2 MB。

### 阶段 17 — 对象命名

所有重要对象必须命名，便于两阶段文字精调按名查找（相同文字可能重复出现）：

```
title_frame / title_icon / title_text
left_main_panel / left_header / left_header_icon / left_header_text
right_main_panel / right_header / right_header_icon / right_header_text
bottom_main_panel / bottom_header / bottom_header_text
process_circle_01 / process_icon_01 / process_label_01
observation_card_01 / observation_icon_01 / observation_text_01
connector_top_left / connector_top_right / connector_center_bidirectional
```

图标图片对象命名为 `icon_<asset_name>`。

## 禁止的错误实现

出现以下任何一种即判定失败：

1. 参考图被设为页面背景
2. 页面中存在隐藏参考图
3. 页面由一张整页截图构成
4. 大模块由截图构成
5. 整体设计被缩小后放在页面中
6. 页面右侧三分之一空白
7. 页面底部存在多余空白
8. 页面内容整体偏左或偏上
9. PPT 页面比例与参考图不一致
10. 用自动平均分布替代原图位置
11. 使用 PowerPoint 自动布局
12. 用统一宽度替代不同卡片宽度
13. 用统一默认圆角
14. 文字仅粗略居中，没有二次校正
15. 图标从截图中裁切
16. 图标存在缺笔或断线
17. 图标 PNG 包含矩形背景
18. 图标被拉伸
19. 箭头为 Freeform
20. 箭头由多段线拼接
21. 箭头为 PNG 或 SVG 图片
22. 对象超出页面
23. 文本溢出
24. PPTX 包含超大媒体
25. 没有实际渲染 PPT
26. 渲染图未调整为参考图精确尺寸
27. 没有生成叠加图
28. 没有检查整体占用率
29. 没有检查四个主框体
30. 一轮生成后直接交付

## 验收阈值

必须全部达到：

| 指标 | 阈值 |
|---|---|
| 页面宽高比误差 | 0 |
| 水平占用率误差 | ≤ 0.5% |
| 垂直占用率误差 | ≤ 0.5% |
| 内容中心 X 误差 | ≤ 0.3% |
| 内容中心 Y 误差 | ≤ 0.3% |
| 大型主框每条边误差 | 目标 ≤ 3–5 个参考像素 |
| 对象越界数量 | 0 |
| 明显文字溢出数量 | 0 |
| Freeform 箭头数量 | 0 |
| 参考图背景数量 | 0 |
| 超大图标数量 | 0 |

图标属于重新绘制对象，允许因原始截图分辨率产生细节推测。
但图标必须**完整、清晰、无缺笔、无背景污染**。

单页 PPTX 建议控制在 **0.1 MB – 2 MB**。图标较多时可以略高，但不得因为小图标达到几十 MB。

---

## 执行清单（26 步）

1. 读取原始像素尺寸
2. 创建相同比例的 PPT 页面
3. 建立参考像素到 PPT 的直接映射
4. 建立 scene_spec 对象表
5. 测量四个主要框体
6. 测量全部子框体
7. 建立文字对象表
8. 建立图标目标可见边界表
9. 建立箭头对象表
10. 重绘或复用已批准的 SVG 图标
11. 将 SVG 渲染为 128×128 PNG
12. 计算图标 Alpha 边界
13. 按图层顺序生成 PPT 原生对象
14. 保存第一版 PPTX
15. 使用独立 LibreOffice 用户目录渲染
16. 生成 comparison、overlay 和 difference map
17. 建立文字及图标位置校正表
18. 修改第二版
19. 重新渲染
20. 检查全画布占用率和内容中心
21. 检查四个主要框体
22. 检查越界和文字溢出
23. 检查 PPTX 内部媒体
24. 生成最终版 PPTX
25. 打包工程文件
26. 提供真实下载链接

---

## 脚本用法

本 Skill 附带 5 个脚本，可直接用于真实任务：

```bash
# 1. 校验 scene_spec
python3 scripts/validate_spec.py scene_spec.json --ref source/reference_image.png

# 2. 生成 PPT + 渲染 + 三种对比图 + report.json
python3 scripts/build_editable_ppt.py \
    --reference source/reference_image.png \
    --spec scene_spec.json \
    --out ppt --render preview --icons icons

# 3. 重绘图标 SVG
python3 scripts/redraw_icon.py --kind trophy \
    --out icons/svg/trophy_blue.svg --color "#1B7FBF"

# 4. 生成 manifest.txt
python3 scripts/make_manifest.py --project . --reference source/reference_image.png

# 5. 打包（工程 ZIP + 图标 ZIP + PPTX）
python3 scripts/package_outputs.py --project . --out /mnt/data
```

自测（会真实渲染并校验全部阈值）：

```bash
python3 scripts/selftest.py
```

## 交付物

1. 可编辑 PPTX
2. 完整工程 ZIP
3. 图标素材 ZIP
4. 每个图标的 SVG
5. 每个图标的 128×128 透明 PNG
6. PPT 渲染图
7. 参考图与 PPT 的并排对比图
8. 参考图与 PPT 的透明叠加图
9. 像素差异图
10. 图标总览图
11. manifest.txt

## manifest.txt 内容

Project name / Reference filename / Reference pixel size / Reference ratio /
Slide size in inches / Slide ratio / Slide count / Full-canvas mapping used /
Contain or fit-inside used / Extra global padding used / Reference content bbox
ratios / PPT render content bbox ratios / Reference horizontal occupancy /
PPT render horizontal occupancy / Reference vertical occupancy / PPT render
vertical occupancy / Reference content center / PPT render content center /
Title frame reference coordinates / Left main frame reference coordinates /
Right main frame reference coordinates / Bottom main frame reference coordinates /
SVG icon count / 128 PNG icon count / PNG color mode / Icons redrawn or cropped /
Icon insertion strategy / Native connector types used / Freeform arrows used /
Reference image used as background / Out-of-bounds warning count / Text overflow
warning count / PPTX file size / PPT render generated / Comparison generated /
Overlay generated / Difference map generated / Known font rendering differences /
Uncertain low-resolution icon details

## 最终回复格式

必须明确报告：

```
PPT 页数：
参考图尺寸：
PPT 页面尺寸：
页面比例：
重绘图标数量：
SVG 数量：
128×128 PNG 数量：
PPT 中图标格式：
原生箭头类型：
参考图水平占用率：
PPT 水平占用率：
参考图垂直占用率：
PPT 垂直占用率：
参考图内容中心：
PPT 内容中心：
对象越界数量：
文字溢出数量：
Freeform 箭头数量：
是否嵌入参考图：
PPTX 文件大小：
```

然后提供三个真实下载链接：工程 ZIP、可编辑 PPTX、图标素材 ZIP。

**不得只回复"已完成"。不得在实际文件没有生成时伪造下载链接。**
