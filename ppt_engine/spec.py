"""SpecLock — 现场生成并冻结的设计语言（v0.3 单一真源）。

它是 v0.2 `theme.py:Theme` 的演进：
 - 向后兼容：暴露 `colors / display_font / body_font / chart_palette / name` 与
   `css_vars() / families() / scheme() / color_slot()`，故 build/render/oox/fonts
   不改即可把 SpecLock 当 theme 用。
 - 新增（v0.3）：`type_scale`(模块化字阶) / `grid`(网格) / `image`(图像统一处理) /
   `motifs`(招牌母题) / `rules`(硬规则)，供设计系统套件实例化与评论官校验。

来源两条：`from_seed(theme_id, ...)` 从预置主题确定性派生（兜底/测试）；
或由艺术总监(LLM)直接产出 `SpecLock`（freedom）。两者都先过身份评论官再冻结。"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

from .theme import THEMES

# 可接受的模块化字阶比例（QUALITY ID-TS-1）
RATIOS = {
    "minor-third": 1.2, "major-third": 1.25, "perfect-fourth": 1.333,
    "perfect-fifth": 1.5, "golden": 1.618,
}

# SpecLock.colors 必须含的全部键（与模板 CSS 变量对齐，等于 theme.py 的键集）
COLOR_KEYS = [
    "bg", "bg-2", "bg-content", "ink", "muted", "hairline", "surface",
    "primary", "primary-2", "pos", "neg", "on-dark", "on-dark-muted", "glow",
]


class TypeScale(BaseModel):
    """模块化字阶（px）。所有页面字号只能取这几档。"""
    ratio: float = 1.5
    display: int = 84
    h1: int = 48
    h2: int = 32
    body: int = 22
    caption: int = 15
    micro: int = 12

    def sizes(self) -> dict[str, int]:
        return {"display": self.display, "h1": self.h1, "h2": self.h2,
                "body": self.body, "caption": self.caption, "micro": self.micro}

    def all_px(self) -> list[int]:
        return sorted(set(self.sizes().values()), reverse=True)


class Grid(BaseModel):
    cols: int = 12
    margin: int = 64          # 安全区（px）
    gutter: int = 24
    unit: int = 8             # 间距基准（8pt 网格）


class ImageTreatment(BaseModel):
    """全局图像统一处理——让一堆杂图协调的关键（借鉴 ppt-master duotone/screen-print）。"""
    style: Literal["none", "duotone", "screen-print", "grayscale", "warm"] = "none"
    css_filter: str = ""      # 应用到 <img> 的 CSS filter（screen-print 烤进图片）

    def css(self) -> str:
        if self.css_filter:
            return self.css_filter
        return {
            "none": "",
            "grayscale": "grayscale(1) contrast(1.05)",
            "warm": "sepia(.25) saturate(1.1)",
            "duotone": "grayscale(1) contrast(1.1)",      # 真 duotone 用 SVG feColorMatrix，这里近似
            "screen-print": "grayscale(1) contrast(1.4) brightness(1.05)",
        }.get(self.style, "")


class Motif(BaseModel):
    """艺术总监为本主题产出的招牌手法。html 是带 data-ppt 标记、只引用令牌变量的片段。"""
    name: str
    description: str = ""
    html: str = ""            # 创作轨可直接嵌入；必须带 data-ppt + 用 var(--*) / .t-*/.c-*


class SpecLock(BaseModel):
    id: str
    name: str
    colors: dict[str, str]                 # 见 COLOR_KEYS
    display_font: str
    body_font: str
    chart_palette: list[str]               # hex，无 '#'
    type_scale: TypeScale = Field(default_factory=TypeScale)
    grid: Grid = Field(default_factory=Grid)
    image: ImageTreatment = Field(default_factory=ImageTreatment)
    motifs: list[Motif] = []
    rules: list[str] = []
    rationale: str = ""
    embed_families: list[str] = []         # 需嵌入 pptx 的字族（默认 = families()）
    look: str = ""                         # 所属 look 包 id（"" = 无包身份，走默认结构库）
    font_vars: dict[str, str] = {}         # look 自定义字体 CSS 变量（font-display/font-mono/…）

    # ---- 向后兼容 theme.Theme 的接口 ----------------------------------
    def render_colors(self) -> dict[str, str]:
        """结构库（riso 版式）用到的扩展词汇补齐——身份可换、结构统一的关键：
        任何 SpecLock（seed / 现场生成）都能渲染 look 结构库而不出未定义变量。"""
        c = self.colors
        aliases = {
            "blue": c.get("primary"), "pink": c.get("primary-2"),
            "mustard": "#" + self.chart_palette[2] if len(self.chart_palette) > 2 else c.get("primary-2"),
            "black": c.get("ink"), "paper-2": c.get("surface"),
            "on-paper-muted": c.get("muted"),
        }
        return {**aliases, **c}

    def css_vars(self) -> str:
        """注入设计系统套件 :root —— 颜色 + 字体 + 字阶 + 网格。"""
        rows = [f"--{k}: {v};" for k, v in self.render_colors().items()]
        fv = {
            "font-serif": f'"{self.display_font}", "Songti SC", "STSong", serif',
            "font-sans": f'"{self.body_font}", "PingFang SC", '
                         '"Hiragino Sans GB", system-ui, sans-serif',
            # look 结构库的角色变量（look 可在 font_vars 覆盖）
            "font-display": f'"{self.display_font}", "PingFang SC", sans-serif',
            "font-body": f'"{self.body_font}", "PingFang SC", sans-serif',
            "font-mono": '"Space Mono", "Noto Sans SC", monospace',
            **self.font_vars,
        }
        rows += [f"--{k}: {v};" for k, v in fv.items()]
        for role, px in self.type_scale.sizes().items():
            rows.append(f"--type-{role}: {px}px;")
        rows.append(f"--grid-cols: {self.grid.cols};")
        rows.append(f"--space-unit: {self.grid.unit}px;")
        rows.append(f"--margin: {self.grid.margin}px;")
        rows.append(f"--img-filter: {self.image.css() or 'none'};")
        return ":root{\n  " + "\n  ".join(rows) + "\n}"

    def families(self) -> list[str]:
        out = [self.body_font]
        if self.display_font not in out:
            out.append(self.display_font)
        return out

    def scheme(self) -> dict:
        c = self.colors
        return {
            "dk1": c["ink"], "lt1": c["bg-content"],
            "dk2": c["bg"], "lt2": c["surface"],
            "accent1": c["primary"], "accent2": c["primary-2"],
            "accent3": "#" + self.chart_palette[2], "accent4": "#" + self.chart_palette[3],
            "accent5": "#" + self.chart_palette[4], "accent6": "#" + self.chart_palette[5],
            "hlink": c["primary"], "folHlink": c["primary-2"],
        }

    def color_slot(self) -> dict:
        """反查 'RRGGBB'(大写无#) -> schemeClr slot，让 render 发主题色引用（保一键换色）。"""
        c = self.colors
        hx = lambda v: v.lstrip("#").upper()
        return {
            hx(c["ink"]): "tx1", hx(c["bg-content"]): "bg1",
            hx(c["bg"]): "tx2", hx(c["surface"]): "bg2",
            hx(c["primary"]): "accent1", hx(c["primary-2"]): "accent2",
        }

    # ---- 令牌纪律：供身份评论官 / 创作轨校验 ---------------------------
    def allowed_hex(self) -> set[str]:
        """全部合规颜色（大写无#）——页面评论官用来判定 颜色 ∈ 令牌集。"""
        out = set()
        for v in self.render_colors().values():
            if isinstance(v, str) and v.startswith("#"):
                out.add(v.lstrip("#").upper())
        out |= {h.upper() for h in self.chart_palette}
        return out

    def embed_list(self) -> list[str]:
        """要嵌进 pptx 的全部字族。look 可带附加字面（如 Anton×思源黑 中西配对），
        它们不占 families() 的角色数（ID-FT-1 管的是角色，不是文件数）。"""
        return list(dict.fromkeys(self.embed_families)) if self.embed_families else self.families()

    def allowed_sizes(self) -> list[int]:
        return self.type_scale.all_px()

    # ---- 构造 ----------------------------------------------------------
    @classmethod
    def from_seed(cls, theme_id: str = "editorial", *, scale: TypeScale | None = None,
                  image: ImageTreatment | None = None, motifs: list[Motif] | None = None,
                  rules: list[str] | None = None, rationale: str = "") -> "SpecLock":
        """从预置主题/look 包确定性派生一份 SpecLock（兜底 / 测试 / freedom 的起点）。"""
        from .looks import LOOKS   # 懒导入防环（looks → spec）
        if theme_id in LOOKS:
            base = LOOKS[theme_id].spec
            return base.model_copy(update={
                k: v for k, v in {"type_scale": scale, "image": image, "motifs": motifs,
                                  "rules": rules, "rationale": rationale}.items() if v})
        t = THEMES[theme_id]
        return cls(
            id=t.id, name=t.name, colors=legibilize(dict(t.colors)),
            display_font=t.display_font, body_font=t.body_font,
            chart_palette=list(t.chart_palette),
            type_scale=scale or _SEED_SCALES.get(theme_id, TypeScale()),
            image=image or ImageTreatment(),
            motifs=motifs or [], rules=rules or [],
            rationale=rationale or f"seed:{theme_id}",
        )


def resolve_spec(spec) -> "SpecLock":
    """接受 SpecLock / look-id / theme-id 字符串，统一返回 SpecLock。
    未知 id 兜底到默认 look（当前唯一已优化的结构库）。"""
    if isinstance(spec, SpecLock):
        return spec
    if isinstance(spec, str):
        from .looks import LOOKS, DEFAULT_LOOK
        if spec in LOOKS or spec in THEMES:
            return SpecLock.from_seed(spec)
        return SpecLock.from_seed(DEFAULT_LOOK)
    raise TypeError(f"resolve_spec 不支持 {type(spec)}")


# 各 seed 主题的默认字阶（editorial 用更大的衬线巨号）
_SEED_SCALES = {
    "editorial": TypeScale(ratio=1.6, display=88, h1=53, h2=32, body=20, caption=15, micro=12),
    "aurora":    TypeScale(ratio=1.5, display=80, h1=48, h2=32, body=22, caption=15, micro=12),
    "ember":     TypeScale(ratio=1.5, display=80, h1=48, h2=32, body=22, caption=15, micro=12),
}


def expand_palette(minimal: dict[str, str]) -> dict[str, str]:
    """把艺术总监给的最小调色板（bg/paper/ink/muted/primary/accent[/pos/neg]）扩成
    SpecLock.colors 全键集，缺省键用合理派生填充——降低 LLM 出错面，保证模板变量齐全。"""
    bg = minimal.get("bg", "#1C1815")
    paper = minimal.get("paper", minimal.get("bg-content", "#F5F0E6"))
    ink = minimal.get("ink", "#211C18")
    muted = minimal.get("muted", "#8A7F70")
    primary = minimal.get("primary", "#C0392B")
    accent = minimal.get("accent", minimal.get("primary-2", "#A6703C"))
    full = {
        "bg": bg,
        "bg-2": minimal.get("bg-2", _shade(bg, 0.12)),
        "bg-content": paper,
        "ink": ink,
        "muted": muted,
        "hairline": minimal.get("hairline", _mix(paper, ink, 0.18)),
        "surface": minimal.get("surface", _shade(paper, -0.05)),
        "primary": primary,
        "primary-2": accent,
        "pos": minimal.get("pos", "#4F7A52"),
        "neg": minimal.get("neg", "#B23A2E"),
        "on-dark": minimal.get("on-dark", _mix(bg, paper, 0.92)),
        "on-dark-muted": minimal.get("on-dark-muted", _mix(bg, paper, 0.62)),
        "glow": minimal.get("glow", _shade(bg, 0.12)),
    }
    return full


# ---- 小工具：HEX 派生 ----------------------------------------------------
def _clamp(x): return max(0, min(255, int(round(x))))


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(r, g, b): return f"#{_clamp(r):02X}{_clamp(g):02X}{_clamp(b):02X}"


def _shade(h: str, f: float) -> str:
    """f>0 提亮，f<0 压暗。"""
    r, g, b = _rgb(h)
    if f >= 0:
        return _hex(r + (255 - r) * f, g + (255 - g) * f, b + (255 - b) * f)
    return _hex(r * (1 + f), g * (1 + f), b * (1 + f))


def _mix(a: str, b: str, t: float) -> str:
    """a→b 线性插值，t∈[0,1]。"""
    ra, ga, ba = _rgb(a)
    rb, gb, bb = _rgb(b)
    return _hex(ra + (rb - ra) * t, ga + (gb - ga) * t, ba + (bb - ba) * t)


# ---- WCAG 对比度：身份评论官 / 结构评论官共用 ----------------------------
def _lin(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(h: str) -> float:
    r, g, b = _rgb(h)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG 对比度 ∈ [1, 21]。入参可带或不带 '#'。"""
    l1, l2 = luminance(fg), luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _darken_until(hexv: str, bg: str, target: float = 3.2, steps: int = 14) -> str:
    """把颜色逐步压深直到对 bg 的对比 ≥ target（语义色必须当小字可读）。"""
    cur = hexv if hexv.startswith("#") else "#" + hexv
    for _ in range(steps):
        if contrast_ratio(cur, bg) >= target:
            return cur
        cur = _shade(cur, -0.12)
    return cur


def legibilize(colors: dict) -> dict:
    """归一：把 pos/neg 这类「会被当小字用」的语义色压深到对纸底 ≥3.2，保证可读。
    确定性保证，不依赖 LLM 自觉，也不破坏 seed 主题。"""
    bg = colors.get("bg-content", "#FFFFFF")
    for k in ("pos", "neg"):
        if colors.get(k):
            colors[k] = _darken_until(colors[k], bg, 3.2)
    return colors
