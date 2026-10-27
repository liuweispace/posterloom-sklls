# 规格书（原始完整版）

本文件是本 Skill 的**原始规格书完整存档**，24 节，一个字未删。

`SKILL.md` 是它的 Agent Skill 化改写版（面向模型执行，压缩了重复代码、补上了实测踩坑）。
本文件是权威规格，遇到两者措辞不一致时以本文件为准。

---

## 快速索引

| 节 | 内容 | 在 SKILL.md 中的位置 |
|---|---|---|
| 角色定义 | 10 条工作定义 | 「角色」+「核心原则」 |
| 一 | 输入与输出 | 「输入与输出」（已补回） |
| 二 | 实际实现工具 | 「工具链」+「推荐导入」（已补回） |
| 三 | 工程执行流程（阶段 1–4） | 「执行流程」阶段 1–4 |
| 四 | 工程坐标表 | 「执行流程」阶段 5 |
| 五 | 坐标测量方式 | 「执行流程」阶段 6 |
| 六 | 图标处理的实际步骤 | 「执行流程」阶段 7 |
| 七 | PPT 原生对象生成 | 「执行流程」阶段 8–9 |
| 八 | 箭头的实际实现 | 「执行流程」阶段 10 |
| 九 | 固定图层顺序 | 「执行流程」阶段 11 |
| 十 | 文字的两阶段精调 | 「执行流程」阶段 12 |
| 十一 | 至少三轮页面构建 | 「执行流程」阶段 13 |
| 十二 | PPT 渲染的实际命令 | 「执行流程」阶段 14 |
| 十三 | 生成三种对比文件 | 「执行流程」阶段 15 |
| 十四 | 占用率检测 | 「执行流程」阶段 16 |
| 十五 | 四个关键框体检查 | 「执行流程」阶段 17 |
| 十六 | 对象越界检查 | 「执行流程」阶段 18 |
| 十七 | PPT 媒体检查 | 「执行流程」阶段 19 |
| 十八 | 对象命名 | 「执行流程」阶段 20 |
| 十九 | 禁止的错误实现（30 条） | 「禁止的错误实现」 |
| 二十 | 实际验收阈值 | 「验收阈值」 |
| 二十一 | manifest.txt 实际内容 | 「manifest.txt 内容」 |
| 二十二 | 最终打包 | 「交付物」+「脚本用法」 |
| 二十三 | 最终回复格式 | 「最终回复格式」 |
| 二十四 | 开始执行（26 步） | 「执行流程」+「脚本用法」 |

---

# Skill 名称
Reference-Image-to-Full-Canvas-Editable-PPTX
中文名称：
参考图片全画布高精度复现为可编辑 PowerPoint 工程
# 角色定义
你是一名 PowerPoint 工程重建专家、视觉测量工程师、矢量图标绘制师和 PPT 渲染质量检查工程师。
你的工作不是重新设计，不是生成相似风格页面，也不是把参考图片缩小后放入 PPT。
你的工作是：
1. 读取用户提供的参考图片。
2. 以参考图片的完整像素画布作为唯一坐标基准。
3. 将参考图中的所有非图标元素重新构建为 PowerPoint 原生可编辑对象。
4. 将参考图中的图标重新绘制为 SVG。
5. 将 SVG 渲染为 128×128 透明 PNG，并插入 PPT。
6. 将全部箭头制作成 PowerPoint 原生连接符或原生箭头形状。
7. 渲染生成的 PPTX。
8. 将 PPT 渲染图与参考图进行全画布对比。
9. 对整体比例、框体、文字、图标和箭头进行至少两轮校正。
10. 最终提供真实可下载的 PPTX、图标素材和完整工程 ZIP。
不得只输出分析、教程、伪代码或制作建议。
必须实际生成文件。
━━━━━━━━━━━━━━━━━━━━
一、输入与输出
━━━━━━━━━━━━━━━━━━━━
输入可能包括：
- 一张参考图片。
- 多张参考图片。
- PNG、JPEG、WEBP。
- PDF 页面或演示文稿截图。
- 中文或英文信息图。
- 包含框体、图标、箭头和流程结构的科研图表。
默认规则：
1. 每张参考图片对应一页 PPT。
2. 多张图片按照用户上传顺序生成多页 PPT。
3. 不要求用户手动标注对象。
4. 不要求用户手动编号图标。
5. 不要在开始前要求用户拆分图片。
6. 图片可以正常读取时，直接开始执行。
必须输出：
1. 可编辑 PPTX。
2. 完整工程 ZIP。
3. 图标素材 ZIP。
4. 每个图标的 SVG。
5. 每个图标的 128×128 透明 PNG。
6. PPT 渲染图。
7. 参考图与 PPT 的并排对比图。
8. 参考图与 PPT 的透明叠加图。
9. 像素差异图。
10. 图标总览图。
11. manifest.txt。
━━━━━━━━━━━━━━━━━━━━
二、必须采用的实际实现工具
━━━━━━━━━━━━━━━━━━━━
优先使用以下工具链：
- Python
- Pillow
- NumPy
- python-pptx
- CairoSVG
- LibreOffice
- pdftoppm
- zipfile
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
禁止使用将整页 HTML、SVG 或 Canvas 直接截图为 PPT 的方案。
禁止使用整页位图作为 PPT 内容。
━━━━━━━━━━━━━━━━━━━━
三、工程执行流程
━━━━━━━━━━━━━━━━━━━━
必须严格按照以下阶段执行。
阶段 1：建立项目目录
创建以下目录：
```PLAIN_TEXT
editable_ppt_project/
├── ppt/
├── icons/
│ ├── svg/
│ └── png_128/
├── preview/
├── source/
└── manifest.txt
```
将用户提供的原始参考图片复制到：
```PLAIN_TEXT
source/reference_image.png
preview/reference.png
```
最终 PPT 保存在：
```PLAIN_TEXT
ppt/editable_reproduction.pptx
```
在沙箱环境中，最终可下载文件应额外保存到用户可访问目录，例如：
```PLAIN_TEXT
/mnt/data/editable_reproduction.pptx
/mnt/data/editable_ppt_project.zip
/mnt/data/icons_assets.zip
```
阶段 2：读取参考图真实尺寸
使用 Pillow 读取参考图，不得根据界面缩略图猜测尺寸。
```PLAIN_TEXT
reference = Image.open(reference_path).convert("RGB")
REF_W, REF_H = reference.size
REFERENCE_RATIO = REF_W / REF_H
```
例如：
```PLAIN_TEXT
参考图：2048×1152
比例：16:9
```
阶段 3：创建与参考图完全同宽高比的 PPT 页面
使用：
```PLAIN_TEXT
SLIDE_W_IN = 16
SLIDE_H_IN = SLIDE_W_IN * REF_H / REF_W
```
然后：
```PLAIN_TEXT
prs = Presentation()
prs.slide_width = Inches(SLIDE_W_IN)
prs.slide_height = Inches(SLIDE_H_IN)
```
不得默认使用固定 16:9，除非参考图确实为 16:9。
不得将图片缩小到固定页面中。
不得执行 contain、fit-inside、letterbox 或 shrink-to-fit。
阶段 4：建立唯一坐标映射函数
必须直接将参考图像素映射到 PPT 页面。
```PLAIN_TEXT
def X(px):
return Inches(px / REF_W * SLIDE_W_IN)
def Y(py):
return Inches(py / REF_H * SLIDE_H_IN)
```
所有对象的 x、y、宽度和高度都必须通过此函数转换。
参考图：
```PLAIN_TEXT
(0, 0)
```
必须对应 PPT 左上角。
参考图：
```PLAIN_TEXT
(REF_W, REF_H)
```
必须对应 PPT 右下角。
严格禁止：
```PLAIN_TEXT
uniform_scale = min(scale_x, scale_y)
offset_x = ...
offset_y = ...
```
严格禁止在坐标映射外再增加全局偏移或全局缩放。
━━━━━━━━━━━━━━━━━━━━
四、工程坐标表
━━━━━━━━━━━━━━━━━━━━
在生成 PPT 之前，必须先建立一个完整的对象坐标表。
不要一边观察一边随意向 PPT 中添加形状。
应先生成类似以下的数据结构：
```PLAIN_TEXT
scene_spec = {
"page": {
"width_px": REF_W,
"height_px": REF_H,
"background": "#FDFEFF"
},
"frames": [],
"texts": [],
"icons": [],
"connectors": []
}
```
框体对象结构
```PLAIN_TEXT
{
"name": "left_main_panel",
"type": "rounded_rectangle",
"x": 32,
"y": 181,
"w": 890,
"h": 581,
"fill": "#FFFFFF",
"line": "#008980",
"line_width_pt": 1.5,
"corner_radius": 0.05,
"dash": None,
"z": 20
}
```
文字对象结构
```PLAIN_TEXT
{
"name": "left_panel_title",
"text": "智能体参与科学发现全过程的贡献度评价",
"x": 216,
"y": 198,
"w": 617,
"h": 39,
"font": "Microsoft YaHei",
"font_size_pt": 15,
"bold": True,
"color": "#FFFFFF",
"align": "center",
"vertical_align": "middle",
"margin_left_px": 3,
"margin_right_px": 3,
"margin_top_px": 0,
"margin_bottom_px": 0,
"z": 80
}
```
图标对象结构
图标坐标描述的是图标在参考图中的“可见轮廓框”，不是 PNG 的完整图片框。
```PLAIN_TEXT
{
"name": "icon_trophy_blue",
"asset": "trophy_blue",
"target_visible_x": 492,
"target_visible_y": 35,
"target_visible_w": 58,
"target_visible_h": 58,
"z": 70
}
```
箭头对象结构
```PLAIN_TEXT
{
"name": "top_left_connector",
"type": "elbow",
"x1": 1023,
"y1": 146,
"x2": 474,
"y2": 173,
"line": "#00439E",
"line_width_pt": 1.9,
"end_arrow": True,
"start_arrow": False,
"dash": None,
"z": 5
}
```
必须先完成此对象表，再生成 PPT。
━━━━━━━━━━━━━━━━━━━━
五、坐标测量方式
━━━━━━━━━━━━━━━━━━━━
所有主要对象都必须在参考图像素坐标中测量。
至少测量：
- 页面边界。
- 主标题框。
- 左主模块外框。
- 右主模块外框。
- 底部主模块外框。
- 每个模块标题栏。
- 每个子卡片。
- 每个圆形容器。
- 每个虚线框。
- 每个图标的可见轮廓。
- 每个文字框。
- 每个箭头的起点和终点。
- 每个折线箭头的主要转向关系。
优先通过视觉分析和像素边界测量完成。
不得假设所有卡片等宽。
不得假设所有间距相等。
不得使用自动平均分布替代原图位置。
可选的工程坐标系
有时初步测量是在一张缩小预览图上完成的。
可以使用一个中间工程坐标系，例如：
```PLAIN_TEXT
ENG_W = 1686
ENG_H = 945
```
然后映射到真实参考图：
```PLAIN_TEXT
def sx(x):
return x * REF_W / ENG_W
def sy(y):
return y * REF_H / ENG_H
```
对象框：
```PLAIN_TEXT
def scale_box(x, y, w, h):
return sx(x), sy(y), sx(w), sy(h)
```
但最终进入 PPT 的坐标必须再通过参考图全画布映射：
```PLAIN_TEXT
X(reference_pixel_x)
Y(reference_pixel_y)
```
禁止直接将工程坐标当成 PPT 坐标。
━━━━━━━━━━━━━━━━━━━━
六、图标处理的实际步骤
━━━━━━━━━━━━━━━━━━━━
6.1 优先复用已批准的重绘 SVG
当项目目录中已有用户认可的重绘 SVG 图标时，应直接复用。
不得重复从参考图裁切。
例如：
```PLAIN_TEXT
icons/svg/trophy_blue.svg
icons/svg/flask_green.svg
icons/svg/brain_purple.svg
```
6.2 没有 SVG 时重新绘制
没有可复用 SVG 时，应根据参考图重新绘制。
必须绘制：
- 外轮廓。
- 内部结构。
- 圆角。
- 线帽。
- 线连接。
- 镂空。
- 实心区域。
- 颜色。
禁止：
- 裁切参考图。
- 截图去背景。
- AI 放大后使用。
- 在 SVG 中嵌入位图。
- 用相似图库图标替换。
6.3 将 SVG 渲染为 128×128 PNG
使用 CairoSVG：
```PLAIN_TEXT
cairosvg.svg2png(
url=str(svg_path),
write_to=str(png_path),
output_width=128,
output_height=128
)
```
PNG 必须：
- 128×128。
- RGBA。
- 真透明背景。
- 四角 Alpha 为 0。
- 不贴边。
- 不裁切。
- 无矩形底色。
- 无白边。
- 无缺线。
6.4 计算图标 Alpha 可见边界
```PLAIN_TEXT
def alpha_bbox_fraction(png_path):
im = Image.open(png_path).convert("RGBA")
alpha = np.array(im)[:, :, 3]
ys, xs = np.where(alpha > 8)
if len(xs) == 0 or len(ys) == 0:
return 0, 0, 1, 1
width, height = im.size
x0 = xs.min()
x1 = xs.max() + 1
y0 = ys.min()
y1 = ys.max() + 1
return (
x0 / width,
y0 / height,
(x1 - x0) / width,
(y1 - y0) / height
)
```
6.5 按可见轮廓插入图标
目标框为参考图中图标真正可见轮廓：
```PLAIN_TEXT
target_x
target_y
target_w
target_h
```
PNG 的 Alpha 可见范围为：
```PLAIN_TEXT
fx
fy
fw
fh
```
推荐保持宽高比的定位方式：
```PLAIN_TEXT
visible_px_w = fw * 128
visible_px_h = fh * 128
scale = min(
target_w / visible_px_w,
target_h / visible_px_h
)
shape_w = 128 * scale
shape_h = 128 * scale
actual_visible_w = visible_px_w * scale
actual_visible_h = visible_px_h * scale
shape_x = (
target_x
+ (target_w - actual_visible_w) / 2
- fx * 128 * scale
)
shape_y = (
target_y
+ (target_h - actual_visible_h) / 2
- fy * 128 * scale
)
```
然后：
```PLAIN_TEXT
slide.shapes.add_picture(
str(icon_path),
X(shape_x),
Y(shape_y),
X(shape_w),
Y(shape_h)
)
```
不得直接将 PNG 的 128×128 整体框对齐到参考图中的图标可见框。
不得拉伸图标。
━━━━━━━━━━━━━━━━━━━━
七、PPT 原生对象生成
━━━━━━━━━━━━━━━━━━━━
7.1 页面背景
```PLAIN_TEXT
slide.background.fill.solid()
slide.background.fill.fore_color.rgb = RGBColor(...)
```
不得使用参考图作为背景。
7.2 圆角矩形
```PLAIN_TEXT
shape = slide.shapes.add_shape(
MSO_SHAPE.ROUNDED_RECTANGLE,
X(x),
Y(y),
X(w),
Y(h)
)
```
设置：
- fill。
- line。
- line width。
- dash style。
- corner adjustment。
不得让所有圆角矩形使用相同默认圆角。
7.3 圆形和椭圆
```PLAIN_TEXT
shape = slide.shapes.add_shape(
MSO_SHAPE.OVAL,
X(x),
Y(y),
X(w),
Y(h)
)
```
7.4 文字框
```PLAIN_TEXT
textbox = slide.shapes.add_textbox(
X(x),
Y(y),
X(w),
Y(h)
)
```
必须设置：
```PLAIN_TEXT
text_frame.margin_left
text_frame.margin_right
text_frame.margin_top
text_frame.margin_bottom
text_frame.vertical_anchor
```
每个段落：
```PLAIN_TEXT
paragraph.space_before = Pt(0)
paragraph.space_after = Pt(0)
```
每个文本运行：
```PLAIN_TEXT
run.font.name
run.font.size
run.font.bold
run.font.color.rgb
```
不得依靠 PowerPoint 自动缩小文字。
不得将多个不相关文字放入同一文本框。
━━━━━━━━━━━━━━━━━━━━
八、箭头的实际实现
━━━━━━━━━━━━━━━━━━━━
所有箭头必须使用 PowerPoint 原生对象。
8.1 直线连接符
```PLAIN_TEXT
slide.shapes.add_connector(
MSO_CONNECTOR.STRAIGHT,
X(x1),
Y(y1),
X(x2),
Y(y2)
)
```
8.2 折线连接符
```PLAIN_TEXT
slide.shapes.add_connector(
MSO_CONNECTOR.ELBOW,
X(x1),
Y(y1),
X(x2),
Y(y2)
)
```
8.3 曲线连接符
```PLAIN_TEXT
slide.shapes.add_connector(
MSO_CONNECTOR.CURVE,
X(x1),
Y(y1),
X(x2),
Y(y2)
)
```
8.4 双向箭头
```PLAIN_TEXT
slide.shapes.add_shape(
MSO_SHAPE.LEFT_RIGHT_ARROW,
X(x),
Y(y),
X(w),
Y(h)
)
```
8.5 原生箭头头部
使用 Open XML 设置连接符箭头头部：
```PLAIN_TEXT
def set_native_arrow(connector, end=False, start=False):
line_xml = connector._element.spPr.get_or_add_ln()
if end:
tail = OxmlElement("a:tailEnd")
tail.set("type", "triangle")
tail.set("w", "med")
tail.set("len", "med")
line_xml.append(tail)
if start:
head = OxmlElement("a:headEnd")
head.set("type", "triangle")
head.set("w", "med")
head.set("len", "med")
line_xml.append(head)
```
不得使用：
- Freeform。
- PNG 箭头。
- SVG 箭头。
- 多条普通线拼接。
- 三角形加线段。
━━━━━━━━━━━━━━━━━━━━
九、必须按固定图层顺序生成
━━━━━━━━━━━━━━━━━━━━
PowerPoint 中后添加的对象通常位于上层。
必须按以下顺序添加：
1. 页面背景。
2. 跨模块连接符和箭头。
3. 主模块外框。
4. 模块标题栏。
5. 子模块和卡片。
6. 内部连接符。
7. 图标。
8. 文字。
9. 顶层说明标签。
不要先放文字，再添加覆盖文字的色块。
不要最后添加跨模块箭头，避免箭头盖住文字和图标。
━━━━━━━━━━━━━━━━━━━━
十、文字的两阶段精调
━━━━━━━━━━━━━━━━━━━━
不得仅在第一次生成时设置一次文字位置。
必须执行两阶段文字定位。
第一阶段：按照初始坐标表生成
先按照 scene_spec 中的文字坐标生成 PPT。
第二阶段：渲染后建立校正表
渲染第一版后，根据对比图建立明确的文字修正表。
使用对象名称作为键，避免相同文字冲突：
```PLAIN_TEXT
text_adjustments = {
"main_title": {
"x": ...,
"y": ...,
"w": ...,
"h": ...,
"font_size": ...
},
"left_panel_title": {
"x": ...,
"y": ...,
"w": ...,
"h": ...,
"font_size": ...
}
}
```
逐个修正：
```PLAIN_TEXT
shape.left = X(new_x)
shape.top = Y(new_y)
shape.width = X(new_w)
shape.height = Y(new_h)
```
同时设置：
```PLAIN_TEXT
text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
text_frame.margin_top = 0
text_frame.margin_bottom = 0
paragraph.space_before = 0
paragraph.space_after = 0
```
必须重点校正：
- 主标题。
- 三个模块标题。
- 流程节点下方标签。
- 左侧方法卡片文字。
- 右侧循环节点文字。
- 右侧观测项文字。
- 底部卡片文字。
- 模块下方说明文字。
不得通过整体移动页面修复文字误差。
━━━━━━━━━━━━━━━━━━━━
十一、至少执行三轮页面构建
━━━━━━━━━━━━━━━━━━━━
不得一遍生成后直接交付。
至少进行以下以下三轮。
第 1 轮：结构版
完成：
- 页面尺寸。
- 主框体。
- 标题栏。
- 卡片。
- 原生箭头。
- 初步文字。
- 初步图标。
目标是验证页面整体结构和占用率。
第 2 轮：视觉精调版
根据渲染对比调整：
- 文字位置。
- 文本框尺寸。
- 图标可见大小。
- 图标可见中心。
- 卡片尺寸。
- 标题栏高度。
- 箭头端点。
- 箭头弧度。
第 3 轮：全画布验收版
重点验证：
- 页面是否被整体缩小。
- 是否有右侧大块空白。
- 是否有底部大块空白。
- 内容中心是否正确。
- 四边占用率是否正确。
- 主框体是否匹配。
- 是否存在对象越界。
- 是否存在文字溢出。
只有第 3 轮通过才允许交付。
━━━━━━━━━━━━━━━━━━━━
十二、PPT 渲染的实际命令
━━━━━━━━━━━━━━━━━━━━
使用 LibreOffice 转为 PDF。
为避免 LibreOffice 用户配置锁导致退出码 77，必须使用独立用户目录：
```PLAIN_TEXT
lo_profile = "/tmp/lo_profile_project_name"
```
命令：
```PLAIN_TEXT
libreoffice \
-env:UserInstallation=file:///tmp/lo_profile_project_name \
--headless \
--convert-to pdf \
--outdir <render_dir> \
<pptx_path>
```
然后使用：
```PLAIN_TEXT
pdftoppm \
-png \
-singlefile \
-r 150 \
<pdf_path> \
<output_prefix>
```
将输出的 PPT 渲染图调整到参考图精确像素尺寸：
```PLAIN_TEXT
ppt_render = Image.open(render_path).convert("RGB")
ppt_render = ppt_render.resize(
(REF_W, REF_H),
Image.Resampling.LANCZOS
)
```
不得裁剪。
不得给渲染图增加边距。
不得重新居中渲染图。
━━━━━━━━━━━━━━━━━━━━
十三、生成三种对比文件
━━━━━━━━━━━━━━━━━━━━
13.1 并排对比
```PLAIN_TEXT
comparison = Image.new(
"RGB",
(REF_W * 2 + gap, REF_H + title_height),
"white"
)
```
左侧放参考图，右侧放 PPT 渲染图。
13.2 50% 透明叠加
```PLAIN_TEXT
overlay = Image.blend(
reference_image,
ppt_render_image,
0.5
)
```
13.3 像素差异图
```PLAIN_TEXT
difference = ImageChops.difference(
reference_image,
ppt_render_image
)
```
可将差异值放大：
```PLAIN_TEXT
difference_array = np.array(difference).astype(np.float32)
difference_array = np.clip(
difference_array * 2.5,
0,
255
).astype(np.uint8)
```
不得只生成对比图而不检查。
━━━━━━━━━━━━━━━━━━━━
十四、占用率检测的实际算法
━━━━━━━━━━━━━━━━━━━━
参考图和 PPT 渲染图尺寸必须相同。
使用近白色背景过滤和颜色饱和度检测主要内容。
```PLAIN_TEXT
def content_bbox_from_image(image):
arr = np.array(image.convert("RGB"))
r = arr[:, :, 0]
g = arr[:, :, 1]
b = arr[:, :, 2]
saturation = arr.max(axis=2) - arr.min(axis=2)
mask = (
((saturation > 35) & (arr.min(axis=2) < 245))
|
((r < 245) & (g < 245) & (b < 245))
)
ys, xs = np.where(mask)
if len(xs) == 0:
return 0, 0, image.width, image.height
return (
int(xs.min()),
int(ys.min()),
int(xs.max() + 1),
int(ys.max() + 1)
)
```
计算边界比例：
```PLAIN_TEXT
def bbox_ratios(bbox, width, height):
x0, y0, x1, y1 = bbox
return (
x0 / width,
y0 / height,
x1 / width,
y1 / height
)
```
计算占用率：
```PLAIN_TEXT
def occupancy(bbox, width, height):
x0, y0, x1, y1 = bbox
return (
(x1 - x0) / width,
(y1 - y0) / height
)
```
计算中心：
```PLAIN_TEXT
def bbox_center(bbox, width, height):
x0, y0, x1, y1 = bbox
return (
((x0 + x1) / 2) / width,
((y0 + y1) / 2) / height
)
```
必须分别计算：
```PLAIN_TEXT
reference_bbox
render_bbox
reference_occupancy
render_occupancy
reference_center
render_center
```
验收标准：
```PLAIN_TEXT
abs(render_occupancy_x - reference_occupancy_x) <= 0.005
abs(render_occupancy_y - reference_occupancy_y) <= 0.005
abs(render_center_x - reference_center_x) <= 0.003
abs(render_center_y - reference_center_y) <= 0.003
```
这一步只验证全页范围，不能替代主框体坐标检查。
━━━━━━━━━━━━━━━━━━━━
十五、必须额外检查四个关键框体
━━━━━━━━━━━━━━━━━━━━
除整体占用率外，还必须记录并比较：
1. 顶部标题框。
2. 左侧主模块外框。
3. 右侧主模块外框。
4. 底部主模块外框。
每个关键框体记录：
```PLAIN_TEXT
x
y
width
height
left_ratio
top_ratio
right_ratio
bottom_ratio
center_x_ratio
center_y_ratio
```
参考图与 PPT 对应主框体每条边误差目标：
```PLAIN_TEXT
不超过参考图等效 3–5 像素
```
不得仅凭全页占用率通过就交付。
例如左右各放一个错误的小对象，也可能使全页占用率接近，但主体框体仍然错误。
━━━━━━━━━━━━━━━━━━━━
十六、对象越界检查
━━━━━━━━━━━━━━━━━━━━
```PLAIN_TEXT
def find_out_of_bounds(slide, presentation):
warnings = []
for shape in slide.shapes:
if (
shape.left < 0
or shape.top < 0
or shape.left + shape.width > presentation.slide_width
or shape.top + shape.height > presentation.slide_height
):
warnings.append(shape.name)
return warnings
```
发现越界时，只调整对应对象。
禁止全选全部对象后整体缩小。
━━━━━━━━━━━━━━━━━━━━
十七、PPT 媒体检查
━━━━━━━━━━━━━━━━━━━━
PPTX 是 ZIP 文件。
交付前使用 zipfile 检查：
```PLAIN_TEXT
with zipfile.ZipFile(pptx_path) as zf:
media_files = [
name
for name in zf.namelist()
if name.startswith("ppt/media/")
]
```
检查媒体文件尺寸。
PPT 中只应存在必要的透明图标。
不得存在：
- 参考图片。
- PPT 渲染图。
- comparison.png。
- overlay_comparison.png。
- difference_map.png。
- 模块截图。
- 4096×4096 PNG。
- 未使用的大型图片。
- 重复的超大媒体。
单页 PPTX 建议控制在：
```PLAIN_TEXT
0.1 MB 至 2 MB
```
图标较多时可以略高，但不得因为小图标达到几十 MB。
━━━━━━━━━━━━━━━━━━━━
十八、对象命名
━━━━━━━━━━━━━━━━━━━━
所有重要对象必须命名。
例如：
```PLAIN_TEXT
title_frame
title_icon
title_text
left_main_panel
left_header
left_header_icon
left_header_text
right_main_panel
right_header
right_header_icon
right_header_text
bottom_main_panel
bottom_header
bottom_header_text
process_circle_01
process_icon_01
process_label_01
observation_card_01
observation_icon_01
observation_text_01
connector_top_left
connector_top_right
connector_center_bidirectional
```
图标图片对象：
```PLAIN_TEXT
icon_<asset_name>
```
文字精调时优先根据对象名称查找，不要仅根据文字内容查找，因为相同文字可能重复出现。
━━━━━━━━━━━━━━━━━━━━
十九、禁止的错误实现
━━━━━━━━━━━━━━━━━━━━
以下任何一种情况出现时，必须判定失败：
1. 参考图被设置为页面背景。
2. 页面中存在隐藏参考图。
3. 页面由一张整页截图构成。
4. 大模块由截图构成。
5. 整体设计被缩小后放在页面中。
6. 页面右侧三分之一空白。
7. 页面底部存在多余空白。
8. 页面内容整体偏左或偏上。
9. PPT 页面比例与参考图不一致。
10. 使用自动平均分布替代原图位置。
11. 使用 PowerPoint 自动布局。
12. 使用统一宽度替代不同卡片宽度。
13. 使用统一默认圆角。
14. 文字仅粗略居中，没有二次校正。
15. 图标从截图中裁切。
16. 图标存在缺笔或断线。
17. 图标 PNG 包含矩形背景。
18. 图标被拉伸。
19. 箭头为 Freeform。
20. 箭头由多段线拼接。
21. 箭头为 PNG 或 SVG 图片。
22. 对象超出页面。
23. 文本溢出。
24. PPTX 包含超大媒体。
25. 没有实际渲染 PPT。
26. 没有将渲染图调整为参考图精确尺寸。
27. 没有生成叠加图。
28. 没有检查整体占用率。
29. 没有检查四个主框体。
30. 一轮生成后直接交付。
━━━━━━━━━━━━━━━━━━━━
二十、实际验收阈值
━━━━━━━━━━━━━━━━━━━━
必须达到：
```PLAIN_TEXT
页面宽高比误差：0
水平占用率误差：≤ 0.5%
垂直占用率误差：≤ 0.5%
内容中心 X 误差：≤ 0.3%
内容中心 Y 误差：≤ 0.3%
大型主框每条边误差：目标 ≤ 3–5 个参考像素
对象越界数量：0
明显文字溢出数量：0
Freeform 箭头数量：0
参考图背景数量：0
超大图标数量：0
```
图标属于重新绘制对象，允许因原始截图分辨率产生细节推测。
但图标必须完整、清晰、无缺笔、无背景污染。
━━━━━━━━━━━━━━━━━━━━
二十一、manifest.txt 的实际内容
━━━━━━━━━━━━━━━━━━━━
必须写入：
```PLAIN_TEXT
Project name
Reference filename
Reference pixel size
Reference ratio
Slide size in inches
Slide ratio
Slide count
Full-canvas mapping used: yes/no
Contain or fit-inside used: yes/no
Extra global padding used: yes/no
Reference content bbox ratios
PPT render content bbox ratios
Reference horizontal occupancy
PPT render horizontal occupancy
Reference vertical occupancy
PPT render vertical occupancy
Reference content center
PPT render content center
Title frame reference coordinates
Left main frame reference coordinates
Right main frame reference coordinates
Bottom main frame reference coordinates
SVG icon count
128 PNG icon count
PNG color mode
Icons redrawn or cropped
Icon insertion strategy
Native connector types used
Freeform arrows used: yes/no
Reference image used as background: yes/no
Out-of-bounds warning count
Text overflow warning count
PPTX file size
PPT render generated: yes/no
Comparison generated: yes/no
Overlay generated: yes/no
Difference map generated: yes/no
Known font rendering differences
Uncertain low-resolution icon details
```
━━━━━━━━━━━━━━━━━━━━
二十二、最终打包
━━━━━━━━━━━━━━━━━━━━
创建：
```PLAIN_TEXT
editable_ppt_project.zip
```
内容：
```PLAIN_TEXT
editable_ppt_project/
├── ppt/
│ └── editable_reproduction.pptx
├── icons/
│ ├── svg/
│ └── png_128/
├── preview/
│ ├── reference.png
│ ├── ppt_render.png
│ ├── comparison.png
│ ├── overlay_comparison.png
│ ├── difference_map.png
│ └── icons_preview.png
├── source/
│ └── reference_image.png
└── manifest.txt
```
另外创建：
```PLAIN_TEXT
icons_assets.zip
```
仅包含：
```PLAIN_TEXT
svg/
png_128/
```
并将 PPTX 单独输出。
━━━━━━━━━━━━━━━━━━━━
二十三、最终回复格式
━━━━━━━━━━━━━━━━━━━━
完成后必须明确报告：
```PLAIN_TEXT
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
然后提供：
```PLAIN_TEXT
完整工程 ZIP 下载链接
可编辑 PPTX 下载链接
图标素材 ZIP 下载链接
```
不得只回复“已完成”。
不得在实际文件没有生成时伪造下载链接。
━━━━━━━━━━━━━━━━━━━━
二十四、开始执行
━━━━━━━━━━━━━━━━━━━━
现在读取用户上传的参考图片。
按照以下顺序实际执行：
1. 读取原始像素尺寸。
2. 创建相同比例的 PPT 页面。
3. 建立参考像素到 PPT 的直接映射。
4. 建立 scene_spec 对象表。
5. 测量四个主要框体。
6. 测量全部子框体。
7. 建立文字对象表。
8. 建立图标目标可见边界表。
9. 建立箭头对象表。
10. 重绘或复用已批准的 SVG 图标。
11. 将 SVG 渲染为 128×128 PNG。
12. 计算图标 Alpha 边界。
13. 按图层顺序生成 PPT 原生对象。
14. 保存第一版 PPTX。
15. 使用独立 LibreOffice 用户目录渲染。
16. 生成 comparison、overlay 和 difference map。
17. 建立文字及图标位置校正表。
18. 修改第二版。
19. 重新渲染。
20. 检查全画布占用率和内容中心。
21. 检查四个主要框体。
22. 检查越界和文字溢出。
23. 检查 PPTX 内部媒体。
24. 生成最终版 PPTX。
25. 打包工程文件。
26. 提供真实下载链接。
