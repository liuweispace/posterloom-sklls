# 用户提示词模板

给用户直接复制使用的提示词。三个档位：最简、推荐、完整验收。

---

## 档位 A · 最简（大多数情况用这个）

```
用 reference-image-to-full-canvas-editable-pptx skill 处理这张参考图，
把它重建为可编辑的 PowerPoint。

要求：
- 参考图的完整像素画布作为唯一坐标基准，不要 contain、不要留白缩放
- 所有框体、文字、箭头用 PPT 原生对象重建，不要贴图
- 图标重绘为 SVG，渲染成 128×128 透明 PNG 后插入
- 渲染 PPT 并与参考图做全画布对比，至少校正两轮
- 最后给我可编辑 PPTX + 工程 ZIP + 图标素材 ZIP，并报告验收指标
```

---

## 档位 B · 推荐（附带具体验收要求）

```
用 reference-image-to-full-canvas-editable-pptx skill 把我上传的参考图重建为可编辑 PowerPoint。

工程要求：
1. 参考图尺寸由 Pillow 实测，不许按缩略图猜
2. PPT 页面比例必须与参考图完全一致，宽高比误差为 0
3. 所有对象坐标通过唯一映射函数 X()/Y() 从参考图像素换算，
   坐标映射之外不许再叠加任何全局偏移或缩放
4. 先写完整的 scene_spec 对象表（frames / texts / icons / connectors），
   校验通过后再生成 PPT
5. 图标重绘为 SVG（禁止裁切原图、禁止内嵌位图），
   转 128×128 RGBA 透明 PNG，按 Alpha 可见轮廓插入，不拉伸
6. 箭头全部用 PowerPoint 原生连接符 + Open XML 箭头头部，
   不许用 Freeform / PNG / SVG 箭头
7. 跨模块箭头画在框体之下，内部箭头画在卡片之上，文字永远在最上层
8. 至少三轮构建：结构版 → 视觉精调版 → 全画布验收版

验收要求：
- 渲染 PPT（LibreOffice + pdftoppm，用独立用户目录避免退出码 77）
- 生成并排对比图、50% 透明叠加图、像素差异图
- 水平/垂直占用率误差 ≤ 0.5%
- 内容中心 X/Y 误差 ≤ 0.3%
- 顶部标题框、左侧主模块、右侧主模块、底部主模块四个主框体
  每条边误差 ≤ 3–5 个参考像素
- 对象越界 0、文字溢出 0、Freeform 箭头 0、参考图背景 0
- 单页 PPTX 控制在 0.1–2 MB

交付：
- 可编辑 PPTX
- 完整工程 ZIP（含 icons/svg、icons/png_128、preview、manifest.txt）
- 图标素材 ZIP（仅 svg/ + png_128/）
- 每个图标单独提供 SVG 和 128×128 PNG
- manifest.txt 记录全部测量值与验收阈值
- 最终回复按 SKILL.md 的「最终回复格式」逐项报告 + 真实下载链接
```

---

## 档位 C · 多页 / 批量

```
用 reference-image-to-full-canvas-editable-pptx skill 处理我上传的 N 张参考图，
每张图对应一页 PPT，按上传顺序排页。

注意：
- 每页各自按自己的像素画布测量，页面比例可以互不相同
- 不要为了「看起来整齐」把不同比例的页强行统一成 16:9
- 图标资产可以在多页之间复用，同一 asset 只保留一份 SVG 和 PNG
- 一次生成一个多页 PPTX（每个页面尺寸相同时）或多个单页 PPTX（尺寸不同时）
  —— 尺寸不同时必须输出多个文件，并在 manifest 里说明原因
- 每页独立做三轮构建和全画布验收
```

---

## 常见追问与回答

**「它是不是就是把我图片贴进去了？」**
不是。PPTX 是 ZIP，可以自己验证：

```bash
unzip -l editable_reproduction.pptx | grep ppt/media/
```

只应看到图标 PNG，看不到参考图。也可以看 `manifest.txt` 里的
`Reference image used as background: no` 和 `Freeform arrows used: no`。

**「为什么和原图差一点？」**
看 `preview/difference_map.png` —— 亮的地方就是差异位置。文字边缘的轻微锯齿差异
是渲染器字体栅格化造成的，属于正常范围；结构性差异（框体错位、文字溢出）
才是要修的。

**「图标能改吗？」**
能。`icons/svg/*.svg` 是纯矢量文件，改完重新跑一次 build 即可。
`icons/png_128/*.png` 是从 SVG 渲染的，不用手动改。

**「能不能改字体？」**
改 `scene_spec` 里对应 text 对象的 `font` 和 `font_size_px`。
如果本机没有目标字体（中文常见 `Microsoft YaHei`、`SimHei`、`PingFang SC`），
渲染时会替换，差异会体现在 `manifest.txt` 的
`Known font rendering differences` 字段里。
