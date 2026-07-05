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
- **高颜值**:设计固化在 look 包(令牌 + 版式模板),不依赖 LLM 审美。
- **不溢出**:几何来自浏览器实测;结构层断言零越界。

## 仓库布局

```
ppt_engine/          核心库(纯 Python,pip 可装)
  looks/riso/        riso look 包 —— 当前唯一精调 look(见下)
mastra/              生成层(TypeScript):brief --LLM--> Deck IR --cli--> pptx
examples/            确定性 demo(不依赖 LLM)
out/                 全部产物(gitignore),一次生成 = 一个目录
docs/                设计文档
```

## look 包(`ppt_engine/looks/<id>/`)

一套设计语言 = 一个自包含目录,引擎按目录发现并加载,新增 look 引擎零改动:

```
manifest.json     设计令牌:色板 / 字体栈 / 嵌入清单 / chart palette / major·minor
templates/*.j2    全套版式模板(自包含,无共享回退)
fonts/*.ttf       该 look 嵌入的全部字体
icons.json        look 专属图标,叠加在引擎基础 stroke 图标集之上
art.py            图像钩子:STYLE_SUFFIX(t2i 风格纪律)+ hero_generate / hero_from_source
constraints.json  跨字段版式约束(如 toc≤6),生成侧(mastra)从这里读
agent.zh.md       给 LLM 的指令片段(美学气质 + 版式 cheat-sheet)
```

生成器通过 `python3 -m ppt_engine.cli --describe riso` 拿到图标白名单/约束/指令片段——**约束单一来源**。

现有 look:**riso**(Risograph zine:暖纸 + 联邦蓝/荧光粉/芥末,Anton × 思源黑 Black 重黑海报标题,Space Mono 注解,硬边色块 + 套色错位)。糙版主题(editorial/aurora/ember)已清除,git 历史可寻。

## 运行

```bash
pip install -e .                                  # 或手动装 pyproject 里的依赖
python3 examples/demo_riso.py                     # riso 全套版式样张 → out/riso_demo/
python3 examples/demo_beauty_riso.py              # 上海美妆样张(含 t2i hero) → out/beauty_riso/
python3 -m ppt_engine.cli --deck deck.json --out out/x/deck.pptx --shots out/x/shots
cd mastra && npm run beauty                       # brief --qwen3.7-plus--> IR --> pptx(见 mastra/README)
```

> 默认用系统 Chrome(`channel="chrome"`),无需 `playwright install`。

## 能力

- **16 个版式原型**:`cover` `hero`(image-mode 全出血大图)`toc` `section` `kpi` `bullets` `two_col` `comparison` `process` `chart`(原生图表)`icon_grid` `timeline` `table` `pillars` `quote` `closing`。
- **image-mode(hero 大图页)**:t2i(qwen-image-2.0,prompt 只写内容、look 强制风格)→ look 的 `hero_from_source` 双版分色后处理;无 key/失败自动降级到程序化 `hero_generate`(sun/city/shanghai/vanity 母题),离线可用;全出血嵌入为**原生图片** + scrim + 原生叠字。
- **Risograph 设计系统(高颜值)**:**Anton × 思源黑 Black** 重黑海报标题、**Space Mono** 等宽注解、**套色错位**(同字错位叠色)、硬边色块卡、暖纸 + 联邦蓝/荧光粉/芥末三色。
- **多字体嵌入 + 拉丁/中文分字族**:OFL 开源字体按 deck 用字**子集化**后嵌入 `.pptx`(写入 `major/minorFont`);**按元素拆 `a:latin` / `a:ea`**——同一标题里拉丁走 Anton、中文走思源黑 Black。同一份子集喂浏览器度量与最终文档 → 任意机器零安装、渲染一致。
- **图标/素材管线**:stroke 基础集 + look 实心集 → 浏览器 SVG → 逐元素栅格化为透明 PNG → 原生图片嵌入。
- **原生图表**:`add_chart`,categories/series 可在 PowerPoint 改数据。
- **渲染-自检闭环**:① IR 字数预算(生成端拦截)② 结构不变量(几何层断言越界/重叠,无需出图)③ `render_preview` 出图供视觉评审。

## 代码结构

| 文件 | 职责 |
|------|------|
| `ppt_engine/ir.py` | IR:判别联合 + 字数预算(`max_length`/条数上限) |
| `ppt_engine/theme.py` | look 加载器:`looks/*/manifest.json` → `Theme`(令牌 + 模板目录 + 图标 + art 钩子 + scheme 映射) |
| `ppt_engine/looks/riso/` | riso look 包(令牌/模板/字体/图标/图像钩子/约束/agent 指令) |
| `ppt_engine/icons.py` | 引擎基础 stroke 图标集(每个 look 都可用的语义名) |
| `ppt_engine/genimage.py` | 通用 t2i 客户端(DashScope qwen-image-2.0),风格后缀由 look 注入 |
| `ppt_engine/measure.py` | 浏览器内 JS:`[data-ppt]` 叶子 → 几何 + 样式 |
| `ppt_engine/render.py` | 几何 → 原生 pptx(渐变/字体/图表色/主题色引用) |
| `ppt_engine/oox_theme.py` | 令牌写入 `theme1.xml`(一键换色/换字) |
| `ppt_engine/fonts.py` | 按 deck 用字子集化 look 的字体 |
| `ppt_engine/embed_fonts.py` | 把子集字体嵌入 `.pptx`(OOXML `embeddedFontLst`) |
| `ppt_engine/selfcheck.py` | 结构不变量 + `render_preview` 出图 |
| `ppt_engine/build.py` | 编排:IR → 子集字体 → HTML → 浏览器 → 渲染 → 嵌字 |
| `ppt_engine/cli.py` | JSON 桥(外部编排器入口)+ `--describe` look 契约 |
| `mastra/` | LLM 生成层:brief → Deck IR → cli 构建(详见 `mastra/README.md`) |

## 已知限制 / 下一步

- **预览保真**:浏览器截图(`out/<run>/shots/`)用嵌入字体,是**真实排版**;但**原生图表与 hero 海报图只在真实 `.pptx` 里渲染**——用 LibreOffice `render_preview` 核验(注意它会把嵌入字替换成楷体状字形,是预览替字非 bug)。
- **图标为 PNG**:可缩放性有限 → 下一步 SVG→freeform 保矢量。
- **自检的视觉层**:`render_preview` 已出图,接入视觉模型做美学评审 + 自动修复闭环。
- 更多 look(编辑部/极简等,按 look 包格式增量添加)、MCP 接入。
- 大方向:v0.3「按主题现场生成身份」路线(见 `feature/ppt-master` 分支 docs)以本 look 包格式为 seed/兜底。
