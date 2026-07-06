"""Image-mode for the Swiss look.

  swiss_ify(src, theme)  -> 任意来源图统一成 ink×paper 双色调（近黑→纸白灰阶），
                            高对比、无色相——照片成为网格里的"证据块"而非装饰。

  make_hero(art, theme)  -> 无源图时的程序化兜底：Müller-Brockmann 式几何构成
                            （IKB 圆弧 / 细线网格 / 墨色块），大量留白。

输出扁平 RGB PNG，作为原生图片全宽嵌入；文字在其下方原生排布（S22 结构，
不叠图上，无需预留安静区）。"""
from __future__ import annotations
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def swiss_ify(src_path: str, theme, out_path: str):
    """灰度双色调：暗部压到 ink、亮部升到 paper，中间灰阶带一点冷调。
    任何杂图（照片 / t2i 渲染）都收敛进同一套克制的黑白语言。"""
    c = theme.render_colors() if hasattr(theme, "render_colors") else theme.colors
    ink, paper = c["ink"], c["bg-content"]
    src = Image.open(src_path).convert("L")
    src = ImageOps.autocontrast(src, cutoff=1)
    out = ImageOps.colorize(src, black=ink, white=paper)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    return out_path


def make_hero(art: str, theme, out_path: str, w: int = 1600, h: int = 560):
    """程序化几何兜底：纸底 + 细线网格 + IKB 大圆（部分出血）+ 墨色条。
    单锚点色纪律；构图冷静，左右均衡但不对称。"""
    c = theme.render_colors() if hasattr(theme, "render_colors") else theme.colors
    paper, ink, accent = _rgb(c["bg-content"]), _rgb(c["ink"]), _rgb(c["primary"])
    grey2 = _rgb(c.get("grey-2", "#D4D4D2"))
    img = Image.new("RGB", (w, h), paper)
    d = ImageDraw.Draw(img)
    # 细线网格（16 列）
    step = w / 16
    for i in range(1, 16):
        d.line([(i * step, 0), (i * step, h)], fill=grey2, width=1)
    d.line([(0, h * 0.5), (w, h * 0.5)], fill=grey2, width=1)
    # IKB 大圆，右侧半出血（几何主角）
    r = h * 0.72
    cx, cy = w * 0.72, h * 0.52
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent)
    # 墨色竖条组（左侧配重，模数化宽度）
    bx = w * 0.10
    for i, bw_ in enumerate((10, 22, 46)):
        d.rectangle([bx, h * 0.22, bx + bw_, h * 0.86], fill=ink)
        bx += bw_ + 18
    # 纸色小方在圆上开窗（图形标点）
    s = h * 0.10
    d.rectangle([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2], fill=paper)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


# ---- t2i 风格纪律（拼在任意内容 prompt 之后；engine 经 genimage 使用） ----
STYLE_SUFFIX = (
    "Minimalist black and white documentary photograph in the Swiss "
    "international typographic style: a single clear subject, clean geometric "
    "composition, generous negative space, high contrast monochrome, soft "
    "even studio light, plain light grey seamless background. No text, no "
    "letters, no watermark, no logo, no border, no gradients, no clutter."
)
