"""Image-mode hooks for the riso look (the engine's look-art contract).

  STYLE_SUFFIX                 -> appended to every t2i content prompt so the
                                  generated source already matches the look.
  hero_from_source(src, theme) -> take ANY photo/illustration and screen-print it:
                            duotone (luminance -> 2-colour ramp) + halftone dots
                            + misregistration, on paper. Use when a source image
                            is available (user photo, AI render, …).

  hero_generate(seed, theme)   -> generate riso poster art from scratch (no source):
                            halftone sun + layered duotone hills + grain, with a
                            calm zone for overlay type. Used by the `hero` archetype.

Output is a flat RGB PNG embedded full-bleed as a native picture; text is laid
over it natively (with a scrim for legibility)."""
from __future__ import annotations
import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageChops

# t2i prompt discipline: the model only gets the CONTENT from the caller; the
# look enforces composition/colour here (and again in hero_from_source()).
STYLE_SUFFIX = (
    "Flat screen-print poster illustration, bold stencil-cut silhouette shapes, "
    "minimal graphic composition, two flat ink colours on a plain warm-paper "
    "background, thick simple shapes, generous negative space. The left 45% of "
    "the frame is empty plain paper reserved for typography overlay; the main "
    "motif occupies the right side. No text, no letters, no watermark, "
    "no gradients, no photorealism."
)


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _dots(draw, density, bbox, dot, color):
    """Halftone screen: fill bbox with ink dots whose radius tracks density()."""
    x0, y0, x1, y1 = bbox
    gy = y0
    while gy < y1:
        gx = x0
        while gx < x1:
            v = density(gx, gy)
            if v > 0.05:
                r = dot * 0.62 * (v ** 0.5)
                draw.ellipse([gx - r, gy - r, gx + r, gy + r], fill=color)
            gx += dot
        gy += dot


def _grain(img, amount=0.06):
    noise = Image.effect_noise(img.size, 22).convert("L")
    noise = ImageOps.autocontrast(noise)
    tint = Image.new("RGB", img.size, (26, 24, 21))
    return Image.blend(img, ImageChops.multiply(img, noise.convert("RGB")), amount)


def hero_generate(art: str, theme, out_path: str, w: int = 1600, h: int = 900):
    c = theme.colors
    paper, blue, pink, mustard, ink = (_rgb(c["bg-content"]), _rgb(c["blue"]),
                                       _rgb(c["pink"]), _rgb(c["mustard"]), _rgb(c["ink"]))
    rnd = random.Random(sum(ord(x) for x in art) if art else 7)
    ph = rnd.uniform(0, 6.28)
    base = Image.new("RGB", (w, h), paper)
    d = ImageDraw.Draw(base)
    dot = 11

    if art == "shanghai":
        # pink halftone sun behind the pearl-tower antenna (clear of the 56% scrim edge)
        cx, cy, cr = w * 0.685, h * 0.16, h * 0.24
        _dots(d, lambda x, y: max(0, 1 - math.hypot(x - cx, y - cy) / cr),
              (int(w * 0.57), 0, int(w * 0.85), int(h * 0.42)), dot, pink)
        ground = h * 0.86

        def skyline(dr, ox, oy, color):
            def R(x0, y0, x1, y1):
                dr.rectangle([x0 + ox, y0 + oy, x1 + ox, y1 + oy], fill=color)

            def P(pts):
                dr.polygon([(x + ox, y + oy) for x, y in pts], fill=color)

            def C(x, y, r):
                dr.ellipse([x - r + ox, y - r + oy, x + r + ox, y + r + oy], fill=color)

            tx = w * 0.72
            # oriental pearl: tripod legs / column / two spheres / antenna
            P([(tx - 100, ground), (tx - 64, ground), (tx + 12, h * 0.60), (tx - 12, h * 0.60)])
            P([(tx + 64, ground), (tx + 100, ground), (tx + 12, h * 0.60), (tx - 12, h * 0.60)])
            R(tx - 14, h * 0.56, tx + 14, ground)
            C(tx, h * 0.585, 64)
            R(tx - 9, h * 0.335, tx + 9, h * 0.56)
            C(tx, h * 0.335, 40)
            R(tx - 4, h * 0.155, tx + 4, h * 0.30)
            C(tx, h * 0.15, 13)
            # stepped tower (jinmao-ish)
            bx = tx + 152
            R(bx, h * 0.47, bx + 76, ground)
            R(bx + 13, h * 0.395, bx + 63, h * 0.47)
            R(bx + 27, h * 0.335, bx + 49, h * 0.395)
            P([(bx + 30, h * 0.335), (bx + 46, h * 0.335), (bx + 38, h * 0.265)])
            # slanted-top slab (swfc-ish)
            bx2 = tx + 274
            P([(bx2, ground), (bx2, h * 0.43), (bx2 + 68, h * 0.355), (bx2 + 68, ground)])
            bx3 = tx + 386
            R(bx3, h * 0.52, bx3 + 58, ground)
            R(bx3 + 74, h * 0.61, bx3 + 118, ground)
            # low cluster on the left edge of the skyline (title zone stays calm)
            R(w * 0.545, h * 0.63, w * 0.585, ground)
            R(w * 0.598, h * 0.555, w * 0.648, ground)
            R(w * 0.660, h * 0.665, w * 0.684, ground)

        for color, ox, oy in ((pink, -7, -7), (blue, 0, 0)):
            skyline(d, ox, oy, color)
        # punched paper scanlines — screen-print banding across the silhouettes
        yy = h * 0.50
        while yy < ground - 14:
            d.rectangle([w * 0.545, yy, w, yy + 2], fill=paper)
            yy += 24
        # mustard sun-core (graphic punctuation), ink keyline
        d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=mustard, outline=ink, width=4)
        # huangpu river: halftone band under the horizon
        d.rectangle([0, ground - 3, w, ground], fill=ink)
        _dots(d, lambda x, y: max(0.0, (y - ground) / max(1, h - ground)) * 0.55,
              (0, int(ground), w, h), dot, blue)
    elif art == "vanity":
        # backdrop: large pink halftone disc, centre-right (clear of the 56% scrim edge)
        cx, cy, cr = w * 0.76, h * 0.40, h * 0.335
        _dots(d, lambda x, y: max(0, 1 - math.hypot(x - cx, y - cy) / cr) * 0.9,
              (int(w * 0.57), int(h * 0.02), w, int(h * 0.84)), dot, pink)
        base_y = h * 0.80

        def objects(dr, ox, oy, color):
            def R(x0, y0, x1, y1):
                dr.rectangle([x0 + ox, y0 + oy, x1 + ox, y1 + oy], fill=color)

            def P(pts):
                dr.polygon([(x + ox, y + oy) for x, y in pts], fill=color)

            def C(x, y, r):
                dr.ellipse([x - r + ox, y - r + oy, x + r + ox, y + r + oy], fill=color)

            fx = w * 0.575                      # perfume flask
            R(fx, h * 0.40, fx + 132, base_y)
            P([(fx, h * 0.40), (fx + 132, h * 0.40), (fx + 97, h * 0.352), (fx + 35, h * 0.352)])
            R(fx + 52, h * 0.312, fx + 80, h * 0.352)
            R(fx + 44, h * 0.245, fx + 88, h * 0.312)
            lx = w * 0.665                      # lipstick
            R(lx, h * 0.565, lx + 58, base_y)
            R(lx + 8, h * 0.518, lx + 50, h * 0.565)
            P([(lx + 11, h * 0.518), (lx + 47, h * 0.518), (lx + 47, h * 0.398), (lx + 11, h * 0.452)])
            C(w * 0.845, h * 0.615, 94)         # compact mirror
            wx = w * 0.938                      # mascara
            R(wx, h * 0.42, wx + 26, base_y)
            R(wx - 5, h * 0.358, wx + 31, h * 0.42)

        for color, ox, oy in ((pink, -7, -7), (blue, 0, 0)):
            objects(d, ox, oy, color)
        # compact: paper ring + pink halftone powder face
        mx, my = w * 0.845, h * 0.615
        d.ellipse([mx - 72, my - 72, mx + 72, my + 72], fill=paper)
        _dots(d, lambda x, y: max(0, 1 - math.hypot(x - mx, y - my) / 68),
              (int(mx - 68), int(my - 68), int(mx + 68), int(my + 68)), 9, pink)
        # perfume glass highlight (punched paper stripe)
        d.rectangle([w * 0.575 + 20, h * 0.425, w * 0.575 + 36, base_y - 20], fill=paper)
        # lipstick bullet re-struck in mustard (third colour, ink keyline)
        lx = w * 0.665
        d.polygon([(lx + 11, h * 0.518), (lx + 47, h * 0.518), (lx + 47, h * 0.398), (lx + 11, h * 0.452)],
                  fill=mustard, outline=ink)
        # vanity-table baseline
        d.rectangle([w * 0.56, base_y, w * 0.985, base_y + 5], fill=ink)
    elif art == "city":
        # pink halftone moon top-right
        cx, cy, cr = w * 0.80, h * 0.20, h * 0.30
        _dots(d, lambda x, y: max(0, 1 - math.hypot(x - cx, y - cy) / cr),
              (int(w * 0.5), 0, w, int(h * 0.55)), dot, pink)
        # skyline: vertical building bars, blue with pink misregistration
        n = 13
        bw = w / n
        tops = [h * (0.42 + 0.34 * rnd.random()) for _ in range(n)]
        for layer_color, ox, oy in ((pink, -6, -6), (blue, 0, 0)):
            for i in range(n):
                if (i + 1) / n < 0.42:      # keep the left calm for the title
                    continue
                bx0, bx1, top = i * bw, (i + 1) * bw - 6, tops[i]
                _dots(d, lambda x, y: 0.92, (int(bx0) + ox, int(top) + oy, int(bx1) + ox, h + oy), dot, layer_color)
    else:
        # halftone sun (pink), bleeding off the top-right
        cx, cy, cr = w * 0.80, h * 0.15, h * 0.48
        _dots(d, lambda x, y: max(0, 1 - math.hypot(x - cx, y - cy) / cr),
              (int(w * 0.42), 0, w, int(h * 0.74)), dot, pink)
        # two duotone hills sweeping up to the right, blue over an offset pink ghost
        def hill(amp, base_y, freq, phase):
            def dens(x, y):
                yb = base_y + math.sin(x / w * math.pi * freq + phase) * amp - (x / w) * h * 0.16
                return 0.9 if y > yb else 0.0
            return dens
        for color, ox, oy in ((pink, -7, -7), (blue, 0, 0)):
            _dots(d, hill(h * 0.05, h * 0.66, 2.1, ph), (int(w * 0.40) + ox, int(h * 0.4), w + ox, h + oy), dot, color)
        _dots(d, hill(h * 0.04, h * 0.80, 3.0, ph + 2), (int(w * 0.40), int(h * 0.55), w, h), dot, blue)

    if art not in ("shanghai", "vanity"):
        # hard-edge mustard accent square (graphic punctuation)
        sx, sy, ss = w * 0.62, h * 0.12, h * 0.11
        d.rectangle([sx, sy, sx + ss, sy + ss], fill=mustard, outline=ink, width=4)

    base = _grain(base)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    base.save(out_path)
    return out_path


def hero_from_source(src_path: str, theme, out_path: str, dot: int = 7):
    """Screen-print an existing image as a true two-plate separation:
    dark tones -> blue plate, mid tones -> pink plate (offset = misregistration),
    highlights stay clean paper. Generic for any source (photo / t2i render)."""
    c = theme.colors
    paper, blue, pink = _rgb(c["bg-content"]), _rgb(c["blue"]), _rgb(c["pink"])
    src = Image.open(src_path).convert("L")
    w, h = src.size
    src = ImageOps.autocontrast(src)
    px = src.load()
    out = Image.new("RGB", (w, h), paper)
    d = ImageDraw.Draw(out)

    def darkness(x, y):
        return (255 - px[min(max(x, 0), w - 1), min(max(y, 0), h - 1)]) / 255.0

    def pink_plate(x, y):        # band-pass around the mid tones (e.g. a sun disc)
        v = 1 - abs(darkness(x, y) - 0.40) / 0.17
        return v if v > 0.22 else 0.0    # floor kills paper-vignette speckle

    def blue_plate(x, y):        # dark tones only; paper stays clean
        return max(0.0, (darkness(x, y) - 0.48) / 0.52)

    _dots(d, lambda x, y: pink_plate(x + 6, y + 6), (-6, -6, w, h), dot, pink)
    _dots(d, blue_plate, (0, 0, w, h), dot, blue)
    out = _grain(out)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    return out_path
