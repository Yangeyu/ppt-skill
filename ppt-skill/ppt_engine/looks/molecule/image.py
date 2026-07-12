"""Image-mode for the Molecule look.

签名视觉 = 紫蓝渐变分子气泡（景深虚化的玻璃球簇），全部走同一套 PIL 算法：
  BUBBLE_ASSETS    -> 预生成的透明 PNG 气泡簇（import 时按需生成到 ./assets/，
                      确定性构图），路径注册进 look.icons，模板经
                      data-ppt="image" data-src 原生嵌入。
                      ⚠ 资产必须完整落在视口内,禁止负偏移出血定位
                      （元素超出视口时 Playwright 元素截图退化为整页截图）。
  make_hero        -> 无源图时的程序化兜底：同款气泡簇构图,
                      左 50% 留浅底给文字,主簇收在右侧。
  molecule_ify     -> 任意源图（t2i / 照片）统一收敛：轻降饱和 + 提亮 +
                      冷雾罩 matte,再按宽高比烤蒙版——
                      方图→圆形图窗,纵图→圆角矩形,横图(封面)→左半白雾
                      （封面文字压图的可读性不依赖模型构图自觉）。
"""
from __future__ import annotations
import base64
import math
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps

ASSET_DIR = Path(__file__).parent / "assets"


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _colors(theme) -> dict:
    return theme.render_colors() if hasattr(theme, "render_colors") else theme.colors


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# 气泡三档色相（与 SpecLock 令牌同源;气泡是栅格资产,写死无碍换色纪律）
_PURPLE = ((186, 174, 245), (94, 78, 196))     # light -> dark
_VIOLET = ((172, 176, 246), (86, 96, 210))
_BLUE = ((158, 198, 248), (56, 110, 208))
_RAMPS = {"p": _PURPLE, "v": _VIOLET, "b": _BLUE}


# ---------------------------------------------------------------- PIL 气泡
def _sphere(d: int, ramp, alpha: int = 255) -> Image.Image:
    """一颗玻璃球 sprite：偏心径向渐变 + 左上高光 + 圆形蒙版（RGBA）。"""
    c_light, c_dark = ramp
    ss = 3
    D = d * ss
    img = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    steps = 56
    hx, hy = D * 0.40, D * 0.34          # 明部中心（左上）
    for i in range(steps, 0, -1):
        t = i / steps
        col = _lerp(c_light, c_dark, t ** 1.15)
        r = (D / 2) * t
        cx = D / 2 + (hx - D / 2) * (1 - t)
        cy = D / 2 + (hy - D / 2) * (1 - t)
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (255,))
    # 高光
    hl = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([D * 0.20, D * 0.12, D * 0.48, D * 0.32],
                               fill=(255, 255, 255, 150))
    img = Image.alpha_composite(img, hl.filter(ImageFilter.GaussianBlur(D * 0.045)))
    # 圆形蒙版（叠 alpha,保留高光/整体透明度）
    mask = Image.new("L", (D, D), 0)
    ImageDraw.Draw(mask).ellipse([1, 1, D - 2, D - 2], fill=alpha)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), mask))
    return img.resize((d, d), Image.LANCZOS)


_PAPER = (247, 247, 251)   # 与 SpecLock bg-content 同源(栅格资产写死无碍换色纪律)


def _haze(sp: Image.Image, k: float) -> Image.Image:
    """空气透视:虚化球的颜色向纸色混合 k,越糊越淡,融进高调底。"""
    r, g, b, a = sp.split()
    rgb = Image.blend(Image.merge("RGB", (r, g, b)),
                      Image.new("RGB", sp.size, _PAPER), k)
    return Image.merge("RGBA", (*rgb.split(), a))


def _compose(size: tuple[int, int], items: list) -> Image.Image:
    """按绘制谱构图(列表序 = z 序),坐标为逻辑像素,2x 出图。
      ("s", cx, cy, d, ramp, blur, alpha)      球:blur 模拟景深——
          0=对焦(锐利高光),10-20=背景虚化,30+=前景散景(化成色雾);
          blur≥8 时自动做空气透视(颜色向纸色混合)。
      ("b", x1, y1, x2, y2, halfw, ramp, alpha) 键:对焦分子链的球间短圆柱,
          画在链球之前(z 在下),两端被球盖住——参考模板的分子模型感来源。"""
    w, h = size
    canvas = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    for it in items:
        if it[0] == "b":
            _, x1, y1, x2, y2, hw, ramp, alpha = it
            ang = math.atan2(y2 - y1, x2 - x1)
            dx, dy = math.sin(ang) * hw * 2, -math.cos(ang) * hw * 2
            c_l, c_d = _RAMPS[ramp]
            layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).polygon(
                [(x1 * 2 + dx, y1 * 2 + dy), (x2 * 2 + dx, y2 * 2 + dy),
                 (x2 * 2 - dx, y2 * 2 - dy), (x1 * 2 - dx, y1 * 2 - dy)],
                fill=_lerp(c_l, c_d, 0.62) + (alpha,))
            canvas.alpha_composite(layer)
            continue
        _, cx, cy, d, ramp, blur, alpha = it
        sp = _sphere(int(d * 2), _RAMPS[ramp], alpha)
        if blur >= 8:
            sp = _haze(sp, min(0.5, blur / 70))
        if blur:
            pad = int(blur * 6)
            padded = Image.new("RGBA", (sp.width + pad * 2,) * 2, (0, 0, 0, 0))
            padded.paste(sp, (pad, pad))
            sp = padded.filter(ImageFilter.GaussianBlur(blur * 2))
        canvas.alpha_composite(sp, (int(cx * 2 - sp.width / 2), int(cy * 2 - sp.height / 2)))
    return canvas


# 构图谱：name -> (逻辑尺寸, 绘制列表)。三层景深(对标参考模板封面):
# 底=前/背景散景(blur 30+,化成色雾) → 中=背景虚化(blur 10-20) →
# 键+对焦分子链(blur 0,锐利高光) → 锐利小卫星。列表序即 z 序。
_BUBBLE_SPECS = {
    # 封面/兜底主簇(980×720):中央对焦分子链,四角大散景
    "mol-hero": ((980, 720), [
        ("s", 195, 545, 220, "v", 22, 115),
        ("s", 785, 520, 260, "b", 24, 110),
        ("s", 132, 145, 150, "p", 18, 130),
        ("s", 862, 125, 130, "b", 16, 125),
        ("s", 620, 88, 90, "v", 12, 130),
        ("s", 200, 380, 56, "b", 8, 150),
        ("s", 760, 420, 70, "p", 10, 150),
        ("b", 430, 150, 530, 260, 15, "v", 235),
        ("b", 530, 260, 450, 370, 15, "v", 235),
        ("b", 450, 370, 600, 450, 12, "b", 230),
        ("b", 530, 260, 640, 300, 14, "b", 230),
        ("s", 430, 150, 105, "p", 0, 250),
        ("s", 530, 260, 72, "v", 0, 245),
        ("s", 450, 370, 125, "b", 0, 250),
        ("s", 600, 450, 56, "p", 0, 240),
        ("s", 640, 300, 88, "b", 0, 248),
        ("s", 320, 240, 34, "b", 0, 230),
        ("s", 700, 180, 26, "v", 0, 225),
        ("s", 560, 540, 40, "p", 2, 205),
        ("s", 280, 500, 22, "v", 0, 215),
    ]),
    # 章节/收尾竖簇(700×720):竖向对焦链,下缘散景
    "mol-side": ((700, 720), [
        ("s", 522, 542, 220, "p", 18, 112),
        ("s", 172, 512, 180, "b", 16, 118),
        ("s", 140, 104, 110, "v", 12, 130),
        ("b", 420, 120, 330, 250, 15, "v", 235),
        ("b", 330, 250, 470, 340, 15, "b", 232),
        ("b", 470, 340, 380, 480, 13, "b", 230),
        ("b", 380, 480, 520, 560, 13, "p", 228),
        ("s", 420, 120, 120, "p", 0, 248),
        ("s", 330, 250, 80, "v", 0, 242),
        ("s", 470, 340, 140, "b", 0, 250),
        ("s", 380, 480, 70, "p", 0, 240),
        ("s", 520, 560, 100, "v", 0, 245),
        ("s", 250, 180, 36, "b", 0, 225),
        ("s", 600, 220, 44, "v", 0, 230),
        ("s", 250, 620, 28, "b", 1, 200),
        ("s", 600, 430, 26, "p", 0, 220),
    ]),
    # 角部点缀小簇(430×300)
    "mol-corner": ((430, 300), [
        ("s", 128, 176, 108, "v", 12, 118),
        ("s", 342, 92, 80, "b", 10, 122),
        ("b", 290, 110, 200, 190, 11, "v", 230),
        ("b", 200, 190, 330, 220, 10, "b", 228),
        ("s", 290, 110, 90, "p", 0, 245),
        ("s", 200, 190, 60, "b", 0, 238),
        ("s", 330, 220, 70, "v", 0, 240),
        ("s", 120, 80, 30, "b", 0, 220),
        ("s", 380, 270, 24, "p", 0, 210),
    ]),
}


def _ring(size: int = 1000, paper: str = "#F7F7FB") -> Image.Image:
    """圆环遮罩:四角纸色、圆心透明。盖在 hero 图窗上,方图(兜底)与
    圆形蒙版图(t2i 后处理)都稳定呈现圆窗。"""
    ss = 4
    D = size * ss
    img = Image.new("RGBA", (D, D), _rgb(paper) + (255,))
    hole = Image.new("L", (D, D), 255)
    ImageDraw.Draw(hole).ellipse([ss, ss, D - ss - 1, D - ss - 1], fill=0)
    img.putalpha(hole)
    return img.resize((size, size), Image.LANCZOS)


def _fade(img: Image.Image, k: float) -> Image.Image:
    out = img.copy()
    out.putalpha(out.getchannel("A").point(lambda a: int(a * k)))
    return out


def _assets() -> dict[str, str]:
    """按需生成资产 PNG（确定性构图,重复调用直接复用）。
    每个构图谱同时产出镜像(-l)与淡化(-soft/-soft-l)变体——
    CSS transform/opacity 不进原生导出,变体必须在资产层烤好。"""
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    out: dict[str, str] = {}
    for name, (size, bubbles) in _BUBBLE_SPECS.items():
        variants = {name: None}
        if name != "mol-hero":
            variants[f"{name}-l"] = ("mirror",)
        if name == "mol-corner":
            variants[f"{name}-soft"] = ("fade",)
            variants[f"{name}-soft-l"] = ("mirror", "fade")
        missing = [v for v in variants if not (ASSET_DIR / f"{v}.png").exists()]
        if missing:
            base = _compose(size, bubbles)
            for v in missing:
                img = base
                ops = variants[v] or ()
                if "mirror" in ops:
                    img = ImageOps.mirror(img)
                if "fade" in ops:
                    img = _fade(img, 0.5)
                img.save(ASSET_DIR / f"{v}.png")
        for v in variants:
            p = ASSET_DIR / f"{v}.png"
            out[f"{v}.png"] = str(p)
            # 浏览器预览要真实显图:set_content 页面加载不了 file:// 子资源,
            # 静态装饰以 data URI 双注册("<name>.b64"),模板作 background-image 用
            out[f"{v}.b64"] = base64.b64encode(p.read_bytes()).decode()
    ring = ASSET_DIR / "mol-ring.png"
    if not ring.exists():
        _ring().save(ring)
    out["mol-ring.png"] = str(ring)
    out["mol-ring.b64"] = base64.b64encode(ring.read_bytes()).decode()
    return out


BUBBLE_ASSETS = _assets()


# ---------------------------------------------------------------- 兜底 hero
def make_hero(art: str, theme, out_path: str, w: int = 1664, h: int = 928):
    """程序化兜底：浅底 + 右侧气泡主簇,左 50% 留白给文字。"""
    c = _colors(theme)
    base = Image.new("RGB", (w, h), _rgb(c["bg-content"]))
    rnd = sum(ord(x) for x in art) if art else 7
    # 远景小球（左侧,极淡）
    far = [("s", w * 0.14, h * (0.18 + (rnd % 5) * 0.04), 36, "v", 5, 90),
           ("s", w * 0.30, h * 0.72, 52, "b", 6, 80),
           ("s", w * 0.07, h * 0.60, 24, "p", 4, 90)]
    # 右侧主簇（把 mol-hero 谱平移进右半幅）
    _, items = _BUBBLE_SPECS["mol-hero"]
    ox, oy, k = w * 0.44, h * 0.10, 0.9
    main = []
    for it in items:
        if it[0] == "s":
            _, cx, cy, d, r, b, a = it
            main.append(("s", cx * k + ox, cy * k + oy, d * k, r, b, a))
        else:
            _, x1, y1, x2, y2, hw, r, a = it
            main.append(("b", x1 * k + ox, y1 * k + oy, x2 * k + ox, y2 * k + oy, hw * k, r, a))
    layer = _compose((w, h), far + main)
    layer = layer.resize((w, h), Image.LANCZOS)
    base.paste(layer, (0, 0), layer)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    base.save(out_path)
    return out_path


# ---------------------------------------------------------------- 后处理
def _rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    ss = 4
    m = Image.new("L", (size[0] * ss, size[1] * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] * ss - 1, size[1] * ss - 1],
                                        radius=radius * ss, fill=255)
    return m.resize(size, Image.LANCZOS)


def molecule_ify(src_path: str, theme, out_path: str):
    """任意源图统一收敛进 molecule 的高调冷灰语言,并按宽高比烤蒙版:
    方图(hero 圆窗)→圆形透明蒙版;纵图(bullets 插图列)→圆角矩形蒙版;
    横图(封面全出血)→左 55% 烤白雾,保证压图文字可读。"""
    c = _colors(theme)
    img = Image.open(src_path).convert("RGB")
    w, h = img.size
    # 高调 matte：轻降饱和 + 提亮 + 提黑（收敛杂图,不破坏紫蓝主色）
    img = ImageEnhance.Color(img).enhance(0.86)
    img = ImageEnhance.Brightness(img).enhance(1.04)
    img = img.point(lambda v: int(24 + v * (248 - 24) / 255))
    # 冷雾罩
    veil = Image.new("RGB", (w, h), _rgb(c["bg-content"]))
    img = Image.blend(img, veil, 0.06)

    ar = w / h
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    if 0.92 <= ar <= 1.08:                       # 方图 -> 圆形图窗
        m = Image.new("L", (w * 2, h * 2), 0)
        ImageDraw.Draw(m).ellipse([2, 2, w * 2 - 3, h * 2 - 3], fill=255)
        img = img.convert("RGBA")
        img.putalpha(m.resize((w, h), Image.LANCZOS))
        img.save(out_path)
    elif ar < 0.92:                              # 纵图 -> 圆角矩形
        img = img.convert("RGBA")
        img.putalpha(_rounded_mask((w, h), max(20, int(w * 0.07))))
        img.save(out_path)
    else:                                        # 横图(封面) -> 左半白雾
        paper = _rgb(c["bg-content"])
        grad = Image.new("L", (w, 1))
        solid, fade = int(w * 0.42), int(w * 0.66)
        for x in range(w):
            if x < solid:
                a = 236
            elif x < fade:
                t = (x - solid) / (fade - solid)
                a = int(236 * (1 - t) ** 1.6)
            else:
                a = 0
            grad.putpixel((x, 0), a)
        scrim = Image.new("RGB", (w, h), paper)
        img.paste(scrim, (0, 0), grad.resize((w, h)))
        img.save(out_path)
    return out_path


# ---- t2i 风格纪律（拼在任意内容 prompt 之后;engine 经 genimage 使用） ----
STYLE_SUFFIX = (
    "Minimal clean 3D render, glossy translucent spheres and soft molecular "
    "forms in a purple-to-blue gradient palette, floating on a bright pale "
    "grey-white seamless studio background, high-key lighting, shallow depth "
    "of field with a few softly blurred bubbles in the foreground, generous "
    "negative space, elegant scientific biotech aesthetic, main subject "
    "composed around the centre-right of the frame. No text, no letters, "
    "no logos, no watermark, no harsh shadows, no dark background."
)
