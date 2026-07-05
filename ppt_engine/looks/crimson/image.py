"""Image-mode for the Crimson Consulting look.

  crimson_ify(src, theme)  -> 任意来源图统一成酒红双色调（深酒红暗部 → 纸白亮部，
                              中间调压暖红棕）——照片成为报告里的"证据图版"，
                              与深红锚点同一色相家族，绝不引入杂色。

  make_hero(art, theme)    -> 无源图时的程序化兜底：咨询报告式几何构成
                              （深红大块面 + 墨色细条 + 12 列发丝网格），全部直角。

输出扁平 RGB PNG，作为原生图片全宽嵌入；文字在其下方原生排布，不叠图上。"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def crimson_ify(src_path: str, theme, out_path: str):
    """酒红双色调：暗部压到深酒红黑、亮部升到纸白，中间调走暖红棕。
    任何杂图（照片 / t2i 渲染）都收敛进深红报告的同一色相语言。"""
    c = theme.render_colors() if hasattr(theme, "render_colors") else theme.colors
    paper = c["bg-content"]
    src = Image.open(src_path).convert("L")
    src = ImageOps.autocontrast(src, cutoff=1)
    out = ImageOps.colorize(src, black="#26110E", white=paper, mid="#7C4038")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    return out_path


def make_hero(art: str, theme, out_path: str, w: int = 1600, h: int = 560):
    """程序化兜底：纸底 + 12 列发丝网格 + 深红大块面（右侧出血）+ 墨色横条组。
    全部直角矩形——咨询报告的克制几何，无圆无斜。"""
    c = theme.render_colors() if hasattr(theme, "render_colors") else theme.colors
    paper, ink, accent = _rgb(c["bg-content"]), _rgb(c["ink"]), _rgb(c["primary"])
    deep = _rgb(c.get("primary-2", "#5E1414"))
    hairline = _rgb(c.get("hairline", "#D6D6D2"))
    img = Image.new("RGB", (w, h), paper)
    d = ImageDraw.Draw(img)
    # 12 列发丝网格
    step = w / 12
    for i in range(1, 12):
        d.line([(i * step, 0), (i * step, h)], fill=hairline, width=1)
    d.line([(0, h * 0.62), (w, h * 0.62)], fill=hairline, width=1)
    # 深红大块面，右侧出血（视觉主角），内嵌暗阶窄条制造装订感
    d.rectangle([w * 0.58, h * 0.14, w + 2, h * 0.86], fill=accent)
    d.rectangle([w * 0.58, h * 0.14, w * 0.60, h * 0.86], fill=deep)
    # 墨色横条组（左侧配重，模数化厚度）
    by = h * 0.30
    for bh in (8, 18, 40):
        d.rectangle([w * 0.07, by, w * 0.46, by + bh], fill=ink)
        by += bh + 22
    # 纸色小方在红面上开窗（图形标点）
    s = h * 0.09
    cx, cy = w * 0.78, h * 0.50
    d.rectangle([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2], fill=paper)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


# ---- t2i 风格纪律（拼在任意内容 prompt 之后；engine 经 genimage 使用） ----
STYLE_SUFFIX = (
    "Refined corporate documentary photograph for a premium strategy "
    "consulting report: a single clear subject, restrained composition, "
    "soft directional studio light, muted warm-grey tonality, generous "
    "negative space, shallow depth of field, plain seamless background. "
    "No text, no letters, no watermark, no logo, no border, no clutter."
)
