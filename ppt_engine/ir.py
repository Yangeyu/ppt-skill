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


class BulletsData(BaseModel):
    kind: Literal["bullets"] = "bullets"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    bullets: list[Bullet] = Field(min_length=1, max_length=6)


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


class CompareData(BaseModel):
    kind: Literal["comparison"] = "comparison"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    left: Column
    right: Column


class Step(BaseModel):
    title: str = Field(max_length=16)
    desc: str = Field(default="", max_length=48)
    icon: str = "check-circle"


class ProcessData(BaseModel):
    kind: Literal["process"] = "process"
    eyebrow: str = Field(default="", max_length=24)
    title: str = Field(max_length=24)
    steps: list[Step] = Field(min_length=2, max_length=5)


class QuoteData(BaseModel):
    kind: Literal["quote"] = "quote"
    quote: str = Field(max_length=80)
    attribution: str = Field(default="", max_length=40)


class ClosingData(BaseModel):
    kind: Literal["closing"] = "closing"
    title: str = Field(default="谢谢", max_length=20)
    subtitle: str = Field(default="", max_length=48)
    contact: str = Field(default="", max_length=48)


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
    Union[CoverData, SectionData, KpiData, BulletsData, ChartData,
          TocData, TwoColData, CompareData, ProcessData, QuoteData, ClosingData,
          CustomData],
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
    theme: str = "aurora"
    slides: list[Slide]
