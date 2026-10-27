# 用户提示词模板

给**没接触过这个 Skill** 的使用者看的。

**先看第 1 段** —— 一条提示词同时完成"找 skill + 装 + 干活"。
后面是拆开版，需要更细控制时才用。

---

# 第 1 段 · 一条提示词搞定

复制这个，**连图一起发**：

```text
帮我从 github 安装 https://github.com/liuweispace/posterloom-sklls 里的
office/reference-image-to-pptx skill（装到 ~/.hermes/skills/ 下），
装完跑一次它的自测脚本确认，然后把我上传的这张参考图重建为可编辑的 PowerPoint。

要求：
- 参考图的完整像素画布作为唯一坐标基准，不要 contain、不要留白缩放
- 所有框体、文字、箭头用 PPT 原生对象重建，不要贴图
- 图标重绘为 SVG，渲染成 128×128 透明 PNG 后插入
- 渲染 PPT 并与参考图做全画布对比，至少校正两轮
- 最后给我可编辑 PPTX + 工程 ZIP + 图标素材 ZIP，并报告验收指标
```

这段话做了三件事：**找 skill → 装 → 干活**。使用者不需要知道 GitHub 地址长什么样。

**已经装好了**就只说后半段：

```text
用 reference-image-to-pptx skill 把我上传的这张参考图重建为可编辑的 PowerPoint。

- 参考图的完整像素画布作为唯一坐标基准，不要 contain、不要留白缩放
- 所有框体、文字、箭头用 PPT 原生对象重建，不要贴图
- 图标重绘为 SVG，渲染成 128×128 透明 PNG 后插入
- 渲染 PPT 并与参考图做全画布对比，至少校正两轮
- 最后给我可编辑 PPTX + 工程 ZIP + 图标素材 ZIP，并报告验收指标
```

**助手说找不到这个 skill 时**（例如它只搜了 `posterloom/` 目录）：

```text
先读一下 ~/.hermes/skills/reference-image-to-pptx/SKILL.md，按里面的流程做。
```

---

# 拆开版 · 需要更细控制时用

## 第 1 步 · 找到并装上这个 Skill

## 它在哪

| | |
|---|---|
| **GitHub 仓库** | `https://github.com/liuweispace/posterloom-sklls` |
| **仓库内路径** | `office/reference-image-to-pptx/` |
| **装到本机的位置** | `~/.hermes/skills/reference-image-to-pptx/` |
| **正式 Skill 名** | `Reference-Image-to-Full-Canvas-Editable-PPTX` |
| **目录名（实际调用用这个）** | `reference-image-to-pptx` |

仓库首页 README 的「📚 这里有什么」表格第 2 行就是它。

## 装（一条命令）

把下面这段**整段复制**给装这个 Skill 的人（你的 AI 助手，或你自己的终端）：

```text
帮我从 github 安装 https://github.com/liuweispace/posterloom-sklls 里的
office/reference-image-to-pptx 这个 skill，装到 ~/.hermes/skills/ 下。

装完运行它的自测脚本 python3 scripts/selftest.py，把 40 项检查结果贴给我。
```

自己装的话：

```bash
curl -fsSL https://github.com/liuweispace/posterloom-sklls/archive/refs/heads/main.tar.gz | tar xz
mv posterloom-sklls-main/office/reference-image-to-pptx ~/.hermes/skills/reference-image-to-pptx
```

⚠️ **装到顶层，不要装在 `posterloom/office/` 嵌套层** —— 嵌套层会让 Hermes
把同名 Skill 加载两次（`reference-image-to-pptx` 和 `posterloom` 各一份），
既浪费上下文，也可能触发「找不到这个技能」的判断。


## 确认装上了

```bash
ls ~/.hermes/skills/reference-image-to-pptx/
# 应该看到: SKILL.md  scripts/  references/  templates/

cd ~/.hermes/skills/reference-image-to-pptx && python3 scripts/selftest.py
# 应该看到: 40/40 PASS  SELFTEST OK
```

**看到 `40/40 PASS` 才算装好。** 失败的话通常是缺依赖：

| 缺什么 | 症状 | 解决 |
|---|---|---|
| LibreOffice | 自测里 `ppt rendered` FAIL | `brew install --cask libreoffice` |
| `pdftoppm` | 渲染 PDF 失败 | `brew install poppler` |
| python-pptx | import 报错 | `pip3 install python-pptx` |
| Pillow / NumPy | import 报错 | `pip3 install pillow numpy` |

---

# 第 2 步 · 让它干活

## 档位 A · 最简（大多数情况用这个）

```
用 reference-image-to-pptx skill 处理这张参考图，
把它重建为可编辑的 PowerPoint。

要求：
- 参考图的完整像素画布作为唯一坐标基准，不要 contain、不要留白缩放
- 所有框体、文字、箭头用 PPT 原生对象重建，不要贴图
- 图标重绘为 SVG，渲染成 128×128 透明 PNG 后插入
- 渲染 PPT 并与参考图做全画布对比，至少校正两轮
- 最后给我可编辑 PPTX + 工程 ZIP + 图标素材 ZIP，并报告验收指标
```

## 档位 B · 推荐（附带具体验收要求）

```
用 reference-image-to-pptx skill 把我上传的参考图重建为可编辑 PowerPoint。

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

## 档位 C · 多页 / 批量

```
用 reference-image-to-pptx skill 处理我上传的 N 张参考图，
每张图对应一页 PPT，按上传顺序排页。

注意：
- 每页各自按自己的像素画布测量，页面比例可以互不相同
- 不要为了「看起来整齐」把不同比例的页强行统一成 16:9
- 图标资产可以在多页之间复用，同一 asset 只保留一份 SVG 和 PNG
- 一次生成一个多页 PPTX（每个页面尺寸相同时）或多个单页 PPTX（尺寸不同时）
  —— 尺寸不同时必须输出多个文件，并在 manifest 里说明原因
- 每页独立做三轮构建和全画布验收
```

## 不知道叫什么名字怎么办

有些 AI 助手对 Skill 名称敏感。**如果它说找不到这个 skill**，直接说：

```
先读一下 ~/.hermes/skills/reference-image-to-pptx/SKILL.md，
按里面的流程做。
```

或者更简单：

```
帮我把 ~/.hermes/skills/reference-image-to-pptx/SKILL.md 读一遍，
然后用它重建我上传的参考图。
```

---

# 第 3 步 · 怎么验收（拿到文件后自己看）

## 交付物在哪

跑完后应该得到：

| 文件 | 在哪 | 是什么 |
|---|---|---|
| `editable_reproduction.pptx` | `ppt/` | **主要交付物** —— 可编辑 PPT |
| `editable_ppt_project.zip` | 项目根 | 完整工程（含所有中间产物） |
| `icons_assets.zip` | 项目根 | 只含 `svg/` + `png_128/` |
| `comparison.png` | `preview/` | 参考图 vs PPT 并排对比 |
| `overlay_comparison.png` | `preview/` | 50% 半透明叠加 |
| `difference_map.png` | `preview/` | 像素差异图（亮的=有差异） |
| `icons_preview.png` | `preview/` | 图标总览 |
| `manifest.txt` | 项目根 | 全部测量值与验收结果 |

## 三种自检

**① 确认不是把图片贴进去了**

```bash
unzip -l ppt/editable_reproduction.pptx | grep ppt/media/
```

只应看到图标 PNG（几个小的），**看不到参考图**。

**② 确认箭头是真连接符**

```bash
unzip -p ppt/editable_reproduction.pptx ppt/slides/slide1.xml | grep -c "tailEnd"
```

应该 ≥ 1（每个箭头一个 `a:tailEnd`）。没有这个标签说明箭头是图片或 Freeform。

**③ 看 manifest.txt 的关键行**

```text
Full-canvas mapping used      yes
Contain or fit-inside used    no
Extra global padding used     no
Freeform arrows used          no
Reference image used as background   no
Out-of-bounds warning count   0
PPTX file size                < 2000000
```

## 肉眼比对的顺序

1. 先开 `preview/comparison.png` —— 左右并排，一眼看出整体比例对不对
2. 再开 `preview/difference_map.png` —— **亮的地方就是要修的地方**
3. 最后开 `preview/overlay_comparison.png` —— 重影错位最直观

---

# 常见追问与回答

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

**「PPTX 里能直接改吗？」**
能。框体是 PPT 原生形状、文字是文本框、箭头是连接符 —— 双击就能改。
只有图标是 PNG（128×128 透明底），要改得动 SVG 再重新生成。

**「页面比例必须和原图一样吗？」**
是。这是这个 Skill 的核心约束 —— 页面比例由参考图像素尺寸决定，
不是固定 16:9。缩到固定比例再加白边是明确禁止的做法。

**「支持几张图？」**
多张图 → 多页 PPT，按上传顺序排页。每页各自按自己的画布测量，
比例可以不同（比例不同时会输出多个文件而不是硬凑成一个）。
