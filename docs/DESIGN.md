# AI 可编辑 PPT 生成工具 · 设计文档

> 版本：v0.1（草案）  日期：2026-06-26  状态：待评审
>
> 一句话定位：智能体输入语义结构，引擎产出**原生可编辑、设计感强、稳定不崩**的 `.pptx`。

---

## 目录

1. [目标与边界](#1-目标与边界)
2. [核心设计原则](#2-核心设计原则)
3. [整体架构](#3-整体架构)
4. [IR 中间表示](#4-ir-中间表示)
5. [盒模型排版引擎（核心 IP）](#5-盒模型排版引擎核心-ip)
6. [版式原型库](#6-版式原型库)
7. [主题与设计令牌系统](#7-主题与设计令牌系统)
8. [文本度量与自适应](#8-文本度量与自适应)
9. [渲染器（python-pptx）](#9-渲染器python-pptx)
10. [渲染-自检-修复闭环](#10-渲染-自检-修复闭环)
11. [智能体接入（MCP）](#11-智能体接入mcp)
12. [质量保障与黄金测试](#12-质量保障与黄金测试)
13. [工程结构与技术栈](#13-工程结构与技术栈)
14. [里程碑路线图](#14-里程碑路线图)
15. [风险与权衡](#15-风险与权衡)

---

## 1. 目标与边界

### 1.1 目标
- **高颜值**：产出看起来"被设计过"，而非 python-pptx 直糊的呆板版面。
- **可编辑**：原生 `.pptx`，能在 PowerPoint / WPS / Keynote 里继续编辑；文字是文本框、形状是矢量、图表是原生图表对象、配色走主题。
- **稳定产出**：智能体接入后每次都不溢出、不重叠、可复现、可回归。
- **通用**：覆盖商业汇报、课件、营销、BP 等大多数内容形态。

### 1.2 非目标（v1 不做）
- 不做网页在线编辑器（用户在 PowerPoint/WPS 里编辑）。
- 不做动画/转场（保留 notes 字段，后续扩展）。
- 不做 PPTX 反向解析/导入（只生成不读取）。
- 不追求与 PowerPoint 像素级一致的渲染预览（预览仅用于自检）。

### 1.3 成功判据
- 给定一个主题，智能体在 ≤2 轮自检内产出 10-15 页 deck，**零溢出/零重叠**。
- 产出的 pptx 在 PowerPoint 中打开：文字可改、可一键换主题色、图表可改数据。
- 同一份 IR 多次渲染结果**字节级/版面级一致**（确定性）。

---

## 2. 核心设计原则

1. **LLM 产出语义，不产出像素。** 智能体只选版式 + 填语义槽位，绝不写坐标、字号、颜色。所有视觉决策由引擎确定性完成。
2. **颜值固化进设计系统。** 版式原型库 + 主题令牌由人设计好；AI 不需要"有审美"。
3. **稳定来自约束 + 校验 + 自检。** 受约束的 IR（枚举 + 字数预算）→ Schema 校验 → 渲染自检修复，三道闸。
4. **可编辑是第一公民。** 优先用主题色引用、原生形状、原生图表；能让用户改的绝不烤成图片。
5. **确定性优先。** 同输入同输出；排版无随机；所有"智能"都在 IR 生成那一层，引擎本身是纯函数。

---

## 3. 整体架构

```
┌──────────────────────────────────────────────────────────────────┐
│  智能体 (Claude / 其他 LLM)                                         │
│     │  MCP 工具调用                                                 │
├─────▼────────────────────────────────────────────────────────────┤
│  MCP Server (ppt_mcp)                                               │
│   list_layouts · list_themes · plan_outline · validate_ir          │
│   · render_preview · export_pptx                                   │
├──────────────────────────────────────────────────────────────────┤
│  核心引擎 (Python · 纯函数 · 确定性)                                │
│                                                                    │
│   IR 层 ──────────→ 排版引擎 ──────────→ 渲染器                     │
│   pydantic 模型      盒模型求解器          python-pptx              │
│   字数预算/校验      版式原型库            → 原生 .pptx              │
│                     文本度量                                        │
│                     主题/令牌→OOXML 主题                            │
│                                                                    │
│   ┌────────────────────────────────────────────────────────────┐  │
│   │ 自检闭环：LibreOffice 渲染图 → 视觉评审 → 修复 IR → 重渲       │  │
│   └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

数据流：`内容/大纲 → IR(JSON) → 校验 → 盒树(Box Tree) → 求解(绝对 EMU) → 定位原语 → python-pptx → .pptx → [自检图 → 修复]`

---

## 4. IR 中间表示

IR 是智能体与引擎之间的契约。两层：`Deck` 和 `Slide`。用 **pydantic v2** 建模与校验。

### 4.1 顶层结构

```python
class DeckMeta(BaseModel):
    title: str
    lang: Literal["zh", "en"] = "zh"
    aspect: Literal["16:9", "4:3"] = "16:9"

class Deck(BaseModel):
    meta: DeckMeta
    theme: str                      # 主题 id，对应主题库
    slides: list[Slide]             # 每页一个 Slide

class Slide(BaseModel):
    layout: LayoutId                # 版式原型枚举
    data: LayoutData                # 受 layout 约束的判别联合体
    notes: str | None = None        # 演讲者备注
    emphasis: int = 0               # 该页重要度(影响留白/字号策略)
```

### 4.2 判别联合体（Discriminated Union）

`data` 的形状由 `layout` 决定，每个版式有独立的数据模型与校验。这是稳定性的关键：智能体在"点菜 + 填空"。

```python
class BulletItem(BaseModel):
    text: str = Field(max_length=80)        # 字数预算：单条 ≤80
    level: Literal[0, 1] = 0                 # 仅两级缩进
    emphasis: bool = False

class BulletsData(BaseModel):
    kind: Literal["bullets"]
    title: str = Field(max_length=40)
    bullets: list[BulletItem] = Field(max_length=6)   # ≤6 条
    media: Media | None = None               # 可选配图

class ComparisonData(BaseModel):
    kind: Literal["comparison"]
    title: str = Field(max_length=40)
    left:  Column                            # {heading, points[]}
    right: Column

class KpiData(BaseModel):
    kind: Literal["kpi"]
    title: str = Field(max_length=40)
    stats: list[Stat] = Field(min_length=2, max_length=4)  # {value,label,delta?}

class ChartData(BaseModel):
    kind: Literal["chart"]
    title: str = Field(max_length=40)
    chart_type: Literal["bar", "line", "pie", "column"]
    series: list[Series]                     # 原生图表数据
    # ... 其余版式

LayoutData = Annotated[
    Union[BulletsData, ComparisonData, KpiData, ChartData, ...],
    Field(discriminator="kind"),
]
```

### 4.3 字数预算（第一道稳定闸）

每个文本槽位都带 `max_length`，并按版式定义**条数上限**。这让"文字溢出"在生成端就被挡住，而不是等排版时救火。预算值由各版式经验标定（见 §6 每个原型的容量表）。

校验失败的处理：`validate_ir` 返回结构化错误，智能体据此收敛内容重试。

### 4.4 样式覆盖（受限）
不开放自由样式。仅允许极少量语义级覆盖（如 `emphasis`、`media.focal_point`），杜绝智能体写死颜色/坐标。

---

## 5. 盒模型排版引擎（核心 IP）

PPTX 用 EMU 绝对定位（`914400 EMU/英寸`；16:9 画布 = `12192000 × 6858000 EMU`），**没有 flexbox**。引擎自研一个迷你盒模型，把声明式盒树解算成绝对坐标。这是产品区别于"硬糊"的根本。

### 5.1 坐标与单位
- 内部统一用 **EMU** 计算，避免多次换算误差。
- 提供 `pt → EMU`（×12700）、`px@96dpi → EMU`（×9525）辅助。
- 画布定义安全区（margin），所有内容在安全区内布局。

### 5.2 盒类型

| 盒 | 作用 |
|----|------|
| `Frame` | 画布根，带 margin/安全区 |
| `Stack` | 纵向排列子盒 |
| `Row` | 横向排列子盒 |
| `Grid` | 等分网格（KPI 墙、矩阵） |
| `Leaf` | 叶子：`Text` / `Image` / `Shape` / `Chart` / `Icon` |

### 5.3 盒属性（类 flexbox 子集）

```python
class Box:
    size: Size          # 主轴尺寸：Fixed(emu) | Flex(weight) | Hug(随内容)
    gap: int            # 子盒间距
    padding: Edges      # 内边距
    main_align: Align   # 主轴: start|center|end|space-between
    cross_align: Align  # 交叉轴: start|center|end|stretch
    children: list[Box]
```

### 5.4 两遍求解算法（仿 flexbox）

**Pass 1 · 度量（intrinsic size，自底向上）**
- `Leaf.Text` → 调 §8 文本度量，按给定宽度求换行后高度。
- `Leaf.Image` → 按宽高比求尺寸。
- 容器把子盒 intrinsic 尺寸按 gap/padding 聚合，得到自身 `Hug` 尺寸。

**Pass 2 · 布局（resolve，自顶向下）**
- 容器拿到可用矩形，先扣除 `Fixed`/`Hug` 子盒占用，剩余空间按 `Flex` 权重分配。
- 按 `main_align`/`cross_align` 定位每个子盒，递归下发矩形。
- 叶子最终落到绝对 `(x, y, w, h)`。

**输出**：扁平的定位原语列表，渲染器直接消费：
```python
@dataclass
class Primitive:
    kind: Literal["text", "image", "shape", "chart", "icon"]
    x: int; y: int; w: int; h: int     # 绝对 EMU
    style: ResolvedStyle               # 已解出的具体字体/色/对齐
    content: Any
```

### 5.5 不变量（供测试断言，见 §12）
- 所有原语在画布安全区内：`x≥margin ∧ x+w≤W-margin`，y 同理。
- 同层叶子不重叠（除非显式 overlay）。
- 文本原语的 `h` ≥ 其度量高度（不溢出）。

> 求解器是**纯函数**：`(BoxTree) → list[Primitive]`，无随机、无 IO，可单测、可缓存。

---

## 6. 版式原型库

通用工具的命脉。**原型 = 把 IR 的 `data` + `theme` 组装成盒树的声明**——不写死坐标，由求解器定位，因此天然随内容/主题自适应。

### 6.1 原型即盒树（示例）

```python
class BulletsArchetype(Archetype):
    id = "bullets"
    schema = BulletsData

    def build(self, d: BulletsData, t: Theme) -> Box:
        body = Stack(size=Flex(1), gap=t.space.md, children=[
            Bullet(b, style=t.type.body) for b in d.bullets
        ])
        content = (
            Row(gap=t.space.xl, children=[body, Image(d.media, size=Flex(1))])
            if d.media else body
        )
        return Frame(padding=t.slide_margin, children=[
            Stack(gap=t.space.lg, children=[
                Text(d.title, style=t.type.h1),
                Rule(color=t.color.accent),          # 标题下的装饰线
                content,
            ])
        ])
```

换主题、换内容，版面自动重排且始终对齐——颜值与稳定同时拿到。

### 6.2 v1 原型清单（≥16）与容量表

| id | 名称 | 主槽位 | 容量预算 |
|----|------|--------|---------|
| `cover` | 封面 | 标题/副标题/作者 | 标题≤24 字 |
| `toc` | 目录 | 章节列表 | ≤8 项 |
| `section` | 章节分隔 | 章节标题/序号 | ≤16 字 |
| `bullets` | 要点列表 | 标题 + 要点 | ≤6 条/条≤80 字 |
| `two_col` | 两栏 | 左右两块 | 各≤4 条 |
| `comparison` | 左右对比 | VS 两列 | 各≤5 条 |
| `kpi` | 数字墙 | 2-4 个指标 | value≤8 字 |
| `timeline` | 时间线 | 节点序列 | ≤5 节点 |
| `process` | 流程 | 步骤箭头 | ≤5 步 |
| `quote` | 引用金句 | 金句 + 出处 | ≤60 字 |
| `image_full` | 大图全屏 | 配图 + 叠字 | 叠字≤20 字 |
| `image_text` | 图文混排 | 图 + 段落 | 段落≤180 字 |
| `chart` | 图表页 | 原生图表 | ≤6 系列 |
| `matrix` | 2×2 矩阵 | 四象限 | 各≤30 字 |
| `table` | 表格 | 行列数据 | ≤6 行×5 列 |
| `team` | 团队/人物 | 头像 + 简介 | ≤6 人 |
| `closing` | 结尾页 | 致谢/联系方式 | — |

### 6.3 智能选版式
两段式生成（见 §11）中，`plan_outline` 给每页标注**内容意图**（list/compare/process/data/statement…），引擎按"意图→候选原型"表 + LLM 微调选定。规则优先，LLM 兜底。

---

## 7. 主题与设计令牌系统

颜值的可复用载体。令牌定义一次，落到 OOXML 主题（slide master），全 deck 一致，且用户可在 PowerPoint 里一键换主题。

### 7.1 令牌结构

```python
class Theme(BaseModel):
    id: str; name: str
    color: ColorTokens     # bg, surface, primary, secondary, accent,
                           # text, text_muted, chart_palette[6]
    type:  TypeScale       # h1/h2/h3/body/caption: {font,size,weight,
                           #   line_height,letter_spacing,color}
    space: SpaceScale      # xs..xxl 间距阶梯(8pt 网格)
    slide_margin: int
    radius: int; rule_weight: int
```

### 7.2 令牌 → OOXML 主题映射

| 令牌 | OOXML 目标 | 可编辑收益 |
|------|-----------|-----------|
| `color.text` | `a:clrScheme/dk1` | 用户换主题即全局换字色 |
| `color.bg` | `a:clrScheme/lt1` | 同上 |
| `color.primary` | `accent1` | 形状/图表引用，可一键换色 |
| `color.accent` | `accent2` | 装饰线/强调 |
| `chart_palette` | `accent1..6` | 原生图表自动取主题色 |
| `type.h1.font` | `a:fontScheme/majorFont` | 用户改主题字体即全局生效 |
| `type.body.font` | `minorFont` | 同上 |

引擎在生成 deck 时，由令牌**程序化生成 slide master + theme XML**，每页引用对应版式布局。渲染原语时**优先用主题色引用**（`fill.fore_color.theme_color = MSO_THEME_COLOR.ACCENT_1`）而非写死 RGB，保住"换色"能力。

### 7.3 v1 主题
内置 3-4 套：`corporate`（商务蓝）、`minimal`（极简黑白）、`vibrant`（活力撞色）、`academic`（学术稳重）。每套 = 一组令牌值。

---

## 8. 文本度量与自适应

PPTX 生成时拿不到渲染引擎，必须自己度量文本，否则必溢出。

### 8.1 度量模块
```python
def measure_text(text, font_path, size_pt, max_width_emu,
                 line_height) -> TextMetrics:   # → (w, h, lines)
```
- 用 **fontTools** 加载字体，取字形 advance width；按 `max_width` 做贪心断行。
- **CJK 处理**：中文逐字可断；拉丁按空格断；中英混排分别处理。通用工具必须把中文断行做对。
- 行高 = `size × line_height`，总高 = 行数 × 行高。
- 用 LRU 缓存（字体+字号+文本→度量）提速。

### 8.2 自适应阶梯（内容超框时按序尝试）
1. 在排版字阶内**降一档字号**（body 可降，h1 不降）。
2. 收紧 line-height / 段距（有下限）。
3. **按优先级截断**最低优先级内容（加省略号）；优先级来自 schema。
4. **回流拆页**：bullets 类超量 → 拆成"续页"。
5. **切换原型**：如 `bullets` → `two_col`（两栏装更多）。
6. **终极兜底**：对该文本框开启 PowerPoint autofit（`MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE`），打开时自动缩字。

> 但 90% 的溢出应被 §4.3 字数预算挡在生成端；自适应是安全网，不是主力。

---

## 9. 渲染器（python-pptx）

把定位原语翻译成 python-pptx 调用，产出原生可编辑 `.pptx`。

### 9.1 原语 → python-pptx 映射

| 原语 | python-pptx | 可编辑性要点 |
|------|-------------|-------------|
| `text` | `add_textbox` + runs | 逐 run 设样式；字色尽量用 theme_color |
| `shape` | `add_shape(MSO_SHAPE.*)` | 填充用 `theme_color`；圆角/线条走令牌 |
| `image` | `add_picture` | 按 focal_point 裁剪定位 |
| `chart` | `add_chart(XL_CHART_TYPE, CategoryChartData)` | **原生图表对象**，用户可改数据 |
| `icon` | SVG→PNG(`cairosvg`) 或 freeform | v1 用高 DPI PNG；v2 转 freeform 保矢量 |

### 9.2 主题与母版
- 每个 deck 先按 §7 生成 theme.xml + slide master + 各版式 layout。
- 渐变/阴影等 python-pptx 不直接支持的效果，通过 `shape._element` 直写 OOXML 补齐（封装成 helper）。

### 9.3 备注与元信息
`Slide.notes` → notes slide；deck 标题/语言写入 core properties。

### 9.4 确定性
渲染器无随机、无时间戳；图片按内容哈希命名嵌入，保证同 IR → 同 pptx。

---

## 10. 渲染-自检-修复闭环

从"能用"到"稳定"的关键一跳。可开关（增加延迟与视觉模型调用成本）。

```
IR → 渲染 .pptx → LibreOffice 转图(每页一张 PNG)
   → 视觉模型结构化评审 → 有问题? → 修复 IR → 重渲(≤2 轮)
```

### 10.1 渲染成图
`soffice --headless --convert-to pdf deck.pptx` → `pdf2image` 转 PNG（每页一张）。需在运行环境安装 LibreOffice 与对应字体。

### 10.2 结构化评审
把每页 PNG + 该页 IR 意图喂给视觉模型，要求结构化输出：
```json
{ "overflow": false, "overlap": false, "contrast_ok": true,
  "hierarchy_ok": true, "balance_ok": true,
  "issues": [], "suggested_fix": null }
```

### 10.3 修复策略
问题 → IR 调整：溢出→触发 §8 阶梯 / 减内容；失衡→换原型；对比差→换主题前景色。重渲，最多 2 轮，仍失败则降级到"安全原型"（bullets）并标记告警。

### 10.4 双重保险
注意 §5.5 的**结构不变量**可在**无需出图**的情况下直接断言（越界/重叠/溢出），是廉价的第一层自检；视觉模型负责"美学层"问题。两层叠加。

---

## 11. 智能体接入（MCP）

以 MCP Server 暴露工具；工具描述内嵌 schema + few-shot，任何 LLM 都能驱动。

### 11.1 工具集

| 工具 | 签名 | 说明 |
|------|------|------|
| `list_themes` | `() -> Theme[]` | 可选主题 |
| `list_layouts` | `() -> {id, when_to_use, data_schema}[]` | 版式菜单 + 各自 schema |
| `plan_outline` | `(topic, audience, n_slides?, style?) -> Outline` | 出叙事大纲 + 每页意图 |
| `validate_ir` | `(ir) -> {valid, errors[]}` | 校验 + 字数预算检查 |
| `render_preview` | `(ir, slide_index?) -> image[]` | **反馈通道**：返回渲染图供自检 |
| `export_pptx` | `(ir, out_path) -> file` | 导出可编辑 pptx |

### 11.2 推荐生成工作流（两段式）
```
1. plan_outline(topic)            # 先定叙事，别一口气全生成
2. 逐页：选 layout + 填 data（守字数预算）→ 组装 Deck IR
3. validate_ir → 按 errors 收敛重试
4. (可选) render_preview → 视觉自检 → 修复
5. export_pptx
```

### 11.3 给智能体的契约要点
- 工具描述里给**每个版式的 data 示例**（few-shot），降低跑偏。
- 校验错误必须**可执行**（"bullets[3].text 82>80 字，请精简"），让智能体能直接改。
- `render_preview` 返回图，构成自我纠错闭环。

---

## 12. 质量保障与黄金测试

### 12.1 结构不变量测试（无需出图，快）
对一批 IR fixtures 跑求解器，断言 §5.5 不变量：无越界、无重叠、文本不溢出。改引擎/原型时第一道回归网。

### 12.2 黄金图回归（出图，慢）
固定 IR → 渲染 PNG → 与已批准基准图做感知差异（如 SSIM / 像素阈值）。版面跑偏即报警。

### 12.3 智能体端到端冒烟
固定若干 topic → 全流程跑 → 断言"零溢出 + 页数合理 + 可打开"。

### 12.4 CI
PR 跑 12.1 + 12.3；12.2 因依赖 LibreOffice/字体，单独 job。

---

## 13. 工程结构与技术栈

### 13.1 目录
```
ppt-tool/
  pyproject.toml
  ppt_engine/
    ir/            # pydantic 模型、判别联合、字数预算、校验
      models.py
      layouts.py
    layout/        # 盒模型求解器
      box.py  solver.py  measure.py
    archetypes/    # 版式原型库
      base.py  cover.py  bullets.py  comparison.py  kpi.py  chart.py ...
    theme/         # 设计令牌 + OOXML 主题/母版生成
      tokens.py  master.py  themes/
    render/        # python-pptx 渲染器
      renderer.py  text.py  shape.py  chart.py  image.py  icon.py
    selfcheck/     # libreoffice 出图 + 视觉评审 + 修复
      to_image.py  critique.py  repair.py
    assets/        # 字体、图标、占位图
  ppt_mcp/
    server.py      # MCP Server
  tests/
    fixtures/  golden/  test_invariants.py  test_e2e.py
  docs/
    DESIGN.md
```

### 13.2 依赖
| 用途 | 选型 |
|------|------|
| IR 校验 | pydantic v2 |
| OOXML 底层 | python-pptx |
| 文本度量 | fontTools + Pillow |
| 图标矢量 | cairosvg（SVG→PNG） |
| 自检出图 | LibreOffice（系统级）+ pdf2image |
| MCP | mcp（官方 Python SDK） |
| 测试 | pytest + scikit-image（SSIM） |
| 高保真度量（可选） | Playwright |

---

## 14. 里程碑路线图

| 阶段 | 目标 | 交付 |
|------|------|------|
| **P0 脊柱** | IR Schema + 盒模型求解器 + 1 主题 + 5 原型 + 渲染器跑通 | "IR 进 / 可编辑 pptx 出"的 demo |
| **P1 可用** | 扩到 16 原型 + 3 主题 + 字数预算/文本度量 + MCP 接入 | 智能体可端到端出 deck |
| **P2 稳定** | 结构不变量测试 + LibreOffice 自检闭环 + 黄金回归 | 零溢出/可回归 |
| **P3 颜值深化** | 原生图表 + 图标/配图 + 智能选版式 + 更多主题 | 接近商用观感 |
| **P4 扩展** | 矢量图标(freeform) + 渐变效果 + 品牌套件 + 多语言 | 产品化 |

---

## 15. 风险与权衡

| 风险 | 影响 | 缓解 |
|------|------|------|
| python-pptx 不支持渐变/部分效果 | 颜值上限受限 | 封装 `_element` 直写 OOXML helper |
| **LibreOffice 渲染 ≠ PowerPoint**（尤其字体） | 自检图与真实有偏差 | 统一字体管理；自检以"溢出/重叠"等结构问题为主，美学为辅 |
| CJK 文本度量精度 | 中文断行/高度估算偏差 | fontTools 实测 + 留安全余量 + autofit 兜底 |
| 图标/SVG 矢量保真 | v1 用 PNG 损失可缩放 | v2 SVG→freeform |
| 主题色引用 vs 写死色 | 引用色更可编辑但部分场景需精确色 | 默认引用，allow 列表内可写死 |
| 原型库覆盖不足 | 某些内容无合适版式 | 选版式器兜底到 `bullets`，并记录缺口驱动迭代 |

---

## 附录 A · 端到端示例（伪）

```python
ir = Deck(
    meta=DeckMeta(title="2026 增长复盘", lang="zh"),
    theme="corporate",
    slides=[
        Slide(layout="cover", data=CoverData(kind="cover",
              title="2026 增长复盘", subtitle="增长团队 · Q2")),
        Slide(layout="kpi", data=KpiData(kind="kpi", title="核心指标",
              stats=[Stat(value="+42%", label="GMV"),
                     Stat(value="1.2M", label="MAU"),
                     Stat(value="3.8%", label="转化率")])),
        Slide(layout="bullets", data=BulletsData(kind="bullets",
              title="增长抓手", bullets=[
                  BulletItem(text="渠道组合优化，CAC 下降 18%"),
                  BulletItem(text="新用户首日留存提升至 55%"),
              ])),
    ],
)
errors = validate_ir(ir)            # []
export_pptx(ir, "growth.pptx")      # → 原生可编辑 pptx
```

---

*评审关注点：① IR 是否够约束又够表达；② 盒模型是否覆盖所有原型的排版需求；③ 主题→OOXML 映射的可编辑收益；④ 自检闭环的成本/收益。*
