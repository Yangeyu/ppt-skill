"""编排器 —— 七段管线总入口（DESIGN §3）。

主题 →① 艺术总监 →② 身份评论官 →③ 套件实例化(build 内) →④ 规划+路由 →⑤ 浏览器排版
→⑥ 页面评论官(结构[+美学]) + 创作页重生成 ≤N 轮 →⑦ 导出原生 pptx。

`generate()` 是对外一行入口；细到每段也可单独调用（见 artdirect/planner/build/critic）。"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

from .artdirect import art_direct, DesignBrief
from .planner import plan_deck, _write_html
from .build import Engine
from .critic import critique_structure, critique_deck
from .spec import SpecLock
from .ir import Deck, CustomData


@dataclass
class Result:
    out_path: str
    spec: SpecLock
    deck: Deck
    prims: list
    identity_issues: list = field(default_factory=list)
    structural_issues: list = field(default_factory=list)
    aesthetic_reports: list = field(default_factory=list)
    rounds: int = 0

    @property
    def structural_errors(self):
        return [i for i in self.structural_issues if getattr(i, "level", "") == "error"]

    def summary(self) -> str:
        idn = len([i for i in self.identity_issues if getattr(i, "level", "") == "error"])
        return (f"{len(self.deck.slides)} 页 · 身份 error {idn} · "
                f"结构 error {len(self.structural_errors)} / warning "
                f"{len([i for i in self.structural_issues if getattr(i,'level','')=='warning'])} · "
                f"重生成 {self.rounds} 轮 · {self.out_path}")


def generate(topic: str, *, out_path: str, audience: str = "", tone: str = "",
             seed_theme: str | None = None, n_slides: int = 10,
             use_llm: bool | None = None, screenshot_dir: str | None = None,
             max_repair: int = 2, aesthetic: bool = False) -> Result:
    # ① 艺术总监 + ② 身份评论官（内含身份重生成）
    spec, id_issues = art_direct(
        DesignBrief(topic=topic, audience=audience, tone=tone, seed_theme=seed_theme),
        use_llm=use_llm)

    # ④ 规划 + 路由（③ 套件实例化在 build 内按 spec 完成）
    deck = plan_deck(topic, spec, n_slides=n_slides, audience=audience, use_llm=use_llm)

    engine = Engine()
    rounds = 0
    prims = engine.build(deck, out_path, spec=spec, screenshot_dir=screenshot_dir)

    # ⑥ 页面评论官（结构）+ 创作页重生成 ≤max_repair 轮
    strict = [s.kind == "custom" for s in deck.slides]
    issues = critique_structure(prims, spec, strict_scale=strict)
    while max_repair and rounds < max_repair:
        bad = _creative_slides_with_errors(deck, issues)
        if not bad:
            break
        if not (use_llm if use_llm is not None else True):
            break
        for idx in bad:                       # 带违规项重写该创作页 HTML
            fb = "；".join(str(i.detail) for i in issues if i.slide == idx + 1 and i.level == "error")
            try:
                slide = deck.slides[idx]
                html = _write_html(spec, f"{slide.data.html}\n\n[修正以下问题后重写]：{fb}",
                                   slide.data.role, slide.data.dark)
                deck.slides[idx] = slide.model_copy(update={"data": CustomData(
                    html=html, role=slide.data.role, dark=slide.data.dark)})
            except Exception:
                pass
        rounds += 1
        prims = engine.build(deck, out_path, spec=spec, screenshot_dir=screenshot_dir)
        issues = critique_structure(prims, spec, strict_scale=strict)

    # ⑥(美学) 可选：视觉模型读截图评 B 层（需 screenshot_dir）
    aesthetic_reports = []
    if aesthetic and screenshot_dir:
        from pathlib import Path as _P
        shots = sorted(str(p) for p in _P(screenshot_dir).glob("slide_*.png"))
        intents = [s.data.role if s.kind == "custom" else s.kind for s in deck.slides]
        aesthetic_reports = critique_deck(shots, spec=spec, intents=intents)

    return Result(out_path=out_path, spec=spec, deck=deck, prims=prims,
                  identity_issues=id_issues, structural_issues=issues,
                  aesthetic_reports=aesthetic_reports, rounds=rounds)


def _creative_slides_with_errors(deck: Deck, issues) -> list[int]:
    err_slides = {i.slide for i in issues if i.level == "error"}
    return [idx for idx, s in enumerate(deck.slides)
            if s.kind == "custom" and (idx + 1) in err_slides]
