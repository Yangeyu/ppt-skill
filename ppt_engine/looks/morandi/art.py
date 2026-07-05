"""Image-mode hooks for the morandi (小清新) look.

  STYLE_SUFFIX                 -> forces every t2i content prompt into the look:
                                  airy lifestyle still-life, pale sage backdrop,
                                  muted morandi palette, soft window light.
  hero_from_source(src, theme) -> crop ANY photo to the hero mat slot (532x402,
                                  ~4:3) and give it the milky morandi cast:
                                  lower saturation, lifted brightness, a whisper
                                  of warm-paper veil.
  hero_generate(art, theme)    -> offline fallback: hand-drawn botanical line art
                                  on cream — flora / leaves / blobs / waves.

Output is a flat RGB PNG shown inside the white photo mat on hero pages."""
from __future__ import annotations
import math
import random
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

# caller supplies CONTENT only; composition + palette live here
STYLE_SUFFIX = (
    "Soft airy lifestyle still-life photograph in a fresh Morandi palette: the "
    "subject arranged simply on a warm white surface against a pale sage-green "
    "seamless backdrop, gentle diffused window light, muted low-saturation "
    "colors of sage green, cream, dusty terracotta, generous negative space, "
    "delicate soft shadows, high-end home magazine quality. No text, no "
    "letters, no watermark, no people."
)

# hero template's photo slot is 532x402 inside the white mat — render at 2.5x
STRIP_W, STRIP_H = 1330, 1005


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hero_from_source(src_path: str, theme, out_path: str, dot: int = 0):
    """Crop to the mat slot and quiet the photo into morandi milkiness."""
    img = Image.open(src_path).convert("RGB")
    img = ImageOps.fit(img, (STRIP_W, STRIP_H), Image.LANCZOS, centering=(0.5, 0.45))
    img = ImageEnhance.Color(img).enhance(0.8)
    img = ImageEnhance.Brightness(img).enhance(1.03)
    img = ImageEnhance.Contrast(img).enhance(0.97)
    veil = Image.new("RGB", img.size, _rgb(theme.colors["paper"]))
    img = Image.blend(img, veil, 0.06)
    img.save(out_path)
    return out_path


def _bezier(d, pts, color, width):
    """Plot a cubic bezier as short segments (PIL has no native curves)."""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts
    prev = (x0, y0)
    for i in range(1, 33):
        t = i / 32
        u = 1 - t
        x = u**3 * x0 + 3 * u**2 * t * x1 + 3 * u * t**2 * x2 + t**3 * x3
        y = u**3 * y0 + 3 * u**2 * t * y1 + 3 * u * t**2 * y2 + t**3 * y3
        d.line([prev, (x, y)], fill=color, width=width)
        prev = (x, y)


def _umbel(d, x, y, h, color, rnd, width=3):
    """One dill-style umbel: curved stem + radial spokes tipped with seeds."""
    top = (x + rnd.uniform(-h * .06, h * .06), y - h)
    _bezier(d, [(x, y), (x + h * .04, y - h * .38), (x - h * .05, y - h * .66), top], color, width)
    for k in range(rnd.randint(7, 9)):
        ang = math.pi * (0.15 + 0.7 * k / 8) + rnd.uniform(-.06, .06)
        L = h * rnd.uniform(.16, .26)
        ex, ey = top[0] + L * math.cos(ang) * (1 if k % 2 else -1), top[1] - L * math.sin(ang) * .9
        _bezier(d, [top, (top[0], top[1] - L * .4), ((top[0] + ex) / 2, (top[1] + ey) / 2), (ex, ey)], color, width)
        r = h * .012 + 2
        d.ellipse([ex - r, ey - r, ex + r, ey + r], outline=color, width=width)


def hero_generate(art: str, theme, out_path: str, w: int = STRIP_W, h: int = STRIP_H):
    """Botanical poster on cream. Motifs: flora (umbel field), leaves (eucalyptus
    stems), blobs (morandi pebbles), waves (soft contour arcs)."""
    c = theme.colors
    paper, ink = _rgb(c["paper"]), _rgb(c["ink"])
    sage, sage_deep = _rgb(c["sage"]), _rgb(c["sage-deep"])
    green, terra = _rgb(c["accent"]), _rgb(c["accent-2"])
    motifs = ("flora", "leaves", "blobs", "waves")
    if art not in motifs:
        art = motifs[sum(ord(x) for x in (art or "fresh")) % len(motifs)]
    rnd = random.Random(sum(ord(x) for x in art))

    img = Image.new("RGB", (w, h), paper)
    d = ImageDraw.Draw(img)

    if art == "flora":
        # umbel meadow: a row of dill silhouettes, one terracotta star
        base = h * .92
        xs = [w * v for v in (.16, .3, .45, .58, .72, .86)]
        for i, x in enumerate(xs):
            hh = h * rnd.uniform(.42, .72)
            col = terra if i == 3 else (sage_deep if i % 2 else green)
            _umbel(d, x, base, hh, col, rnd)
        d.rectangle([w * .08, base + 8, w * .92, base + 12], fill=sage)
    elif art == "leaves":
        # eucalyptus stems: arcs with alternating round leaves
        for i, x0 in enumerate((w * .25, w * .5, w * .75)):
            col = green if i == 1 else sage_deep
            pts = [(x0, h * .95), (x0 + w * .06, h * .6), (x0 - w * .05, h * .35), (x0 + w * .02, h * .12)]
            _bezier(d, pts, col, 4)
            for t in range(1, 12):
                tt = t / 12
                u = 1 - tt
                lx = u**3 * pts[0][0] + 3 * u**2 * tt * pts[1][0] + 3 * u * tt**2 * pts[2][0] + tt**3 * pts[3][0]
                ly = u**3 * pts[0][1] + 3 * u**2 * tt * pts[1][1] + 3 * u * tt**2 * pts[2][1] + tt**3 * pts[3][1]
                r = h * .028 * (1 - tt * .5)
                off = r * 1.7 * (1 if t % 2 else -1)
                fill = terra if (i == 1 and t == 5) else (sage if t % 3 else None)
                d.ellipse([lx + off - r, ly - r, lx + off + r, ly + r],
                          fill=fill, outline=col, width=3)
    elif art == "blobs":
        # morandi pebble stack + one outline pebble
        def pebble(cx, cy, rx, ry, fill=None, outline=None):
            pts = []
            for k in range(48):
                a = 2 * math.pi * k / 48
                rr = 1 + 0.12 * math.sin(3 * a + rnd.random() * 6)
                pts.append((cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)))
            d.polygon(pts, fill=fill, outline=outline, width=4)
        pebble(w * .38, h * .52, w * .16, h * .22, fill=terra)
        pebble(w * .62, h * .62, w * .13, h * .18, fill=green)
        pebble(w * .52, h * .36, w * .11, h * .15, outline=ink)
        pebble(w * .74, h * .4, w * .07, h * .1, fill=sage)
        d.rectangle([w * .2, h * .88, w * .5, h * .885], fill=ink)
    else:  # waves
        # soft contour arcs stacked like hills
        for i in range(7):
            y0 = h * (.25 + .09 * i)
            col = terra if i == 3 else (green if i % 2 else sage_deep)
            _bezier(d, [(w * .06, y0), (w * .35, y0 - h * .1), (w * .65, y0 + h * .08), (w * .94, y0 - h * .04)], col, 4)
        d.ellipse([w * .78 - h * .06, h * .16 - h * .06, w * .78 + h * .06, h * .16 + h * .06],
                  fill=terra)

    img.save(out_path)
    return out_path
