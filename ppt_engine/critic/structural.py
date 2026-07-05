"""结构评论官 —— 读浏览器量出的「已测原语」断言 A 层地板（QUALITY §2.1–2.4）。

纯 Python、零模型。放弃确定性后，地板由「浏览器算出的真实几何 + 本断言」保证：
即便排版非确定，零越界/零重叠/颜色∈令牌/对比达标 仍可机器判定。

errors（阻断）：PG-GM-1 越界 / PG-GM-2 文本重叠 / PG-CL-1 颜色离板 / PG-CL-2 对比不足。
warnings（提示）：PG-TY-1 字号离阶(结构轨) / PG-SP-1 留白比 / PG-CS-1 跨页一致。
创作轨传 strict=True：字号离阶升为 error（LLM 必须吃令牌）。"""
from __future__ import annotations
import re
from dataclasses import dataclass

from ..units import CANVAS_W_PX, CANVAS_H_PX, parse_color
from ..spec import SpecLock, contrast_ratio

_READABLE = re.compile(r"[0-9A-Za-z一-鿿぀-ヿ]")  # 含可读内容(字母/数字/中日文)


@dataclass
class StructuralIssue:
    slide: int
    check: str
    level: str            # "error" | "warning"
    detail: str

    def __str__(self):
        return f"  slide{self.slide:>2} [{self.level.upper():7}] {self.check}: {self.detail}"


def _hex(css: str) -> str | None:
    h, a = parse_color(css)
    return h if (h and a > 0) else None


def _rect_color(r) -> str | None:
    """rect 的可见底色：优先渐变首色（深色页用 data-grad 画底，backgroundColor 透明），
    否则取 backgroundColor。grad 格式 'c1,c2,ang'（hex 无 #）。"""
    grad = r.get("grad")
    if grad:
        c1 = grad.split(",")[0].strip().lstrip("#")
        if len(c1) in (3, 6):
            return c1.upper() if len(c1) == 6 else "".join(ch * 2 for ch in c1).upper()
    return _hex(r.get("fill"))


def _base_bg(prims, spec: SpecLock) -> str:
    """该页底色：取覆盖整幅、z 最低的 rect（含渐变底）；缺省回退暖纸。"""
    full = [p for p in prims if p["kind"] == "rect"
            and p["w"] >= CANVAS_W_PX * 0.9 and p["h"] >= CANVAS_H_PX * 0.9]
    if full:
        full.sort(key=lambda p: (p.get("z") if p.get("z") is not None else 0))
        for r in full:
            h = _rect_color(r)
            if h:
                return h
    return spec.colors["bg-content"].lstrip("#").upper()


def _bg_under(p, prims, base: str) -> str:
    """文本 p 脚下的背景色：取包含其中心、z 更低的最高 rect，否则页底色。"""
    cx, cy = p["x"] + p["w"] / 2, p["y"] + p["h"] / 2
    pz = p.get("z") if p.get("z") is not None else 10
    cands = []
    for r in prims:
        if r["kind"] != "rect":
            continue
        rz = r.get("z") if r.get("z") is not None else 0
        if rz >= pz:
            continue
        if r["x"] <= cx <= r["x"] + r["w"] and r["y"] <= cy <= r["y"] + r["h"]:
            h = _rect_color(r)
            if h:
                cands.append((rz, h))
    if cands:
        cands.sort()
        return cands[-1][1]
    return base


def _is_large(p) -> bool:
    fs = p.get("fontSizePx", 0)
    return fs >= 24 or (fs >= 18.66 and p.get("fontWeight", 400) >= 700)


def critique_structure(slides_prims, spec: SpecLock, *, strict_scale: list[bool] | None = None,
                       margin: int = 64, bleed: int = 24) -> list[StructuralIssue]:
    out: list[StructuralIssue] = []
    allowed_hex = spec.allowed_hex()
    allowed_sizes = set(spec.allowed_sizes())
    fams_allowed = {f for f in spec.families()}
    deck_families: set[str] = set()

    for i, prims in enumerate(slides_prims, 1):
        strict = bool(strict_scale[i - 1]) if strict_scale else False
        base = _base_bg(prims, spec)
        texts = [p for p in prims if p["kind"] == "text" and not p.get("deco")]

        # PG-GM-1 越界（装饰可出血，正文不可）
        for p in prims:
            if p.get("deco"):
                continue
            if p["kind"] == "text":
                if (p["x"] < -bleed or p["y"] < -bleed
                        or p["x"] + p["w"] > CANVAS_W_PX + bleed
                        or p["y"] + p["h"] > CANVAS_H_PX + bleed):
                    out.append(StructuralIssue(i, "PG-GM-1", "error",
                        f"越界文本「{p.get('text','')[:18]}」@({p['x']:.0f},{p['y']:.0f})"))

        # PG-GM-2 正文文本两两重叠
        for a in range(len(texts)):
            for b in range(a + 1, len(texts)):
                t1, t2 = texts[a], texts[b]
                ox = min(t1["x"] + t1["w"], t2["x"] + t2["w"]) - max(t1["x"], t2["x"])
                oy = min(t1["y"] + t1["h"], t2["y"] + t2["h"]) - max(t1["y"], t2["y"])
                if ox > 4 and oy > 6:
                    out.append(StructuralIssue(i, "PG-GM-2", "error",
                        f"文本重叠「{t1.get('text','')[:10]}」×「{t2.get('text','')[:10]}」"))

        for p in texts:
            hexv = _hex(p.get("color"))
            fam = p.get("family")
            if fam:
                deck_families.add(fam)
            # PG-CL-1 颜色 ∈ 令牌集
            if hexv and hexv not in allowed_hex:
                out.append(StructuralIssue(i, "PG-CL-1", "error",
                    f"离板文字色 #{hexv}「{p.get('text','')[:12]}」"))
            # PG-CL-2 对比达标：<3.0 不可读=error；3.0–4.5 低于 AA=warning（大字 3.0 即达标）。
            # 纯标点/符号(无可读内容,如分隔点·)是装饰,对比问题降为 warning。
            if hexv:
                bg = _bg_under(p, prims, base)
                cr = contrast_ratio(hexv, bg)
                readable = bool(_READABLE.search(p.get("text", "")))
                if cr < 3.0:
                    out.append(StructuralIssue(i, "PG-CL-2", "error" if readable else "warning",
                        f"对比不可读 {cr:.2f}<3.0 文「{p.get('text','')[:12]}」(#{hexv} on #{bg})"))
                elif cr < 4.5 and not _is_large(p):
                    out.append(StructuralIssue(i, "PG-CL-2", "warning",
                        f"对比低于 AA {cr:.2f}<4.5 文「{p.get('text','')[:12]}」(#{hexv} on #{bg})"))
            # PG-TY-1 字号 ∈ 字阶（结构轨 warning，创作轨 error）
            fs = round(p.get("fontSizePx", 0))
            if allowed_sizes and not any(abs(fs - s) <= 1 for s in allowed_sizes):
                out.append(StructuralIssue(i, "PG-TY-1", "error" if strict else "warning",
                    f"字号 {fs}px 不在字阶 {sorted(allowed_sizes, reverse=True)}「{p.get('text','')[:10]}」"))
            # PG-TY-6 字族 ∈ 锁定字族
            if fam and fams_allowed and fam not in fams_allowed:
                out.append(StructuralIssue(i, "PG-TY-6", "warning",
                    f"字族「{fam}」不在锁定集 {sorted(fams_allowed)}"))

        # PG-SP-1 留白比（内容包围盒/画布）
        content = [p for p in prims if not p.get("deco")
                   and p["w"] < CANVAS_W_PX * 0.9]   # 排除整幅底
        if content:
            x0 = min(p["x"] for p in content); y0 = min(p["y"] for p in content)
            x1 = max(p["x"] + p["w"] for p in content); y1 = max(p["y"] + p["h"] for p in content)
            ratio = max(0, (x1 - x0)) * max(0, (y1 - y0)) / (CANVAS_W_PX * CANVAS_H_PX)
            if ratio > 0.92:
                out.append(StructuralIssue(i, "PG-SP-1", "warning",
                    f"内容过满 留白比 {ratio:.2f}（>0.92，显拥挤）"))

    # PG-CS-1 跨页字族一致
    stray = deck_families - fams_allowed
    if fams_allowed and stray:
        out.append(StructuralIssue(0, "PG-CS-1", "warning", f"出现锁定外字族: {sorted(stray)}"))

    return out


def errors_only(issues) -> list:
    return [i for i in issues if i.level == "error"]
