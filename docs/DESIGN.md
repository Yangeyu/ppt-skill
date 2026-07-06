# 高颜值 AI PPT 生成引擎 · 设计文档

> 版本：v0.3（草案）  日期：2026-06-28  状态：待评审
>
> **实现状态注记(2026-07-06)**:本文的「按主题现场生成身份(freedom)/艺术总监/
> 创作轨双轨/七段管线」是**北极星,当前未实现为产品线**。已落地并验证的形态是
> **skill + look 包 + 五重机器评论官**(见根目录 SKILL.md 与 README):精修的
> look 包承担"已冻结的设计语言",agent 写语义 IR,浏览器算几何。freedom 未来
> 若恢复,正确形态是「艺术总监现场生成一个 **look 包**(身份过 critic/identity
> 门禁 + 复用/生成版式)」,而非绕过 look 包直接渲染——旧 compose 管线因模板
> 已按 look 特化而失效,已于 2026-07-06 拆除(git 历史可考)。本文其余部分
> 作为方向文档保留;身份评论官(§4)与页面评论官(§12)已实现并在产品线服役。
>
> 一句话定位：智能体输入主题/内容，引擎产出**原生可编辑、设计感强、稳定不崩**的 `.pptx`。
>
> **架构选型：浏览器为排版真源 + 双轨创作 + 现场生成视觉身份 + 递归评论官闭环。**
> 内容与美学由 LLM 决策；排版几何由浏览器 CSS 引擎算出（绝不目测）；A 层纪律由评论官在身份层与页面层强制保证；产物统一走「浏览器量测 → 原生 DrawingML」管线。
>
> 变更（v0.2 → v0.3）见 §2.4。核心翻转：**放弃确定性**、**视觉身份从「固定主题库挑选」改为「按主题现场生成」**、**LLM 创作从「节制的 SVG 逃生舱」升为「一等公民创作轨（写 HTML/CSS）」**、**质量主机制从「结构不变量」升为「QUALITY rubric + 递归评论官」**。

---

## 目录

1. [目标与边界](#1-目标与边界)
2. [核心设计原则](#2-核心设计原则)
3. [整体架构：七段管线](#3-整体架构七段管线)
4. [艺术总监 / 身份生成层](#4-艺术总监--身份生成层)
5. [IR 中间表示](#5-ir-中间表示)
6. [浏览器排版基座](#6-浏览器排版基座)
7. [设计系统套件](#7-设计系统套件)
8. [结构轨：版式模板库](#8-结构轨版式模板库)
9. [创作轨：LLM 写 HTML/CSS](#9-创作轨llm-写-htmlcss)
10. [主题令牌与 spec_lock](#10-主题令牌与-spec_lock)
11. [渲染器：原语 → 原生 DrawingML](#11-渲染器原语--原生-drawingml)
12. [递归评论官闭环](#12-递归评论官闭环)
13. [智能体接入（MCP）](#13-智能体接入mcp)
14. [质量保障与验收](#14-质量保障与验收)
15. [工程结构 · 路线图 · 风险](#15-工程结构--路线图--风险)

---

## 1. 目标与边界

### 1.1 目标
- **高颜值**：产出看起来"被设计过"，且**贴合主题**——给独立书店 zine 就长出 Riso 油印感，给财报就长出克制的商务感，而非千篇一律的模板皮。
- **可编辑**：原生 `.pptx`，文字是文本框、形状是矢量、图表是原生图表对象、配色走主题色引用（可一键换肤）、字体已嵌入。
- **稳定产出**：智能体接入后不溢出、不重叠；**地板高**靠评论官闭环保证，不靠"避免使用 LLM"。
- **通用**：覆盖商业汇报、课件、营销、BP、知识科普等多数内容形态。

### 1.2 高颜值 = A 层 + B 层（本设计的定义性认知）
颜值不是一个东西，是两层，拆错了后面全错：

- **A 层 · 体系纪律**（可编码，是**地板**）：模块化字阶、字重对比、行高、**中西混排**（盘古之白/标点挤压/禁孤行）、留白、网格对齐、配色克制（60-30-10）、对比度、图标家族统一、图像统一处理、跨页一致。
- **B 层 · 艺术指导**（靠品味，是**天花板**）：为具体主题现场做的大胆决策——套印错位、戏剧裁切、打破网格、视觉隐喻、招牌母题。

> **核心洞察：AI deck 之所以丑，99% 丑在 A 层塌了，不是 B 层不够。** 多数人感知的"高颜值"其实是 A 层纪律。所以实现路径是：**先把 A 层做成不可违反的硬约束，再让 LLM 在护栏内对 B 层大胆。**

### 1.3 递归 A/B（贯穿全局的原理）
A/B 两层**递归适用于两个层级**：

| 层级 | B 层（LLM 自由发挥） | A 层（机器校验地板） |
|---|---|---|
| **身份层** | 艺术总监为主题**发明设计语言**（配色/字体/母题/图像处理） | 身份评论官校验其**体系成立**（字阶模块化？配色 60-30-10？对比/配对达标？） |
| **页面层** | Executor 在锁定语言内**艺术指导构图** | 页面评论官校验**页面纪律**（越界/字阶/留白/对齐/一致） |

> 旧教条「AI 不需要审美」被翻新为 **「AI 提出美学，机器校验其体系是否成立」**。Freedom ≠ 无约束，而是 **发明时自由、执行时有纪律**：LLM 可为 zine 发明 Riso，但它必须过 A 层体系校验，且一旦锁定，全 deck 都遵守它。

### 1.4 非目标（v1 不做）
- 不做网页在线编辑器（用户在 PowerPoint/WPS/Keynote 里编辑）。
- 不做动画/转场（保留 notes 字段，后续扩展）。
- 不做 PPTX 反向解析/导入（只生成不读取）。
- **不保证同输入同输出**（v0.2 曾以此为原则，v0.3 明确放弃，见 §2.4）。
- 不追求与 PowerPoint 像素级一致的预览（预览仅用于评论官/人工批注）。

### 1.5 成功判据
- 给定主题，智能体 ≤2 轮页面评论官内产出 10–15 页 deck，**零溢出/零重叠**。
- 产出在 PowerPoint 中：文字可改、可一键换主题色、图表可改数据、字体已嵌。
- 表现页（封面/主视觉）达到 ppt-master「Indie Bookstore Zine Guide」封面级的 B 层艺术指导，但**仍原生可编辑**。
- 创作轨页与结构轨页**视觉身份一致**（同一份现场生成的 spec_lock）。

---

## 2. 核心设计原则

1. **浏览器是排版真源。** 几何（坐标/换行/对齐）一律由无头 Chrome 的 CSS 引擎算出，**绝不由模型目测坐标**。这绕开 ppt-master 让 LLM 手写绝对坐标 SVG 的根本缺陷（坐标漂移、需 verify-charts 校准）。
2. **LLM 产出语义与美学，不产出像素。** 结构轨：LLM 选版式 + 填语义槽位。创作轨：LLM 写 **HTML/CSS**（声明式），浏览器解算成像素。两轨都不写绝对坐标。
3. **视觉身份按主题现场生成。** 艺术总监为每个主题发明整套设计语言，而非从固定主题库挑选。这是 B 层天花板的来源。
4. **AI 提出美学，机器校验体系（递归 A/B）。** 见 §1.3。信任 LLM 发明，但不信任它"体系一定对"——身份评论官与页面评论官是地板的强制器。
5. **评论官即地板（取代确定性）。** 放弃"纯函数同输入同输出"；地板改由"浏览器算出的正确几何 + 评论官循环收敛"保证。
6. **可编辑是第一公民。** 优先主题色引用（`schemeClr`）、原生形状、原生图表、嵌入字体。创作轨产出也必须可测、可换色（见 §7 三契约）。
7. **单一锁定真源（spec_lock）。** 现场生成的设计语言冻结成一份机器可读令牌；两轨都从它读；长 deck 逐页重读抗上下文漂移。

> 与 ppt-master 的关系：吸收其「按主题生成身份、spec_lock 抗漂移、逐元素 dispatch 转 DrawingML、质检 gate」；**抛弃其「LLM 手写绝对坐标」**，改用浏览器算几何。

### 2.4 与 v0.2 的明确差异

| 维度 | v0.2（旧） | v0.3（新） |
|---|---|---|
| 确定性 | 「确定性优先·纯函数」 | **放弃**。地板 = 浏览器几何 + 评论官收敛 |
| 视觉身份来源 | 固定主题库挑选（颜值固化、AI 无需审美） | **按主题现场生成**（艺术总监 → 身份评论官 → 冻结） |
| 设计哲学 | 「AI 不需要审美」 | **「AI 提出美学，机器校验体系」（递归 A/B）** |
| LLM 创作路径 | 「SVG 逃生舱·默认禁用·节制」 | **「创作轨·一等公民·按角色路由」** |
| 排版基座 | 自研盒模型求解器为主 | **浏览器（HTML/CSS）为唯一排版真源**（两轨共用） |
| 创作轨作者 | LLM 手写 SVG | **LLM 写 HTML/CSS**（几何浏览器算） |
| 主题库角色 | 唯一来源 | 降为**可选 seed / 兜底** |
| 质量主机制 | 结构不变量 + 次要自检 | **QUALITY rubric + 递归评论官闭环** |
| 黄金图回归 | SSIM 像素对标 | 失效（非确定）→ **rubric 通过率 + 结构不变量（作用于已测原语）** |

---

## 3. 整体架构：七段管线

```
内容/大纲
 ① 艺术总监(LLM)      为主题发明设计语言 → 候选 spec_lock（配色/字阶/字体/母题/图像处理/网格）
 ② 身份评论官(A层递归) 校验设计系统是否体系成立 → 不过则修正/重生成
 ③ 套件实例化          冻结 spec_lock + 实例化「设计系统套件」(通用骨架 ⊕ 生成令牌值 ⊕ 生成母题组件)
 ④ 按角色路由          表现页 → 创作轨(LLM 写 HTML/CSS) ；结构页 → 结构轨(Jinja2 模板)
 ⑤ 浏览器排版          无头 Chrome 排版 → MEASURE_JS 量原语 + 截图 PNG
 ⑥ 页面评论官          结构评论官(机器) + 美学评论官(视觉模型) → 比对 QUALITY rubric → 带违规项重生成 ≤N 轮
 ⑦ 渲染导出            render_deck：原语翻原生 DrawingML → 原生可编辑 .pptx（schemeClr/原生图表/嵌字）
```

数据流（结构轨页）：`主题 → spec_lock → IR(JSON) → 校验 → Jinja2 模板(吃令牌) → 浏览器排版 → 原语 → render → .pptx`
数据流（创作轨页）：`主题 → spec_lock → LLM 写 HTML/CSS(吃套件) → 浏览器排版 → 原语 → render → .pptx`

两轨在 **⑤ 浏览器排版 / ⑦ render** 汇合，统一产出原生 DrawingML，因此同一 deck 内两轨混排、身份一致、都可编辑。

### 3.1 双轨 · 单管线

| 轨道 | 负责 | 输入 | 排版方式 | 适用页面 |
|---|---|---|---|---|
| **结构轨**（A 层地板） | 稳定、便宜、一致 | LLM 填受约束 IR | Jinja2 模板（吃生成令牌） | 要点/数据/对比/流程/表格/时间线/KPI |
| **创作轨**（B 层天花板） | 表现力、设计感 | LLM 写 HTML/CSS（吃实例化套件） | LLM 自由构图，浏览器算几何 | 封面/章节/金句/主视觉/异形海报页 |

**路由（按页面角色）**：`plan_outline` 给每页标内容意图 → 表现型（cover/section/statement/hero）走创作轨，结构型（list/data/compare/process/table）走结构轨。规则优先、LLM 兜底。一份 zine deck：封面走创作轨拿满 Riso 艺术指导；数据/要点页走结构轨，但用**同一套生成令牌** → 一致身份、不同表达。

---

## 4. 艺术总监 / 身份生成层

这是 v0.3 相对 v0.2 最大的新增，也是 B 层天花板的源头。

### 4.1 输入 / 输出
```python
def art_direct(brief: DesignBrief) -> SpecLockCandidate: ...

class DesignBrief(BaseModel):
    topic: str                       # "独立书店与 zine 文化指南"
    audience: str | None = None
    tone: str | None = None          # 用户可给倾向："复古印刷感" / "极简商务"
    seed_theme: str | None = None    # 可选：以某预置主题为起点（editorial/aurora/ember）
    constraints: dict | None = None  # 品牌色锁定、必须用某字体等硬约束

class SpecLockCandidate(BaseModel):  # 见 §10 spec_lock 结构
    palette: Palette                 # 主/辅/中性/语义色 + 图像处理(duotone/screen-print/...)
    type_scale: TypeScale            # 比例 + 各档字号 + 显示体/正文体角色
    fonts: FontPair                  # CJK + 拉丁，含需嵌入清单
    grid: GridSpec                   # 列数 / 安全区 / 间距标尺
    motifs: list[Motif]              # 招牌母题（每个 = 一段带 data-ppt 的 CSS 组件，见 §7.3）
    rules: list[str]                 # 硬规则（如 "card border-radius = 0"）
    rationale: str                   # 为何这套语言贴合该主题（审计）
```

### 4.2 工作方式
1. LLM 读 `brief`，**为主题发明设计语言**：选定情绪 → 推导配色（含图像统一处理风格）、字阶、字体配对、网格、招牌母题。可借鉴 ppt-master Strategist 的「八项确认」作为提示词骨架（画布/受众/核心信息/配色/字体/图标/公式/图像）。
2. 若给了 `seed_theme`，以预置主题为**起点**微调，而非从零（降方差）。
3. 产出 `SpecLockCandidate` 交给 §4.3 身份评论官。

### 4.3 身份评论官（A 层递归校验）
对候选设计语言做**体系性**校验（细则见 `QUALITY.md` 身份层）：
- **字阶**：是否模块化（比例 ∈ {1.2, 1.25, 1.333, 1.5, golden}）、档数 ≤6、标题↔正文对比足够。
- **配色**：主/辅/中性结构是否成立、是否近似 60-30-10、强调色是否克制、关键前后景对比 ≥ WCAG AA、禁纯黑纯白。
- **字体**：CJK + 拉丁配对是否合理、字族 ≤2、显示体/正文体角色是否清晰。
- **母题/图像**：图像处理是否统一；母题是否只引用令牌色（不得引入离板色）。

不过 → 返回结构化违规项，让艺术总监**修正/重生成**（≤N 轮）。通过 → 进入 §10 冻结为 `spec_lock`。

> **这是 freedom 路线的安全阀**：信任 LLM 发明美学，但用机器把住"体系一定对"。它正是递归 A/B 在身份层的落地。

---

## 5. IR 中间表示

IR 是智能体与引擎的契约。用 **pydantic v2** 建模校验。两轨共用顶层 `Deck`，页面 `data` 是判别联合体。

### 5.1 顶层
```python
class DeckMeta(BaseModel):
    title: str
    lang: Literal["zh", "en"] = "zh"
    aspect: Literal["16:9", "4:3"] = "16:9"

class Deck(BaseModel):
    meta: DeckMeta
    spec: SpecLock                 # §10：现场生成并冻结的设计语言（非主题 id）
    slides: list[Slide]

class Slide(BaseModel):
    role: PageRole                 # cover/section/statement/hero/list/data/compare/process/table/...
    track: Literal["structured", "creative"]   # 由 §3.1 路由决定
    data: LayoutData               # 受 role/track 约束的判别联合体
    notes: str | None = None
    rhythm: Literal["anchor", "breathing", "dense"] = "breathing"  # 节奏（影响留白策略）
```

### 5.2 判别联合体
结构轨页 `data` 形状由 `role` 决定，智能体"点菜 + 填空"，每槽位带 `max_length`（**字数预算 = 第一道稳定闸**，把溢出挡在生成端）。创作轨页用 `custom`：

```python
class BulletsData(BaseModel):
    kind: Literal["bullets"]
    title: str = Field(max_length=40)
    bullets: list[BulletItem] = Field(max_length=6)   # 单条 ≤80 字

class KpiData(BaseModel):
    kind: Literal["kpi"]
    title: str = Field(max_length=40)
    stats: list[Stat] = Field(min_length=2, max_length=4)

class ChartData(BaseModel):                # 图表永远走原生图表对象
    kind: Literal["chart"]
    title: str = Field(max_length=40)
    chart_type: Literal["column", "bar", "line"]
    categories: list[str]
    series: list[Series]

class CustomData(BaseModel):               # ← 创作轨页
    kind: Literal["custom"]
    html: str                              # LLM 写的 HTML 片段（只用套件 class / 令牌变量）
    motifs_used: list[str] = []            # 引用了哪些生成母题（审计）
    # 校验期检查：颜色只能来自令牌变量；字号只能取字阶 class；叶子必带 data-ppt；
    #            禁止内联离板 HEX / 离阶 px；禁止自绘图表（图表必须走 ChartData）

LayoutData = Annotated[
    Union[BulletsData, KpiData, ChartData, CustomData, ...],
    Field(discriminator="kind"),
]
```

### 5.3 创作轨可编辑性契约（校验期强制）
`custom` 页校验时强制：① 颜色取自令牌变量（→ §11 还原 `schemeClr`，保一键换色）；② 禁止自绘图表（图表走 `ChartData` 原生对象，保改数据）；③ 文本用真实 HTML 文本节点、带 `data-ppt="text"`（保可改文字、可被 MEASURE_JS 量出）。违反即校验失败。

---

## 6. 浏览器排版基座

**复用并演进 `feature/svg2ppt` 分支**（已验证：11 页中文零溢出、原生可编辑）。核心思想：**浏览器即排版 + 文本度量引擎**。

### 6.1 管线（演进自 `ppt_engine/build.py`）
```python
# 每页：set_content(html) → 等字体 → MEASURE_JS 量原语 → 图标元素截透明 PNG → 收集
# 全 deck：render_deck(原语列表) → 嵌字
page = browser.new_page(viewport={"width": CANVAS_W_PX, "height": CANVAS_H_PX},
                        device_scale_factor=2)
page.set_content(html, wait_until="load")
page.evaluate("async () => { await document.fonts.ready; }")
prims = page.evaluate(MEASURE_JS)                 # ← 几何由 CSS 引擎算出
page.screenshot(path=...)                          # ← 评论官的美学层输入
```
- v0.3 扩展：在 ⑥ 接入评论官循环（不过则改 IR/HTML 重排重量）；前置 ① 艺术总监；HTML 来源分两轨（模板 / LLM 写）。

### 6.2 抽取契约（演进自 `ppt_engine/measure.py` 的 `MEASURE_JS`）
`MEASURE_JS` 遍历所有 `[data-ppt]` 叶子，`getBoundingClientRect()` + `getComputedStyle()` 输出**扁平原语列表**（CSS px）：

| `data-ppt` | 关键字段 |
|---|---|
| `text` | text, x/y/w/h, fontSizePx, fontWeight, family, color, align, lineHeightPx, upper, letterSpacingPx |
| `rect` | fill, radiusPx, grad(`c1,c2,ang`), borderColor, borderWidthPx |
| `image` | src（`data-src`） |
| `icon` | src（Python 端对元素截透明 PNG 后回填） |
| `chart` | chart（`data-chart` JSON） |
| 公共 | `data-ppt-z`（层级）、`data-ppt-deco`（装饰标记，评论官跳过动画/部分检查） |

> **关键**：坐标全部来自浏览器布局，不存在"模型目测"。v0.3 为评论官**扩充测量字段**（如内容包围盒、与安全区距离、相邻叶子间距）。

### 6.3 单位
画布 1280×720 px（16:9）。px → EMU 在 `render` 末端一次转换（`px@96dpi ×9525`；`pt ×12700`；px→pt `×0.75`）。全程 px 推理，对 LLM 与人都直观（沿用 `ppt_engine/units.py`）。

---

## 7. 设计系统套件

「让 LLM 写 HTML/CSS」要安全，靠这个套件。身份现场生成后，套件 = **三段合成**。

### 7.1 通用结构骨架（恒定，人工设计）
注入 `base.html.j2`。定义**槽位**与**纪律规则**：
- 槽位 CSS 变量：`--color-bg/surface/ink/muted/primary/primary-2/...`、`--type-display/h1/h2/body/caption`、`--space-xs..xxl`、`--grid-cols`。
- 工具 class：`.t-display/.t-h1/.t-body/...`（字号只能取字阶档）、`.c-primary/.c-ink/...`（颜色只能取槽位）、`.grid/.col-*`（强制网格）。
- 硬规则：组件必带 `data-ppt`；禁止内联离阶 px / 离板 HEX。
→ **保证 A 层结构永远在**：LLM 写不出离阶字号、离板颜色。

### 7.2 生成的令牌值（每 deck，来自 spec_lock）
把骨架槽位填成主题贴合的具体值（沿用 `theme.py:Theme.css_vars()` 的产出形式）：
```css
:root{
  --color-bg:#1C1815; --color-bg-content:#F5EFE0; --color-primary:#FF5C8A; /* zine */
  --type-display: 88px; --type-body: 20px; /* 字阶档 */
  --font-serif:"Impact","Arial Black",...; --font-sans:"Microsoft YaHei",...;
}
```
→ 提供 **B 层主题贴合**。换主题 = 换这段，骨架与组件不动。

### 7.3 生成的母题组件（每 deck）
艺术总监为本主题产出的招牌手法，以 **带 `data-ppt` 标记、只引用令牌变量** 的 CSS 组件形式加入套件。例（Riso 套印错位标题）：
```html
<div class="motif-misregister" data-ppt-deco>
  <span class="t-display c-primary"  data-ppt="text" style="transform:translate(2px,2px)">ZINE</span>
  <span class="t-display c-ink"      data-ppt="text">ZINE</span>
</div>
```
→ B 层签名动作，但**仍可测**（带 `data-ppt`）、**仍可编辑**（令牌色 → schemeClr）。半调网点用 `rect` + `data-grad`/pattern；screen-print 图像用 CSS filter 烤进图片。

### 7.4 三契约（套件存在的全部理由）
1. **A 层纪律契约**：只暴露合规 class/槽位 → LLM 写不出离阶/离板。
2. **几何抽取契约**：组件预标 `data-ppt` → `MEASURE_JS` 直接能量出原语。
3. **可编辑契约**：组件引用令牌变量 → `render.py` 反查 `schemeClr` → 创作轨页也能一键换色（ppt-master 写死 HEX 做不到）。

---

## 8. 结构轨：版式模板库

保留并精修 `feature/svg2ppt` 的 Jinja2 模板（`ppt_engine/templates/*.j2`），改为**吃现场生成的令牌**而非固定主题。

### 8.1 模板即"受约束的好版面"
每个模板 = 一个把 IR `data` + 令牌组装成 HTML 的 Jinja2 文件，A 层纪律焊死在模板里（字阶/间距/网格/留白），叶子带 `data-ppt`。浏览器排版后由 §6 量出原语。智能体只填语义，排版稳。

### 8.2 v1 模板清单（≥12，已存在大部分）
`cover` · `toc` · `section` · `bullets` · `two_col` · `comparison` · `kpi` · `timeline` · `process` · `chart` · `quote` · `closing`（现有 11 个 j2 + 补全）。每个带容量预算（标题字数/条数上限），与 §5.2 `max_length` 对齐。

### 8.3 智能选版式
`plan_outline` 给每页标意图 → "意图→候选模板"表 + LLM 微调。选不到合适结构模板、或意图为表现型 → 升级到创作轨（§9）。

---

## 9. 创作轨：LLM 写 HTML/CSS

表现页（封面/章节/金句/主视觉/异形海报）在这里拿满 B 层天花板。

### 9.1 约束与提示词骨架
给 LLM 的系统提示包含：① 当前 `spec_lock`（令牌 + 母题清单）；② 套件可用 class 列表与用法；③ 硬规则（§5.3 可编辑性契约 + §7.4 纪律契约）；④ few-shot（一两个高质量 `custom` 页范例）。LLM 输出 `CustomData.html`——**只用套件 class 与令牌变量、组合母题、自由构图**，不写绝对坐标、不内联离板色/离阶字号。

### 9.2 为何比 ppt-master 手写 SVG 强
| | ppt-master（手写 SVG） | 本设计（写 HTML/CSS） |
|---|---|---|
| 坐标 | 模型目测，漂移 10–50px | 浏览器 CSS 算出，不越界 |
| 表达基座 | SVG 子集（禁 mask/style/...） | 完整 CSS（grid/flex/渐变/混合模式） |
| 作者友好度 | 低（绝对坐标） | 高（声明式，LLM 训练充分） |
| 可编辑 | 颜色写死 HEX | 令牌 → schemeClr 可换色 |
| 一致性 | spec_lock 文本提示 | 套件 class 物理约束 |

### 9.3 防滥用
创作轨只接表现型角色页 + `plan_outline` 低置信结构页。引擎记录创作轨占比；过高提示"该补结构模板"。创作轨页更依赖美学评论官（§12）。

---

## 10. 主题令牌与 spec_lock

颜值的可复用载体 + 跨页一致性的锚。v0.3：**spec_lock 是现场生成的**（非从固定主题库取），但**结构沿用 `theme.py`**。

### 10.1 令牌结构（沿用并扩展 `theme.py:Theme`）
现有 `Theme` 已含：`colors`（bg/surface/ink/muted/primary/primary-2/语义色…）、`display_font`/`body_font`、`chart_palette[6]`，并提供：
- `css_vars()` → 注入 §7.2 的 `:root`。
- `scheme()` → `clrScheme`（dk1/lt1/dk2/lt2/accent1–6）写入 `theme1.xml`，PowerPoint 可一键换肤。
- `color_slot()` → 反查表 `HEX → schemeClr`（tx1/bg1/tx2/bg2/accent1/accent2），供 `render` 发主题色引用。

v0.3 扩展：加 `type_scale`（比例 + 各档）、`grid`、`motifs`、`rules`，构成完整 `SpecLock`。

### 10.2 令牌 → OOXML 主题映射（保可编辑）
| 令牌 | OOXML | 可编辑收益 |
|---|---|---|
| `ink` / `bg-content` | `dk1` / `lt1` | 换主题全局换字色/底色 |
| `primary` / `primary-2` | `accent1` / `accent2` | 形状/图表引用，一键换色 |
| `chart_palette` | `accent1..6` | 原生图表自动取主题色 |
| `display_font` / `body_font` | `majorFont` / `minorFont` | 换主题字体全局生效 |

渲染**优先发主题色引用**而非写死 RGB（见 §11）。

### 10.3 spec_lock 纪律（借鉴 ppt-master）
身份生成并通过校验后，冻结成机器可读 `spec_lock`（单一真源）：① 两轨渲染都读它；② 创作轨 LLM 写 HTML 前必读它（只能用其中的色/字/字阶）；③ 长 deck 逐页重读，抗上下文压缩漂移；④ 改色后可批量传播到已生成页（类 ppt-master `update_spec.py`，但因走令牌变量更干净）。

### 10.4 预置主题（降为 seed / 兜底）
`theme.py` 现有 `EDITORIAL`（暖纸+思源宋体+朱砂）、`AURORA`（商务靛蓝）、`EMBER`（暖橙红）**作为可选 seed 与兜底**写入附录，**不再是默认锁定来源**。

---

## 11. 渲染器：原语 → 原生 DrawingML

两轨在此汇合，统一产出原生可编辑 DrawingML。**几乎照用 `feature/svg2ppt:ppt_engine/render.py`**。

### 11.1 原语 → python-pptx
| 原语 | python-pptx | 可编辑要点 |
|---|---|---|
| `text` | `add_textbox` + runs | 逐 run 设样式；字色优先 `theme_color`；中西文分别设 `latin`/`ea`（`_set_run_fonts`）；行距/字距/大写还原 |
| `rect` | `add_shape`（RECTANGLE / ROUNDED_RECTANGLE / OVAL） | 圆角 `radiusPx→adjustments`；渐变 `_set_gradient` 直写 OOXML；填充优先 schemeClr |
| `image` | `add_picture` | 按几何放置 |
| `icon` | `add_picture`（透明 PNG） | v1 高 DPI PNG；v2 可转矢量 |
| `chart` | `add_chart` + `CategoryChartData` | **原生图表对象**，可改数据；`_chart_transparent` 让底透出纸色；系列取 `chart_palette` |

层级用 `ZRANK`/`data-ppt-z` 排序（rect 底、text 顶）。

### 11.2 主题色还原（保一键换色，关键）
`render._clr_inner` 用 `theme.color_slot()` 把已知令牌 HEX 反查成 `<a:schemeClr val="accentN">`；未知色退化为 `<a:srgbClr>`（应已被 §5.3 校验拦下）。文本走 `TEXT_SLOT`（tx1/bg1/accent1…）→ `font.color.theme_color`。这是创作轨也能换肤、优于 ppt-master 的根本。

### 11.3 主题与母版
`oox_theme.inject_theme` 按 `scheme()` 写 `theme1.xml` + slide master；`embed_fonts` 子集化并嵌入思源字体（生成身份选了别的字体则补嵌，见 `fonts.py`/`embed_fonts.py`）。渐变/阴影等 python-pptx 不直接支持的，`shape._element` 直写 OOXML 补齐（render 已有 helper）。

---

## 12. 递归评论官闭环

放弃确定性后的**地板机制**。分身份层（§4.3 已述）与页面层两级。

### 12.1 页面评论官（⑥）
```
生成(模板/LLM HTML) → 浏览器排版 → 量原语 + 截图 PNG
  → 结构评论官(机器，零模型，读原语)
  → 美学评论官(视觉模型，读 PNG)
  → 违反 QUALITY rubric? → 带具体违规项重生成 → 循环 ≤N 轮 → 通过
```

- **结构评论官（廉价，多从已测原语直接算）**：越界（叶子超安全区？）、重叠（同层叶子相交？）、对比度（WCAG，从 computed color 算）、字阶合规（所有 fontSizePx ∈ 锁定字阶？）、留白比（内容包围盒/画布）、网格对齐（吸附容差）、跨页配色/字体一致（颜色 ∈ 令牌集？字体 ∈ 锁定字族？）。
- **美学评论官（视觉模型读截图）**，结构化输出：
  ```json
  { "hierarchy_ok": true, "balance_ok": true, "contrast_ok": true,
    "art_direction_score": 0.0, "issues": [], "suggested_fix": null }
  ```
  结构轨主要靠结构评论官；创作轨更依赖美学评论官。

### 12.2 修复策略
- 结构问题 → 结构轨触发自适应阶梯（降字号档→收行高→截最低优先级→拆页→换模板）；创作轨回传违规项让 LLM 改 HTML。
- 美学问题 → 创作轨调构图/母题；结构轨换模板或调令牌前景色。
- 重生成 ≤N 轮仍失败 → 结构轨降级到安全模板（bullets）并告警；创作轨降级到结构轨同角色模板。

### 12.3 与确定性的关系
不变量断言改为**作用于"已测原语"**（浏览器算出的真实几何），而非"求解器输出"。因此即便排版非确定，"零越界/零重叠/字号∈字阶/颜色∈令牌"仍可机器断言——**地板可证**。

---

## 13. 智能体接入（MCP）

以 MCP Server 暴露工具，描述内嵌 schema + few-shot，任何 LLM 可驱动。

| 工具 | 签名 | 说明 |
|---|---|---|
| `plan_outline` | `(topic, audience, n?) -> Outline` | 叙事大纲 + 每页角色/意图（驱动路由） |
| `art_direct` | `(brief) -> SpecLockCandidate` | **身份生成**：为主题发明设计语言（§4） |
| `lock_spec` | `(candidate) -> SpecLock` | 经身份评论官校验后冻结为单一真源 |
| `list_layouts` | `() -> {role, when_to_use, data_schema}[]` | 结构轨版式菜单 + 各 schema（含 custom 用法/约束） |
| `validate_ir` | `(ir) -> {valid, errors[]}` | 校验 + 字数预算 + 创作轨可编辑性约束 |
| `render_preview` | `(ir, idx?) -> image[]` | 浏览器预览 + 点选批注（反馈通道） |
| `critique` | `(ir, idx?) -> Report` | 跑页面评论官（结构 + 美学），返回违规项 |
| `export_pptx` | `(ir, out) -> file` | 导出原生可编辑 pptx |

**推荐工作流**：`plan_outline → art_direct → lock_spec →（逐页：路由→选模板填 data / 写 custom HTML→validate）→ critique 收敛 →（可选 render_preview 人审）→ export_pptx`。

---

## 14. 质量保障与验收

### 14.1 三类自动检查
- **身份层校验**（身份评论官）：生成令牌过 `QUALITY.md` 身份层 rubric。
- **结构不变量断言**（作用于已测原语，无需视觉模型，快）：零越界/零重叠/字号∈字阶/颜色∈令牌/对比达标。改引擎/模板时第一道回归网。
- **rubric 通过率**（替代失效的黄金图 SSIM）：固定一组 brief，统计页面评论官通过率与重生成轮次，作为质量趋势指标。

### 14.2 端到端验收（成功判据落地）
给定主题，智能体 ≤2 轮评论官内出 10–15 页 deck，断言：
1. 身份评论官：字阶模块化、配色 60-30-10、对比达标。
2. 结构评论官：零越界/零重叠/字号∈字阶/颜色∈令牌。
3. 美学评论官：层级/平衡/设计感达阈值。
4. PowerPoint 打开：文字可改、一键换主题色、图表可改数据、字体已嵌。
5. 创作轨页与结构轨页**身份一致**（同 spec_lock）。

### 14.3 两个评审基准（见 `QUALITY.md`）
- **B 层天花板基准**：ppt-master「Indie Bookstore Zine Guide」**作为基准而非模板**——验证能否现场生成一套同样贴合、同样惊艳、但可编辑且过 A 层的 Riso 语言。
- **A 层基准**：企业增长复盘——验证结构轨零溢出、跨页一致。

---

## 15. 工程结构 · 路线图 · 风险

### 15.1 目录
```
ppt-tool/
  pyproject.toml
  docs/  DESIGN.md  QUALITY.md
  ppt_engine/
    artdirect/      # 艺术总监 + 身份评论官（§4）  director.py  identity_critic.py
    ir.py           # pydantic IR（结构轨 data + custom；字数预算；校验）
    spec.py         # SpecLock 生成式令牌（演进 theme.py）  + seed 主题  + speclock 序列化
    kit/            # 设计系统套件（§7）  base.html.j2(骨架)  tokens.css.j2  motifs.py
    templates/      # 结构轨版式 j2（§8，沿用 svg2ppt）
    build.py        # 浏览器编排管线（沿用 svg2ppt，接评论官）
    measure.py      # MEASURE_JS 抽取契约（沿用 + 扩字段）
    render.py       # 原语→原生 DrawingML（沿用 svg2ppt）
    oox_theme.py embed_fonts.py fonts.py units.py icons.py   # 沿用
    critic/         # 页面评论官（§12）  structural.py  aesthetic.py  repair.py
    assets/fonts/   # 思源黑体+宋体（沿用）
  ppt_mcp/server.py # §13
  tests/  test_invariants.py(已测原语)  test_e2e.py
```

### 15.2 技术栈
| 用途 | 选型 |
|---|---|
| IR 校验 | pydantic v2 |
| 排版基座 | Playwright（无头 Chrome）+ Jinja2 |
| OOXML | python-pptx（+ `_element` 直写补效果） |
| 字体 | fontTools（子集/嵌入）+ 思源黑体/宋体 |
| 评论官-结构 | 纯 Python（读已测原语） |
| 评论官-美学/艺术总监 | 多模态 LLM |
| 预览/人审 | 浏览器（HTML）+ 点选批注 |
| MCP | mcp（官方 SDK） |
| 测试 | pytest |

### 15.3 路线图
| 阶段 | 目标 | 交付 |
|---|---|---|
| **P0 脊柱** | 移植 svg2ppt 浏览器管线进新分支；结构轨跑通 5 模板 + 一套 seed 令牌 | 「IR 进 / 原生可编辑 pptx 出」 |
| **P1 评论官地板** | 结构评论官 + `QUALITY.md` 页面层 | 结构轨自动卡 A 层，零溢出可断言 |
| **P2 身份生成** | 艺术总监层 + 身份评论官 + `QUALITY.md` 身份层 + 套件实例化 | 给定主题现场生成过 A 层校验的设计语言 |
| **P3 创作轨** | `custom` 页 + LLM 写 HTML/CSS + 美学评论官 + 重生成循环 | 封面/主视觉达 B 层水准（Riso 级） |
| **P4 路由与一致** | `plan_outline` 角色路由 + 跨页 spec_lock 抗漂移 + 图像统一处理 | 整 deck 双轨混排、身份统一 |
| **P5 产品化** | MCP 全量 + 多 seed 主题 + 浏览器预览批注 + 品牌套件 | 智能体端到端商用 |

### 15.4 风险与权衡
| 风险 | 缓解 |
|---|---|
| Playwright/Chromium 依赖（部署/CI 重） | 已被 svg2ppt 验证；容器内置 Chromium；接受为基座代价 |
| **信任 LLM 发明设计系统**（freedom 核心风险） | 身份评论官递归卡 A 层；seed 主题兜底；母题须引用令牌 |
| 评论官循环 → 成本/延迟上升 | 角色路由控创作轨占比；结构评论官零模型；重生成 ≤N 轮封顶 |
| 浏览器渲染 ≠ PowerPoint（字体度量） | 几何以浏览器为准 + render 已有 wrap slack；嵌字统一度量 |
| 美学评论官主观/不稳定 | 可机器判定项尽量前移到结构/身份评论官；美学层只判 rubric 明列项 |
| 创作轨非确定 → 无黄金图回归 | 结构不变量（已测原语）+ rubric 通过率替代像素对标 |
| 创作轨 LLM 越护栏（离阶/离板） | 套件只暴露合规槽位 + 结构评论官硬卡 + 校验期拦截 |
| 生成母题破坏可编辑/可测 | 母题强制带 data-ppt + 引用令牌变量，纳入抽取与换色契约 |

---

*评审关注点：① 身份生成 + 身份评论官能否稳定产出过 A 层的设计语言；② 设计系统套件三契约能否同时守住纪律/抽取/可编辑；③ 创作轨"写 HTML/CSS"对 LLM 的实际可控度；④ 评论官重生成轮次的成本上界；⑤ 放弃确定性后，"已测原语断言 + rubric 通过率"是否足以替代回归。*
