# ppt-tool — 高颜值 · 可编辑 PPT 生成引擎

把语义 IR 变成**原生可编辑、设计感强**的 `.pptx`。智能体只填语义槽位,所有视觉决策由引擎确定性完成。

## 架构(核心赌注:浏览器当排版引擎)

不自研排版/文本度量,而是**让浏览器排版与度量**,再把已解析的几何映射成**原生 pptx 对象**:

```
IR(pydantic)              语义 + 字数预算(判别联合,每版式独立 schema)
   └─► 原型 HTML/CSS       每个版式一个模板,设计令牌注入 CSS 变量
        └─► 无头浏览器      排版 + 文本度量(中文断行天生正确)
             └─► 已解析几何  每个 [data-ppt] 叶子的绝对位置 + 计算样式
                  └─► 渲染器  geometry → 原生文本框 / 形状 / 原生图表 / 图标图片
                       └─► .pptx  文字是文字、形状是形状、图表可改数据、可换主题色
```

- **可编辑**:全部原生对象 + 令牌写入 `theme1.xml` 的 `clrScheme/fontScheme`,可在 PowerPoint「设计 > 颜色 / 字体」一键换肤。
- **高颜值**:设计固化在令牌(`theme.py`)+ 版式(`templates/`),不依赖 LLM 审美。
- **不溢出**:几何来自浏览器实测;结构层断言零越界。

## 运行

```bash
pip install python-pptx playwright jinja2 pydantic pillow lxml fonttools
python3 demo.py growth_review.pptx ./preview   # 第二个参数可选:每页浏览器截图(真实字体预览)
```

> 默认用系统 Chrome(`channel="chrome"`),无需 `playwright install`。

## 能力(P1)

- **11 个版式原型**:`cover` `toc` `section` `kpi` `bullets` `two_col` `comparison` `process`(带图标)`chart`(原生图表)`quote` `closing`。
- **3 套主题**:`editorial`(暖纸 · 思源宋体 · 朱砂,默认高颜值)、`aurora`(商务靛蓝)、`ember`(暖橙红)。同一份 IR,换 `theme` 即整体改色 + 改字体。
- **编辑部设计系统(高颜值)**:衬线大标(思源宋体)× 黑体正文的字号反差、暖纸/墨色双场景、发丝线分隔、章节页巨型虚化数字、朱砂单点强调——设计语言固化在令牌+版式,产出杂志级版面而非默认模板。
- **双字体嵌入(跨平台一致)**:衬线 **Noto Serif SC** + 黑体 **Noto Sans SC**(均 OFL 可嵌入),按 deck 用字**子集化**后嵌入 `.pptx`(写入 `major/minorFont`);同一份子集喂给浏览器度量(`@font-face`)与最终文档 → 任意机器零安装、渲染一致。整套 deck 仅 +~360KB。
- **图标/素材管线**:内置 stroke 图标集 → 浏览器 SVG → 逐元素栅格化为透明 PNG → 原生图片嵌入。
- **原生图表**:`add_chart`,categories/series 可在 PowerPoint 改数据。
- **渲染-自检闭环**:① IR 字数预算(生成端拦截)② 结构不变量(几何层断言越界/重叠,无需出图)③ `render_preview` 出图供视觉评审。

## 代码结构

| 文件 | 职责 |
|------|------|
| `ppt_engine/ir.py` | IR:判别联合 + 字数预算(`max_length`/条数上限) |
| `ppt_engine/theme.py` | 设计令牌(颜色/字体/图表色板)+ scheme 映射 |
| `ppt_engine/templates/` | 版式原型(HTML/CSS),11 个 `*.html.j2` |
| `ppt_engine/icons.py` | stroke 图标集(v1 PNG,v2 freeform) |
| `ppt_engine/measure.py` | 浏览器内 JS:`[data-ppt]` 叶子 → 几何 + 样式 |
| `ppt_engine/render.py` | 几何 → 原生 pptx(渐变/字体/图表色/主题色引用) |
| `ppt_engine/oox_theme.py` | 令牌写入 `theme1.xml`(一键换色/换字) |
| `ppt_engine/fonts.py` | 按 deck 用字子集化开源 CJK 字体 |
| `ppt_engine/embed_fonts.py` | 把子集字体嵌入 `.pptx`(OOXML `embeddedFontLst`) |
| `ppt_engine/selfcheck.py` | 结构不变量 + `render_preview` 出图 |
| `ppt_engine/build.py` | 编排:IR → 子集字体 → HTML → 浏览器 → 渲染 → 嵌字 |

## 已验证

- 11 页中文 deck,11 种版式全部跑通;在真 PowerPoint 的 OOXML 上用 LibreOffice 出图核验。
- 结构自检:81 文本框 · 59 形状 · 4 图标图片 · 1 原生图表 · **0 文本越界/重叠**。
- 文本可读取(可编辑)、图表数据原生可改、`ember` 主题验证整体换肤。
- 字体嵌入结构校验:2 个 `fntdata` 子集(regular/bold),关键中文字形齐全,包可被重新打开。
- 自检三道闸均验证可拦截:字数超限 / 条数超限 / 几何越界 / 文本重叠。

## 已知限制 / 下一步

- **预览保真**:浏览器截图(`preview/slide_*.png`)用嵌入字体,是**真实排版**;LibreOffice 的 `render_preview` 不认嵌入字会把宋体替换成楷体——只用它核验**版式/几何**,字体效果以浏览器图或真 PowerPoint 为准。
- **图标为 PNG**:可缩放性有限 → 下一步 SVG→freeform 保矢量。
- **封面纯排版**:已是编辑部杂志封面;下一步可选**封面 image-mode**(AI 出图全出血 + 叠原生字)再加冲击。
- **自检的视觉层**:`render_preview` 已出图,接入视觉模型做美学评审 + 自动修复闭环。
- 阴影/质感深化(噪点、玻璃拟态)、更多主题与版式、MCP 接入。
