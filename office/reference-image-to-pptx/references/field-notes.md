# 实测笔记：踩过的坑与根因

本文记录的是**实际跑出来**的失败与修复，不是设计构想。每条都附了根因，
因为这些坑有一个共同点：症状和原因相隔很远，靠读代码看不出来。

---

## 1. 页面比例误差永远不是 0

**症状**：验收项「页面宽高比误差：0」看起来满足了，实际是 `1.5e-5`。

**根因**：`prs.slide_height = Inches(SLIDE_W_IN * REF_H / REF_W)`。
`Inches()` 内部是 `int(inches * 914400)`，**截断**。宽度和高度各自截断后，
比值就不再精确等于参考比例。

**修复**：约分 + 整数倍。

```python
g = math.gcd(ref_w, ref_h)
rw, rh = ref_w // g, ref_h // g
k = round(target_w_emu / rw)
slide_w_emu = k * rw
slide_h_emu = k * rh
```

此时 `slide_w_emu * ref_h == slide_h_emu * ref_w` **严格成立**，
比例误差是数学上的 0，而不是四舍五入后的 0。

**自测断言**：

```python
assert prs.slide_width * h == prs.slide_height * w
```

---

## 2. 所有框体都有灰色投影

**症状**：渲染出来每个圆角矩形后面都有一圈灰影，参考图里根本没有。

**根因**：`python-pptx` 的 `add_shape()` 会插入一个 `<p:style>` 元素，指向主题的
形状默认值（theme effect / theme fill / theme line）。PowerPoint 打开时按主题
渲染，就带上了默认投影。连接符 `add_connector()` 同样会挂 `<p:style>`。

**修复**：删掉 `<p:style>`，并显式写入空的 `<a:effectLst/>` 覆盖继承。

```python
node = shape._element.find(qn("p:style"))
if node is not None:
    shape._element.remove(node)
```

**注意**：连接符的元素是 `p:cxnSp`，但 `spPr` 子元素路径相同，所以同一个
函数对框体和连接符都适用 —— 但**必须对连接符也调用**，否则箭头还是会带阴影。

---

## 3. 文字和边框整体偏大偏粗

**症状**：spec 里写 `font_size_pt: 11`，渲染出来比参考图明显大一圈。

**根因**：参考图的尺寸是**像素**，PowerPoint 的字号和线宽是**磅**。直接把像素
数字当磅用，等于放大了 `canvas_w_in * 72 / ref_w` 倍。参考图 1400px 宽对应
16 英寸页面时，这个系数是 **0.82**；但如果参考图是 800px 宽，系数就变成
**1.44** —— 文字会大 44%。

**修复**：提供 `font_size_px` / `line_width_px`，按画布比例换算。

```python
def px_font_pt(px, canvas):
    return px / canvas.ref_w * canvas.slide_w_in * 72.0
```

`font_size_pt` / `line_width_pt` 仍然保留，用于显式指定磅值。

**副作用**：PowerPoint 的自动缩放会让字号再次偏离，所以必须关掉 autofit：

```python
bodyPr.append(OxmlElement("a:noAutofit"))
```

---

## 4. 边框落在相邻像素

**症状**：参考图边框在 `x=32`，重建在 `x=31`。整体看着没差，但差 1px。

**根因**：第 3 条的线宽问题。线宽不准 → 描边中心偏移 → 抗锯齿后最暗的列
挪到了相邻像素。

**修复**：换算线宽（见上条）。修完后 `ref x=32 / ren x=31`，落在 1px 容差内。

---

## 5. 全页占用率通过但框体是错的

**症状**：左右各放一个错误的小对象，全页占用率照样接近阈值。

**原因**：占用率是**全页**指标，对「内容整体偏左或偏上」这类错误不敏感。

**修复**：必须**单独**测量四个主框体（标题 / 左模块 / 右模块 / 底部模块）
的每条边，做 3–5 参考像素级的比较。占用率和主框体两项都要过。

---

## 6. 视觉模型会误报「有阴影」和「位置右移」

**症状**：像素级对比图跑完，视觉模型报告"仍有灰色光晕"、"整体右移 5–11px"。

**实测**：

```
面板外侧 12px 宽的取样带
  ref:  mean 254.00  min 254   unique 1     ← 纯白，完全干净
  ren:  mean 242.18  min 115   unique 19    ← 有 1px 渗色
```

全局对齐搜索结果 `best dx=-1, dy=0`，而按颜色直接定位边框：
`ref teal x=32 / ren teal x=32`、`ref red x=730 / ren red x=730` ——
**位置完全一致**，所谓"右移"是模型在降采样对比图上的读数误差。

**结论**：视觉模型的判断用来**发现**问题，不用来**定案**。
定案必须回到像素：

```python
# 边框像素位置
def border_col(im, color, x_lo, x_hi, y0, y1):
    a = np.array(im.convert("RGB"))[y0:y1, x_lo:x_hi]
    d = np.abs(a - np.array(color)).sum(axis=2)
    ys, xs = np.where(d < 40)
    return int(xs.min() + x_lo) if len(xs) else None

# 面板外侧是否干净
band = np.array(ren.convert("L"))[110:500, 20:32]
print(band.min(), band.mean(), len(np.unique(band)))

# 全局对齐搜索
for dy in range(-6, 7):
    for dx in range(-6, 7):
        mse = ((A[20:840, 20:1380] - B[20+dy:840+dy, 20+dx:1380+dx]) ** 2).mean()
```

---

## 7. LibreOffice 退出码 77

**症状**：`soffice --headless --convert-to pdf` 无输出，PDF 没生成。

**根因**：默认用户配置目录被另一个 soffice 实例锁住。

**修复**：每次用独立目录。

```bash
libreoffice -env:UserInstallation=file:///tmp/lo_profile_<name> \
  --headless --convert-to pdf --outdir preview ppt/editable_reproduction.pptx
```

---

## 8. macOS 上没有 CairoSVG

**症状**：`import cairosvg` 失败，而 libcairo 装起来很麻烦。

**修复**：三级降级，接口不变。

```python
try:
    import cairosvg                                    # 首选
    cairosvg.svg2png(url=..., write_to=..., output_width=128, output_height=128)
except Exception:
    rsvg = shutil.which("rsvg-convert")                # 次选，无需 cairo
    if rsvg: subprocess.run([rsvg, "-w", "128", "-h", "128", "-o", png, svg])
    else:
        ql = shutil.which("qlmanage")                  # macOS 内置兜底
        # qlmanage -t -s 128 -o tmpdir icon.svg
```

`rsvg-convert`（librsvg）在 macOS 上直接可用，是最省事的次选。

---

## 9. LibreOffice 本身缺失

**症状**：无法渲染 → 无法比对 → 无法验收。

**这是硬依赖**，没有它整个「渲染 → 对比 → 校正」循环就不成立。

```bash
brew install --cask libreoffice
```

装不了 LibreOffice 的环境里，`qlmanage` 可以出一张缩略图，但那是低保真的，
**不能替代**验收环节。此时必须明确告知用户「已完成生成，但未完成渲染验收」。

---

## 10. 合成参考图的字体让自测产生假阳性

**症状**：自测报「title text height matches reference — ref=8px ren=14px」。

**根因**：合成参考图用 `ImageFont.load_default()`，那是**位图字体**，
不管你传多大的 size，实际字高都是 ~8px。而 spec 里声明的是 22px。
参考图和 spec 自相矛盾，重建当然"不匹配"。

**修复**：合成参考图改用真实 TrueType 字体，尺寸与 spec 声明一致。

```python
ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
```

**教训**：自测的参考图必须和 spec 同源，否则测的是"参考图错"而不是"引擎错"。
