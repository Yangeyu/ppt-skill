"""Image-mode for the Morandi look.

签名视觉 = 干笔刷（dry brush）肌理，全部走同一套 PIL 算法：
  BRUSH_ASSETS     -> 预生成的透明 PNG 构图（import 时按需生成到 ./assets/，
                      确定性种子），路径注册进 look.icons，模板经
                      data-ppt="image" data-src 原生嵌入。
                      ⚠ 不要用 data-ppt="icon" + 负偏移出血定位：元素一旦超出
                      视口，Playwright 元素截图会退化成整页截图，把整页内容
                      "烤进"图标 PNG 再缩放放回（幽灵重影，2026-07-05 实测）。
  make_hero        -> 无源图时的程序化兜底：同款笔刷交叉构图，
                      艺术区收在左 55%，右侧留纸白给文字。
  morandi_ify      -> 任意源图（照片 / t2i）统一莫兰迪化：降饱和 + 暖纸雾罩 +
                      matte 曲线（提黑压白），杂图收敛进同一套低饱和语言。
"""
from __future__ import annotations
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ASSET_DIR = Path(__file__).parent / "assets"


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _colors(theme) -> dict:
    return theme.render_colors() if hasattr(theme, "render_colors") else theme.colors


# 莫兰迪笔刷五色（与 SpecLock 令牌一致；笔刷是栅格资产，写死无碍换色纪律）
_GOLD, _PINK, _TAN, _SAGE, _BLUE = "#C8A25C", "#DFABA1", "#B89F90", "#C0C8C6", "#99A3B2"


# ---------------------------------------------------------------- PIL 笔刷
def _stroke(base: Image.Image, rng: random.Random, color_hex: str, cx, cy,
            length, width, angle, opacity=0.9):
    """一笔干刷 = 大量随机水平条痕（中间密、边缘枯），旋转后叠到画布。"""
    color = _rgb(color_hex)
    layer = Image.new("RGBA", (int(length), int(width)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    n = max(60, int(length * width / 110))
    for _ in range(n):
        y = rng.gauss(width / 2, width * 0.24)
        if not 0 <= y < width:
            continue
        edge = 1 - abs(y - width / 2) / (width / 2)
        l = max(6.0, rng.uniform(0.20, 1.0) * length * (0.28 + 0.72 * edge ** 1.2))
        x = rng.uniform(-l * 0.2, length - l * 0.8)
        h = rng.uniform(1.6, 4.2)
        a = int(255 * opacity * rng.uniform(0.30, 0.95) * (0.45 + 0.55 * edge))
        d.rectangle([x, y, x + l, y + h], fill=color + (a,))
    layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def _brush_png(path: Path, size: tuple[int, int], strokes: list, seed: int):
    """按笔画谱生成一张透明底笔刷构图 PNG（2x 尺寸出图保证清晰度）。"""
    w, h = size
    img = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    rng = random.Random(seed)
    for s in strokes:
        c, cx, cy, ln, wd, ang, op = s
        _stroke(img, rng, c, cx * 2, cy * 2, ln * 2, wd * 2, ang, op)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


# 笔画谱：name -> (逻辑尺寸, 笔画列表, seed)。坐标系 = 逻辑尺寸（模板里按此比例摆放）。
_BRUSH_SPECS = {
    # 满幅交叉构图（封面/章节/目录左区）760×760
    "brush-cross": ((760, 760), [
        (_GOLD, 440, 200, 660, 112, 45, 0.95),
        (_TAN, 210, 190, 540, 100, -48, 0.85),
        (_SAGE, 180, 480, 570, 108, -44, 0.85),
        (_PINK, 310, 570, 550, 96, 46, 0.90),
        (_BLUE, 150, 320, 430, 78, 88, 0.62),
        (_GOLD, 560, 560, 300, 60, 44, 0.70),
    ], 11),
    # 角部点缀 · 左上（驼+金）300×300
    "brush-tl": ((300, 300), [
        (_TAN, 60, 84, 320, 62, 45, 0.60),
        (_GOLD, 118, 44, 230, 40, 45, 0.45),
    ], 23),
    # 角部点缀 · 右下（粉+驼）300×300
    "brush-br": ((300, 300), [
        (_PINK, 226, 224, 320, 62, 45, 0.60),
        (_TAN, 172, 262, 220, 38, 45, 0.42),
    ], 37),
    # 横向一笔（分隔装饰）520×90
    "brush-line": ((520, 90), [
        (_GOLD, 260, 45, 480, 46, 0, 0.85),
    ], 51),
}


def _ensure_brush_assets() -> dict[str, str]:
    """import 时按需生成笔刷 PNG（确定性种子，幂等），返回 {键: 绝对路径}。"""
    out = {}
    for name, (size, strokes, seed) in _BRUSH_SPECS.items():
        p = ASSET_DIR / f"{name}.png"
        if not p.exists():
            _brush_png(p, size, strokes, seed)
        out[f"{name}.png"] = str(p)
    return out


# 路径经 look.icons 注入模板（data-ppt="image" data-src 原生嵌入）
BRUSH_ASSETS: dict[str, str] = _ensure_brush_assets()


def make_hero(art: str, theme, out_path: str, w: int = 1600, h: int = 900):
    """程序化兜底：暖纸 + 干笔刷交叉。艺术区收在左 55%（右侧纸白给原生文字）。"""
    c = _colors(theme)
    paper = _rgb(c["bg-content"])
    img = Image.new("RGBA", (w, h), paper + (255,))
    rng = random.Random(7)
    _stroke(img, rng, _GOLD, 620, 250, 920, 150, 45, 0.95)
    _stroke(img, rng, _TAN, 290, 240, 740, 135, -48, 0.85)
    _stroke(img, rng, _SAGE, 250, 640, 780, 145, -44, 0.85)
    _stroke(img, rng, _PINK, 430, 760, 760, 130, 46, 0.90)
    _stroke(img, rng, _BLUE, 190, 440, 560, 105, 88, 0.60)
    _stroke(img, rng, _GOLD, 760, 740, 420, 82, 44, 0.70)
    # 右下角小笔刷回应（不进右侧安静区上半）
    _stroke(img, rng, _PINK, w - 90, h - 70, 380, 76, 45, 0.55)
    out = img.convert("RGB")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    return out_path


def morandi_ify(src_path: str, theme, out_path: str):
    """任意源图统一莫兰迪化：降饱和 + 暖纸雾罩 + matte 曲线（提黑压白）。"""
    c = _colors(theme)
    paper = _rgb(c["bg-content"])
    img = Image.open(src_path).convert("RGB")
    img = ImageOps.autocontrast(img, cutoff=1)
    g = img.convert("L")
    img = Image.blend(img, Image.merge("RGB", (g, g, g)), 0.42)          # 降饱和
    img = Image.blend(img, Image.new("RGB", img.size, paper), 0.14)      # 暖雾罩
    lut = [int(30 + i * (230 - 30) / 255) for i in range(256)]           # matte
    img = img.point(lut * 3)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


# ---- t2i 风格纪律（拼在任意内容 prompt 之后；engine 经 genimage 使用） ----
STYLE_SUFFIX = (
    "Soft minimalist still life photograph in a muted Morandi color palette: "
    "dusty rose pink, warm sand beige, sage grey-green, powder blue-grey, low "
    "saturation matte tones, gentle diffused daylight, warm cream seamless "
    "background, generous negative space, main subject placed in the left "
    "half of the frame, right half almost empty plain warm cream. No text, "
    "no letters, no watermark, no logo, no people, no harsh shadows."
)
