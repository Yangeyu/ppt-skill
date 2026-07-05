"""IR — the contract between the LLM and the engine.

Discriminated union on `kind`: each archetype has its own schema + word
budgets, so overflow is rejected at generation time, not patched at layout."""
from __future__ import annotations
from typing import Literal, Annotated, Union
from pydantic import BaseModel, Field


# ---- leaf pieces ---------------------------------------------------------
class Stat(BaseModel):
    value: str = Field(max_length=8)        # e.g. "+42%", "1.2M"
    label: str = Field(max_length=16)
    delta: str | None = Field(default=None, max_length=12)
    delta_dir: Literal["up", "down", "flat"] = "flat"


class Bullet(BaseModel):
    text: str = Field(max_length=80)
    emphasis: bool = False


class Series(BaseModel):
    name: str = Field(max_length=20)
    values: list[float]


# ---- per-archetype data --------------------------------------------------
class CoverData(BaseModel):
    kind: Literal["cover"] = "cover"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=28)
    subtitle: str = Field(default="", max_length=48)
    footer: str = Field(default="", max_length=48)


class HeroFact(BaseModel):
    """One big-number fact on a hero page (fact-strip, Jimbocho style)."""
    value: str = Field(max_length=10)
    label: str = Field(max_length=16)


class HeroData(BaseModel):
    """Full-bleed image-mode page: a look-treated picture + overlaid native type."""
    kind: Literal["hero"] = "hero"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=28)
    subtitle: str = Field(default="", max_length=48)
    footer: str = Field(default="", max_length=48)
    art: str = Field(default="sun", max_length=16)     # procedural fallback: sun | city | shanghai | vanity | …
    src: str = Field(default="", max_length=240)        # optional source image to re-ink
    prompt: str = Field(default="", max_length=300)     # t2i content prompt (the look enforces style)
    facts: list[HeroFact] = Field(default_factory=list, max_length=3)


class SectionData(BaseModel):
    kind: Literal["section"] = "section"
    number: str = Field(default="", max_length=4)
    title: str = Field(max_length=20)
    subtitle: str = Field(default="", max_length=40)


class KpiData(BaseModel):
    kind: Literal["kpi"] = "kpi"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    stats: list[Stat] = Field(min_length=2, max_length=4)
    so_what: str = Field(default="", max_length=60)     # 咨询式结论条(look 可选渲染)


class BulletsData(BaseModel):
    kind: Literal["bullets"] = "bullets"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    bullets: list[Bullet] = Field(min_length=1, max_length=6)
    so_what: str = Field(default="", max_length=60)


class ChartData(BaseModel):
    kind: Literal["chart"] = "chart"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    chart_type: Literal["column", "bar", "line"] = "column"
    categories: list[str]
    series: list[Series] = Field(min_length=1, max_length=4)
    takeaway: str = Field(default="", max_length=60)


Point = Annotated[str, Field(max_length=60)]


class TocItem(BaseModel):
    title: str = Field(max_length=24)
    desc: str = Field(default="", max_length=32)        # one-line summary under the title
    pages: str = Field(default="", max_length=10)       # page-range chip, e.g. "P03–P04"


class TocData(BaseModel):
    kind: Literal["toc"] = "toc"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(default="目录", max_length=24)
    items: list[TocItem] = Field(min_length=2, max_length=8)


class Column(BaseModel):
    heading: str = Field(max_length=24)
    points: list[Point] = Field(min_length=1, max_length=5)


class TwoColData(BaseModel):
    kind: Literal["two_col"] = "two_col"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    left: Column
    right: Column
    so_what: str = Field(default="", max_length=60)


class CompareData(BaseModel):
    kind: Literal["comparison"] = "comparison"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    left: Column
    right: Column
    so_what: str = Field(default="", max_length=60)


class Step(BaseModel):
    title: str = Field(max_length=16)
    desc: str = Field(default="", max_length=48)
    icon: str = "check-circle"


class ProcessData(BaseModel):
    kind: Literal["process"] = "process"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    steps: list[Step] = Field(min_length=2, max_length=5)
    so_what: str = Field(default="", max_length=60)


class IconCard(BaseModel):
    icon: str
    title: str = Field(max_length=12)
    subtitle: str = Field(default="", max_length=32)   # latin/mono caption
    lines: list[str] = Field(default_factory=list, max_length=3)
    punch: str = Field(default="", max_length=20)      # the colored take-away line


class IconGridData(BaseModel):
    """Icon-grid: 4–6 solid color-block cards (icon + title + caption +
    a couple lines + a punch line)."""
    kind: Literal["icon_grid"] = "icon_grid"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    subtitle: str = Field(default="", max_length=56)   # mono strapline under title
    cards: list[IconCard] = Field(min_length=2, max_length=6)
    so_what: str = Field(default="", max_length=60)


class Milestone(BaseModel):
    year: str = Field(max_length=10)
    title: str = Field(max_length=16)
    desc: str = Field(default="", max_length=44)


class TimelineData(BaseModel):
    kind: Literal["timeline"] = "timeline"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    subtitle: str = Field(default="", max_length=56)
    milestones: list[Milestone] = Field(min_length=2, max_length=5)
    so_what: str = Field(default="", max_length=60)


class TableData(BaseModel):
    kind: Literal["table"] = "table"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    subtitle: str = Field(default="", max_length=56)
    headers: list[str] = Field(min_length=2, max_length=5)
    rows: list[list[str]] = Field(min_length=1, max_length=8)
    so_what: str = Field(default="", max_length=60)


class Pillar(BaseModel):
    heading: str = Field(max_length=16)
    tag: str = Field(default="", max_length=22)        # latin/mono sub-label
    points: list[Point] = Field(min_length=1, max_length=5)


class PillarsData(BaseModel):
    kind: Literal["pillars"] = "pillars"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    subtitle: str = Field(default="", max_length=56)
    columns: list[Pillar] = Field(min_length=2, max_length=4)
    so_what: str = Field(default="", max_length=60)


class QuoteData(BaseModel):
    kind: Literal["quote"] = "quote"
    quote: str = Field(max_length=80)
    attribution: str = Field(default="", max_length=40)


class ClosingData(BaseModel):
    kind: Literal["closing"] = "closing"
    title: str = Field(default="谢谢", max_length=20)
    subtitle: str = Field(default="", max_length=48)
    contact: str = Field(default="", max_length=48)


class SideBar(BaseModel):
    """侧栏结构条:label + 数值(条宽按组内最大值归一)+ 右侧标注。em=主体条(上强调色)。"""
    label: str = Field(max_length=16)
    value: float
    note: str = Field(default="", max_length=12)
    em: bool = False


class SideModule(BaseModel):
    title: str = Field(max_length=24)
    bars: list[SideBar] = Field(min_length=2, max_length=5)


class InsightBox(BaseModel):
    """编号洞察框(咨询版面的 ①② 解读区)。"""
    title: str = Field(max_length=24)
    points: list[str] = Field(min_length=1, max_length=3)   # 每条 ≤60 字


class Implication(BaseModel):
    """底部「对企业的意义」条目:图标 + 短题 + 一句话。"""
    icon: str = "check-circle"
    title: str = Field(max_length=14)
    desc: str = Field(default="", max_length=40)


class ExhibitData(BaseModel):
    """复合证据版面(高密度咨询页):完整结论句大标题 + 主图表模块 +
    侧栏结构条模块 + 编号洞察框 + 底部意义条 + 来源。SCR 叙事的一页式载体。"""
    kind: Literal["exhibit"] = "exhibit"
    eyebrow: str = Field(default="核心结论", max_length=24)
    title: str = Field(max_length=72)                        # 结论句,允许两行 + **强调**
    chart_title: str = Field(default="", max_length=30)
    chart_type: Literal["column", "bar", "line"] = "column"
    categories: list[str] = []
    series: list[Series] = Field(default_factory=list, max_length=4)
    chart_note: str = Field(default="", max_length=40)       # 图下标注(如 CAGR 框)
    side: list[SideModule] = Field(default_factory=list, max_length=2)
    insights: list[InsightBox] = Field(default_factory=list, max_length=2)
    implications: list[Implication] = Field(default_factory=list, max_length=4)
    source: str = Field(default="", max_length=60)


class CustomData(BaseModel):
    """创作轨（B 层）—— LLM 写的 HTML 片段，吃设计系统套件的 class/令牌变量。
    无字数预算（靠套件约束 + 评论官）；叶子必带 data-ppt；颜色用 var(--*)/.c-*；
    字号用 .t-* 字阶 class；禁自绘图表（图表走 ChartData）。"""
    kind: Literal["custom"] = "custom"
    html: str                              # canvas 内的 HTML
    dark: bool = False                     # 深色场景（用 --bg 底）
    role: str = "hero"                     # cover/section/statement/hero（审计/路由）
    motifs_used: list[str] = Field(default_factory=list)


SlideData = Annotated[
    Union[CoverData, HeroData, SectionData, KpiData, BulletsData, ChartData,
          TocData, TwoColData, CompareData, ProcessData, IconGridData,
          TimelineData, TableData, PillarsData, QuoteData, ClosingData,
          ExhibitData, CustomData],
    Field(discriminator="kind"),
]


# ---- deck ----------------------------------------------------------------
class DeckMeta(BaseModel):
    title: str
    lang: Literal["zh", "en"] = "zh"


class Slide(BaseModel):
    data: SlideData
    notes: str | None = None

    @property
    def kind(self) -> str:
        return self.data.kind


class Deck(BaseModel):
    meta: DeckMeta
    theme: str = "riso"     # look id / seed id；未知值兜底到默认 look
    slides: list[Slide]
