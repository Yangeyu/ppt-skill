"""美学评论官 —— 视觉模型读截图评 B 层（QUALITY §2.5）。

结构评论官（零模型）已把可机器判定的 A 层钉死；这里只判真正需要眼睛的 B 层：
层级 / 平衡 / 设计感 / 艺术指导大胆度 / 身份贴合。无视觉模型时优雅降级（返回 None）。"""
from __future__ import annotations
from dataclasses import dataclass

from .. import llm
from ..spec import SpecLock


@dataclass
class AestheticReport:
    slide: int
    scores: dict          # hierarchy/balance/design/boldness/fit -> 0..1
    issues: list
    suggestion: str

    @property
    def min_score(self) -> float:
        return min(self.scores.values()) if self.scores else 1.0

    def weak(self, thresh: float = 0.7) -> bool:
        return self.min_score < thresh


_SYS = """你是资深演示文稿设计评审。看这一页截图，按 0~1 给分并输出 JSON：
{"hierarchy":0~1(层级是否一眼分明),"balance":0~1(构图是否平衡),"design":0~1(是否"被设计过"非默认呆板),
 "boldness":0~1(艺术指导是否大胆贴题,结构页可适中),"fit":0~1(视觉与主题气质是否相符),
 "issues":["具体问题"],"suggestion":"一句最关键的改进"}
只输出 JSON。标准：专业杂志/keynote 级为 0.85+，干净但平庸 0.6，有明显毛病 <0.5。"""


def critique_aesthetic(screenshot: str, *, slide: int = 1, intent: str = "",
                       spec: SpecLock | None = None) -> AestheticReport | None:
    if not llm.available():
        return None
    try:
        prompt = _SYS + (f"\n本页意图：{intent}" if intent else "")
        if spec:
            prompt += f"\n主题设计语言：{spec.name}；主色应为 {spec.colors['primary']}。"
        d = llm.vision(prompt, screenshot, as_json=True)
        if not isinstance(d, dict):
            return None
        scores = {k: float(d.get(k, 0.7)) for k in ("hierarchy", "balance", "design", "boldness", "fit")}
        return AestheticReport(slide=slide, scores=scores,
                               issues=d.get("issues", []), suggestion=d.get("suggestion", ""))
    except Exception:
        return None


def critique_deck(screenshots: list[str], spec: SpecLock | None = None,
                  intents: list[str] | None = None) -> list[AestheticReport]:
    out = []
    for i, shot in enumerate(screenshots):
        r = critique_aesthetic(shot, slide=i + 1, spec=spec,
                               intent=(intents[i] if intents and i < len(intents) else ""))
        if r:
            out.append(r)
    return out
