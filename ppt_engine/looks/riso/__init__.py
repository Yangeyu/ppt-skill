"""Riso look 包 —— Risograph zine：暖纸 + Federal Blue + Fluo Pink + Mustard，
巨号海报标题（Anton × 思源黑 Black 中西配对）+ mono 注解，硬边、套印错位。
设计规格：./spec.md（对标 ppt-master indie-bookstore zine 示例）。"""
from __future__ import annotations
from pathlib import Path

from ...spec import SpecLock, TypeScale, Grid, ImageTreatment
from ...icons import ICONS
from .. import Look
from .icons import RISO_ICONS
from .image import STYLE_SUFFIX, make_hero, riso_ify

SPEC = SpecLock(
    id="riso",
    name="Riso",
    look="riso",
    colors={
        "bg-content": "#F5EFE0",    # warm paper
        "paper-2": "#EAE2CC",       # secondary paper
        "surface": "#EAE2CC",
        "bg": "#161616", "bg-2": "#0F0F0F",
        "ink": "#1A1A1A",           # riso near-black ink
        "muted": "#5A5A5A",
        "hairline": "#1A1A1A",      # riso dividers are bold black
        "primary": "#1E4DBC",       # Riso Federal Blue
        "primary-2": "#FF5C8A",     # Riso Fluorescent Pink
        "blue": "#1E4DBC", "pink": "#FF5C8A", "mustard": "#E8A02E", "black": "#1A1A1A",
        "on-paper-muted": "#6B6256",
        "pos": "#1E4DBC", "neg": "#FF5C8A",
        "on-dark": "#F5EFE0", "on-dark-muted": "#BDB8A8", "glow": "#0F0F0F",
    },
    # 角色字体（majorFont/minorFont，≤2 族的评论官纪律管这里）；
    # Anton / Space Mono 是中西配对的附加字面，走 embed_families 一起嵌入。
    display_font="Noto Sans SC Black",
    body_font="Noto Sans SC",
    embed_families=["Noto Sans SC", "Noto Sans SC Black", "Anton", "Space Mono"],
    font_vars={
        "font-display": '"Anton", "Noto Sans SC Black", sans-serif',
        "font-mono": '"Space Mono", "Noto Sans SC", monospace',
        "font-body": '"Noto Sans SC", "PingFang SC", sans-serif',
    },
    chart_palette=["1E4DBC", "FF5C8A", "E8A02E", "1A1A1A", "5A5A5A", "EAE2CC"],
    type_scale=TypeScale(ratio=1.5, display=112, h1=54, h2=30, body=20, caption=15, micro=12),
    grid=Grid(cols=12, margin=60, gutter=24, unit=8),
    image=ImageTreatment(style="screen-print"),
    rules=["硬边无圆角", "巨号标题单行不折(nowrap)", "强调色只做强调,大面积留给纸色"],
    rationale="Risograph zine——纸感套色海报风,巨号标题/硬边色块/套印错位,适合潮流文化与叙事主题",
)

LOOK = Look(
    spec=SPEC,
    template_dir=str(Path(__file__).parent / "templates"),
    # riso 自带重字重图标,同时继承基础描边集,语义名(zap/target/…)不至于渲染成空
    icons={**ICONS, **RISO_ICONS},
    image_style_suffix=STYLE_SUFFIX,
    image_postprocess=riso_ify,
    image_fallback=make_hero,
)
