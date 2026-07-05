"""Image-mode hooks for the swiss look (the engine's look-art contract).

  STYLE_SUFFIX                 -> appended to every t2i content prompt so the
                                  generated source already matches the look:
                                  minimal editorial photography, one subject,
                                  vast negative space, muted palette + IKB accent.
  hero_from_source(src, theme) -> crop ANY photo to the hero strip (1280x412 slot,
                                  ~3.1:1) and quiet it down: slight desaturation +
                                  gentle contrast. No filters beyond that — swiss
                                  restraint, the grid does the talking.
  hero_generate(art, theme)    -> offline fallback: flat geometric poster art on
                                  paper (dot matrix / concentric rings / metric
                                  bars / modular grid), IKB + greys only.

Output is a flat RGB PNG embedded as a native picture in the top image strip."""
from __future__ import annotations
import math
import random
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

# t2i prompt discipline: the caller supplies CONTENT only; the look enforces
# composition/colour here (and the strip crop again in hero_from_source()).
STYLE_SUFFIX = (
    "Ultra-minimal editorial studio photograph in the Swiss International Style: "
    "a single clean subject placed on the right two-thirds, ultra-wide panoramic "
    "strip composition, subject centered in the safe middle band, vast empty "
    "seamless background in warm paper white and light grey, soft diffused "
    "lighting, precise geometry, muted near-monochrome palette with one deep "
    "cobalt blue accent, high-end print quality. No text, no letters, no "
    "watermark, no people, no clutter."
)

# the hero template's image slot is 1280x412 — render at 1600x515 (same ratio)
STRIP_W, STRIP_H = 1600, 515


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hero_from_source(src_path: str, theme, out_path: str, dot: int = 0):
    """Crop to the strip and mute: swiss photos are calm, never filtered loud."""
    img = Image.open(src_path).convert("RGB")
    img = ImageOps.fit(img, (STRIP_W, STRIP_H), Image.LANCZOS, centering=(0.5, 0.42))
    img = ImageEnhance.Color(img).enhance(0.88)
    img = ImageEnhance.Contrast(img).enhance(1.04)
    img.save(out_path)
    return out_path


def hero_generate(art: str, theme, out_path: str, w: int = STRIP_W, h: int = STRIP_H):
    """Flat geometric poster: paper field + one IKB construction. Motifs:
    dots (halftone-free dot matrix), rings (concentric hairlines),
    bars (metric strokes), grid (modular squares). Unknown art -> hashed pick."""
    c = theme.colors
    paper, ink, ikb = _rgb(c["bg-content"]), _rgb(c["ink"]), _rgb(c["accent"])
    grey1, grey2 = _rgb(c["grey-1"]), _rgb(c["grey-2"])
    motifs = ("dots", "rings", "bars", "grid")
    if art not in motifs:
        art = motifs[sum(ord(x) for x in (art or "swiss")) % len(motifs)]
    rnd = random.Random(sum(ord(x) for x in art))

    img = Image.new("RGB", (w, h), paper)
    d = ImageDraw.Draw(img)
    # faint modular grid over the whole strip (the swiss substrate)
    for gx in range(0, w, 100):
        d.line([(gx, 0), (gx, h)], fill=grey1, width=1)
    for gy in range(0, h, 100):
        d.line([(0, gy), (w, gy)], fill=grey1, width=1)

    cx = int(w * 0.66)  # construction sits right-of-centre; left stays calm
    if art == "dots":
        step = 34
        for iy in range(step // 2, h, step):
            for ix in range(int(w * 0.38), w - 40, step):
                t = (ix - w * 0.38) / (w * 0.62)
                r = 2 + 8 * (t ** 1.6)
                if rnd.random() < 0.94:
                    d.ellipse([ix - r, iy - r, ix + r, iy + r], fill=ikb)
        d.rectangle([80, h - 96, 80 + 220, h - 92], fill=ink)
    elif art == "rings":
        cy = h // 2
        for i, r in enumerate(range(40, int(h * 1.05), 44)):
            wd = 3 if i % 3 == 0 else 1
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ikb, width=wd)
        d.rectangle([cx - 5, cy - 5, cx + 5, cy + 5], fill=ink)
        d.rectangle([80, h - 96, 80 + 220, h - 92], fill=ink)
    elif art == "bars":
        n, bw = 14, 26
        x0 = int(w * 0.40)
        for i in range(n):
            bh = int(h * (0.18 + 0.68 * abs(math.sin(i * 0.9 + 1.2)) * rnd.uniform(0.75, 1.0)))
            x = x0 + i * int((w * 0.56) / n)
            col = ikb if i % 4 != 3 else ink
            d.rectangle([x, h - 60 - bh, x + bw, h - 60], fill=col)
        d.line([(x0 - 20, h - 60), (w - 60, h - 60)], fill=ink, width=2)
    else:  # grid
        cell = 86
        x0, y0 = int(w * 0.42), 40
        for iy in range(5):
            for ix in range(10):
                x, y = x0 + ix * cell, y0 + iy * cell
                if x + cell > w - 40 or y + cell > h - 40:
                    continue
                v = rnd.random()
                if v < 0.16:
                    d.rectangle([x + 8, y + 8, x + cell - 8, y + cell - 8], fill=ikb)
                elif v < 0.3:
                    d.ellipse([x + 10, y + 10, x + cell - 10, y + cell - 10], outline=ink, width=2)
                elif v < 0.4:
                    d.rectangle([x + 8, y + 8, x + cell - 8, y + cell - 8], outline=grey2, width=1)
        d.rectangle([80, h - 96, 80 + 220, h - 92], fill=ink)

    img.save(out_path)
    return out_path
