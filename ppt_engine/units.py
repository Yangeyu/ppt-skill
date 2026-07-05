"""Unit helpers. The HTML canvas is rendered at 1280x720 CSS px (96 dpi),
which maps exactly onto a 16:9 slide: 1 px = 9525 EMU, 1 px = 0.75 pt."""
from __future__ import annotations

EMU_PER_PX = 9525          # 914400 EMU/in ÷ 96 px/in
PT_PER_PX = 0.75           # 72 pt/in ÷ 96 px/in
CANVAS_W_PX = 1280
CANVAS_H_PX = 720
SLIDE_W_EMU = CANVAS_W_PX * EMU_PER_PX   # 12192000  (13.333 in)
SLIDE_H_EMU = CANVAS_H_PX * EMU_PER_PX   # 6858000   (7.5 in)


def emu(px: float) -> int:
    return int(round(px * EMU_PER_PX))


def pt(px: float) -> float:
    return px * PT_PER_PX


def parse_color(css: str):
    """'rgb(r, g, b)' / 'rgba(r, g, b, a)' -> ('RRGGBB', alpha) or (None, 0)."""
    if not css:
        return None, 0.0
    css = css.strip()
    if css.startswith("#"):
        h = css[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return h.upper(), 1.0
    if css.startswith("rgb"):
        nums = css[css.index("(") + 1: css.index(")")].split(",")
        r, g, b = (int(float(n)) for n in nums[:3])
        a = float(nums[3]) if len(nums) > 3 else 1.0
        return f"{r:02X}{g:02X}{b:02X}", a
    return None, 0.0
