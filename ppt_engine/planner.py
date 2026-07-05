"""规划器 —— 主题 → 完整 Deck IR（DESIGN §3 路由 + §5 IR + §9 创作轨）。

两段：
 ① 叙事大纲（一次 LLM 调用）：每页定 role/track；结构页给 IR 字段，创作页给 brief。
 ② 逐页落地：结构页映射成受校验 IR（超限截断兜底）；创作页用套件写 HTML（聚焦单调用）。

无 LLM 时给一个确定性兜底大纲，保证总能出 deck。"""
from __future__ import annotations
import re

from . import llm
from .contract import FACT_RULES, available_kinds, kind_menu, look_guidance
from .looks import get_look
from .spec import SpecLock
from .ir import (Deck, DeckMeta, Slide, CustomData,
                 CoverData, SectionData, KpiData, Stat, BulletsData, Bullet,
                 ChartData, Series, TocData, TocItem, TwoColData, CompareData,
                 Column, ProcessData, Step, QuoteData, ClosingData)

# 设计系统套件速查（创作轨提示词用）
KIT_CHEAT = """可用 class（只能用这些；写不出离阶字号/离板色）：
字阶 .t-display(hero大字,不折行) .t-h1 .t-h2 .t-body .t-caption .t-micro
字族 .f-serif .f-sans  字重 .w-regular .w-bold .w-black  修饰 .upper .wide .tight .nowrap
文字色 .c-ink .c-muted .c-primary .c-primary-2 .c-on-dark .c-on-dark-muted .c-paper
背景/形状色 .bg-paper .bg-ink .bg-surface .bg-primary .bg-primary-2
排布 .frame(安全区容器) .flex .col .center .between .items-center .grid .abs .rule(发丝线) .bar(强调条) .img
规则：每个可见叶子(文字/色块/图)必须带 data-ppt="text|rect|image"；纯装饰副本(如套印影子)加 data-ppt-deco；
颜色只用上面的 .c-*/.bg-* 或 var(--primary) 等令牌，禁止内联 #HEX。
文字色铁律(否则不可读)：纸底场景文字只用 .c-ink/.c-muted/.c-primary；深色场景(dark)文字只用 .c-on-dark/.c-on-dark-muted/.c-paper；
**绝不**用 surface/paper/浅色当纸底文字色、绝不用 ink/深色当深底文字色。"""

MISREGISTER_EXAMPLE = """<!-- 套印错位标题(misregister)：影子层 data-ppt-deco 偏移3px -->
<div style="position:relative;display:inline-block;">
  <div data-ppt="text" data-ppt-deco class="t-display f-serif w-black c-primary" style="position:absolute;left:3px;top:3px;">标题文字</div>
  <div data-ppt="text" class="t-display f-serif w-black c-ink" style="position:relative;">标题文字</div>
</div>"""


# ---- 结构页：content dict → 受校验 IR --------------------------------------
def _trunc(s, n):
    return s if not isinstance(s, str) or len(s) <= n else s[:n]


def _build_struct(kind: str, c: dict):
    """严格路径：直接过 SlideData 判别联合（覆盖全部 kind，含 exhibit 等新版式）；
    校验失败再落回旧的截断兜底（只覆盖老 9 kind）。"""
    try:
        return Slide(data={"kind": kind, **c}).data
    except Exception:
        pass
    return _build_struct_lenient(kind, c)


def _build_struct_lenient(kind: str, c: dict):
    try:
        if kind == "toc":
            return TocData(eyebrow=_trunc(c.get("eyebrow", ""), 24), title=_trunc(c.get("title", "目录"), 24),
                           items=[TocItem(title=_trunc(x if isinstance(x, str) else x.get("title", ""), 24))
                                  for x in c.get("items", [])][:8])
        if kind == "kpi":
            return KpiData(eyebrow=_trunc(c.get("eyebrow", ""), 24), title=_trunc(c.get("title", ""), 24),
                           stats=[Stat(value=_trunc(s.get("value", ""), 8), label=_trunc(s.get("label", ""), 16),
                                       delta=_trunc(s.get("delta"), 12) if s.get("delta") else None,
                                       delta_dir=s.get("delta_dir", "flat")) for s in c.get("stats", [])][:4])
        if kind == "bullets":
            return BulletsData(eyebrow=_trunc(c.get("eyebrow", ""), 24), title=_trunc(c.get("title", ""), 24),
                               bullets=[Bullet(text=_trunc(b if isinstance(b, str) else b.get("text", ""), 80),
                                               emphasis=bool(b.get("emphasis")) if isinstance(b, dict) else False)
                                        for b in c.get("bullets", [])][:6])
        if kind in ("two_col", "comparison"):
            cls = TwoColData if kind == "two_col" else CompareData
            def col(x):
                return Column(heading=_trunc(x.get("heading", ""), 24),
                              points=[_trunc(p, 60) for p in x.get("points", [])][:5] or ["—"])
            return cls(eyebrow=_trunc(c.get("eyebrow", ""), 24), title=_trunc(c.get("title", ""), 24),
                       left=col(c.get("left", {})), right=col(c.get("right", {})))
        if kind == "process":
            return ProcessData(eyebrow=_trunc(c.get("eyebrow", ""), 24), title=_trunc(c.get("title", ""), 24),
                               steps=[Step(title=_trunc(s.get("title", ""), 16), desc=_trunc(s.get("desc", ""), 48),
                                           icon=s.get("icon", "check-circle")) for s in c.get("steps", [])][:5])
        if kind == "chart":
            return ChartData(eyebrow=_trunc(c.get("eyebrow", ""), 24), title=_trunc(c.get("title", ""), 24),
                             chart_type=c.get("chart_type", "column"), categories=c.get("categories", [])[:8],
                             series=[Series(name=_trunc(s.get("name", ""), 20), values=[float(v) for v in s.get("values", [])])
                                     for s in c.get("series", [])][:4], takeaway=_trunc(c.get("takeaway", ""), 60))
        if kind == "quote":
            return QuoteData(quote=_trunc(c.get("quote", ""), 80), attribution=_trunc(c.get("attribution", ""), 40))
        if kind == "closing":
            return ClosingData(title=_trunc(c.get("title", "谢谢"), 20), subtitle=_trunc(c.get("subtitle", ""), 48),
                               contact=_trunc(c.get("contact", ""), 48))
    except Exception:
        return None
    return None


# ---- 创作页：写 HTML --------------------------------------------------------
def _write_html(spec: SpecLock, brief: str, role: str, dark: bool) -> str:
    motif_help = "\n".join(f"- {m.name}: {m.description}\n  {m.html}" for m in spec.motifs) or "（无预置母题，可自创但须用令牌色）"
    sys = (f"你是演示文稿创作轨设计师。用「设计系统套件」写一页 {role} 的 HTML 片段(只输出 canvas 内的 HTML，不要 <html>/<style>)。\n"
           f"{KIT_CHEAT}\n本主题母题：\n{motif_help}\n套印错位写法示例：\n{MISREGISTER_EXAMPLE}\n"
           f"设计语言：主色 var(--primary)，强调 var(--primary-2)；图像处理 {spec.image.style}。"
           f"务必：大字用 .t-display 且简短不溢出(画布1280×720,安全区{spec.grid.margin}px)；层级清晰、留白充足、单一焦点。")
    usr = f"页面意图/内容：{brief}\n深色场景：{dark}"
    html = llm.chat(sys, usr, temperature=0.7, max_tokens=2000)
    html = html.strip()
    if html.startswith("```"):
        html = re.sub(r"^```[a-z]*\n?", "", html)
        html = re.sub(r"\n?```$", "", html).strip()
    return html


# ---- 大纲 ------------------------------------------------------------------
def _outline_sys(look_id: str) -> str:
    """大纲提示词 = 契约的结构菜单 + 事实纪律 + look 引导段(单一来源,勿手写菜单)。"""
    guidance = look_guidance(look_id)
    return (
        '你是演示文稿叙事策划。把主题拆成 N 页有节奏的 deck，输出 JSON：{"slides":[ ... ]}。\n'
        "每页二选一：\n"
        'A) 结构页(承载信息) {"track":"structured","kind":"<菜单之一>","content":{...该版式字段...}}\n'
        "   菜单与字段——**字数上限是硬约束**,标 ? 的字段可省略:\n"
        f"{kind_menu(look_id)}\n"
        'B) 创作页(强表现力,用于封面/章节/金句/主视觉) {"track":"creative","role":"cover|section|statement",'
        '"brief":"这页要表达什么+关键文案","dark":true/false}\n'
        "规则：第1页必须是 creative cover；含 1-2 个 creative section 做章节过渡；"
        "最后一页 closing 或 creative statement。其余按内容选合适结构版式。\n\n"
        f"{FACT_RULES}\n\n"
        + (f"{guidance}\n\n" if guidance else "")
        + "只输出 JSON。"
    )


def _fallback_outline(topic: str, n: int) -> list[dict]:
    return [
        {"track": "creative", "role": "cover", "brief": f"封面：{topic}", "dark": False},
        {"track": "structured", "kind": "bullets",
         "content": {"eyebrow": "Overview", "title": topic[:20],
                     "bullets": [{"text": f"{topic} 的关键要点（占位）"}]}},
        {"track": "structured", "kind": "closing", "content": {"title": "谢谢"}},
    ]


def plan_deck(topic: str, spec: SpecLock, *, n_slides: int = 10, audience: str = "",
              source: str = "", use_llm: bool | None = None) -> Deck:
    look_id = get_look(spec).spec.id
    struct_kinds = set(available_kinds(look_id))
    want = llm.available() if use_llm is None else use_llm
    items = None
    if want and llm.available():
        try:
            usr = f"主题：{topic}\n受众：{audience or '通用'}\n页数：约 {n_slides} 页"
            if source:
                usr += f"\n素材：\n{source[:6000]}"
            data = llm.chat_json(_outline_sys(look_id), usr, temperature=0.6, max_tokens=8000)
            items = data.get("slides") or []
        except Exception:
            items = None
    if not items:
        items = _fallback_outline(topic, n_slides)

    slides: list[Slide] = []
    for it in items:
        track = it.get("track")
        if track == "creative":
            try:
                html = _write_html(spec, it.get("brief", topic), it.get("role", "hero"), bool(it.get("dark")))
            except Exception:
                continue
            slides.append(Slide(data=CustomData(html=html, role=it.get("role", "hero"), dark=bool(it.get("dark")))))
        else:
            kind = it.get("kind", "bullets")
            if kind not in struct_kinds:
                kind = "bullets"
            data = _build_struct(kind, it.get("content", {}))
            if data is not None:
                slides.append(Slide(data=data))
    if not slides:                       # 极端兜底
        slides = [Slide(data=ClosingData(title=topic[:20]))]
    return Deck(meta=DeckMeta(title=topic[:60], lang="zh"), slides=slides)
