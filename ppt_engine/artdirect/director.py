"""艺术总监 —— 为主题现场发明整套设计语言（DESIGN §4，freedom 的源头）。

两条后端：
 - LLM（默认，若有 key）：读 brief → 产出设计语言 JSON → 组装 SpecLock → 过身份
   评论官，带违规项重生成 ≤N 轮；仍不过则降级确定性，保证总能返回合法 spec。
 - 确定性兜底：按关键词选 seed 主题 + 图像处理 + 母题，by construction 过身份评论官。

字体受限于可嵌入集（思源黑/宋）——Riso 等观感靠颜色/图像处理/母题/重衬线表达。"""
from __future__ import annotations
from pydantic import BaseModel

from ..spec import (SpecLock, TypeScale, Grid, ImageTreatment, Motif,
                    expand_palette, legibilize, THEMES)
from .. import llm
from .identity_critic import critique_identity, EMBEDDABLE


class DesignBrief(BaseModel):
    topic: str
    audience: str = ""
    tone: str = ""                  # "复古印刷感" / "极简商务" / ...
    seed_theme: str | None = None   # 可选起点（editorial/aurora/ember）
    lang: str = "zh"


# ---- 确定性兜底 ----------------------------------------------------------
_TONE_SEED = [
    (("zine", "复古", "印刷", "手作", "riso", "独立", "书店", "文艺", "编辑",
      "潮流", "文化"), "riso", "screen-print"),
    (("商务", "金融", "科技", "汇报", "数据", "企业", "tech", "saas"), "aurora", "none"),
    (("活力", "营销", "温暖", "品牌", "消费", "campaign"), "ember", "warm"),
]


def _pick_seed(brief: DesignBrief) -> tuple[str, str]:
    if brief.seed_theme in THEMES:
        return brief.seed_theme, "none"
    blob = f"{brief.topic} {brief.tone} {brief.audience}".lower()
    for kws, seed, img in _TONE_SEED:
        if any(k in blob for k in kws):
            return seed, img
    return "editorial", "none"


def _deterministic(brief: DesignBrief) -> SpecLock:
    seed, img = _pick_seed(brief)
    spec = SpecLock.from_seed(seed, image=ImageTreatment(style=img),
                              rationale=f"确定性兜底·seed={seed}·主题「{brief.topic}」")
    return spec


# ---- LLM freedom 路径 ----------------------------------------------------
_SYS = """你是顶尖的演示文稿艺术总监。为给定主题**现场发明一整套设计语言**，要既贴合主题气质、又在体系上成立。
只输出一个 JSON 对象，字段：
{
 "name": "设计语言名(中文短语)",
 "rationale": "为何这套语言贴合该主题(1-2句)",
 "palette": {"bg":"#..(深色场景底)","paper":"#..(浅色内容底)","ink":"#..(正文)","muted":"#..(次要文字)","primary":"#..(主强调)","accent":"#..(次强调)","pos":"#..","neg":"#.."},
 "type": {"ratio":1.333,"display":88,"h1":48,"h2":32,"body":20,"caption":15,"micro":12},
 "fonts": {"display":"Noto Serif SC","body":"Noto Sans SC"},
 "image_treatment": "none|duotone|screen-print|grayscale|warm",
 "chart_palette": ["RRGGBB", "..(6个,无#)"],
 "rules": ["硬规则,如 卡片无圆角"],
 "motifs": [{"name":"misregister","description":"何时用","html":"<span data-ppt=\\"text\\" class=\\"t-display c-primary\\">…</span>"}]
}
硬约束(必须满足,否则会被打回):
- 字体 display/body 只能从 ["Noto Serif SC","Noto Sans SC"] 里选(暂只支持这两族;特殊观感用颜色/图像处理/母题表达)。
- type.ratio ∈ {1.2,1.25,1.333,1.5,1.618}; display/body ≥ 3。
- ink 与 paper 对比 ≥ 4.5:1; 不要纯黑#000正文/纯白#FFF底(用染色)。
- 配色: 1主+1辅强调,其余中性; 强调色克制。
- motif 的 html 只能用令牌 class(.t-*/.c-*)或 var(--*),且带 data-ppt 标记,不要内联离板#HEX。"""


def _build_from_json(d: dict, brief: DesignBrief) -> SpecLock:
    pal = d.get("palette", {})
    colors = legibilize(expand_palette(pal))
    t = d.get("type", {})
    scale = TypeScale(
        ratio=float(t.get("ratio", 1.333)),
        display=int(t.get("display", 88)), h1=int(t.get("h1", 48)),
        h2=int(t.get("h2", 32)), body=int(t.get("body", 20)),
        caption=int(t.get("caption", 15)), micro=int(t.get("micro", 12)))
    fonts = d.get("fonts", {})
    disp = fonts.get("display", "Noto Serif SC")
    body = fonts.get("body", "Noto Sans SC")
    disp = disp if disp in EMBEDDABLE else "Noto Serif SC"
    body = body if body in EMBEDDABLE else "Noto Sans SC"
    cp = d.get("chart_palette") or [colors["primary"].lstrip("#"), colors["primary-2"].lstrip("#"),
                                    "C8A15A", "7C6F5B", "4F7A52", "8A7F70"]
    cp = [h.lstrip("#").upper() for h in cp][:6]
    while len(cp) < 6:
        cp.append("8A7F70")
    motifs = [Motif(name=m.get("name", "motif"), description=m.get("description", ""),
                    html=m.get("html", "")) for m in d.get("motifs", [])][:4]
    return SpecLock(
        id="generated", name=d.get("name", brief.topic)[:24],
        colors=colors, display_font=disp, body_font=body, chart_palette=cp,
        type_scale=scale, grid=Grid(),
        image=ImageTreatment(style=d.get("image_treatment", "none")),
        motifs=motifs, rules=d.get("rules", []), rationale=d.get("rationale", ""))


def _llm(brief: DesignBrief, max_rounds: int = 2) -> tuple[SpecLock, list]:
    feedback = ""
    last = None
    for _ in range(max_rounds + 1):
        user = (f"主题：{brief.topic}\n受众：{brief.audience or '通用'}\n"
                f"气质倾向：{brief.tone or '由你判断'}\n语言：{brief.lang}")
        if feedback:
            user += f"\n\n上一版被身份评论官打回，违规项（请修正后重出完整 JSON）：\n{feedback}"
        try:
            d = llm.chat_json(_SYS, user, temperature=0.8)
            spec = _build_from_json(d, brief)
        except Exception as e:
            return _deterministic(brief), [f"LLM 失败降级: {str(e)[:80]}"]
        issues = critique_identity(spec)
        errs = [i for i in issues if i.level == "error"]
        last = (spec, issues)
        if not errs:
            return spec, issues
        feedback = "\n".join(f"- {i.check}: {i.detail}" for i in errs)
    # 多轮仍不过 → 降级确定性兜底（保证可用）
    det = _deterministic(brief)
    return det, critique_identity(det)


# ---- 对外入口 ------------------------------------------------------------
def art_direct(brief: DesignBrief, *, use_llm: bool | None = None,
               max_rounds: int = 2) -> tuple[SpecLock, list]:
    """返回 (SpecLock, 身份评论官 issues)。use_llm=None 时按 key 自动决定。"""
    want = llm.available() if use_llm is None else use_llm
    if want and llm.available():
        return _llm(brief, max_rounds)
    spec = _deterministic(brief)
    return spec, critique_identity(spec)
