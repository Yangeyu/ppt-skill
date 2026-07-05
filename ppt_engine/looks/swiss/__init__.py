"""Swiss look 包 —— 瑞士国际主义（Swiss International Typographic Style）：
高级灰白纸 + 单一克莱因蓝锚点（IKB），"越大越细"的字重纪律
（Inter Light × 思源黑 Light 中西配对细大字 + JetBrains Mono 数字/角标），
16 列网格、发丝线分级、直角纯色、无渐变无阴影。
对标 op7418/guizang-ppt-skill 的 Swiss 主题（themes-swiss / layouts-swiss / layout-lock）。
设计规格：./spec.md。"""
from __future__ import annotations
from pathlib import Path

from ...spec import SpecLock, TypeScale, Grid, ImageTreatment
from ...icons import ICONS
from .. import Look
from .image import STYLE_SUFFIX, make_hero, swiss_ify

SPEC = SpecLock(
    id="swiss",
    name="Swiss",
    look="swiss",
    colors={
        "bg-content": "#FAFAF8",    # paper — 极浅暖白（不是纯白，克制感的来源）
        "surface": "#F0F0EE",       # grey-1 浅灰块底
        "bg": "#0A0A0A", "bg-2": "#111111",
        "ink": "#0A0A0A",           # 近黑（不是纯黑）
        "muted": "#737373",         # grey-3 辅助文字
        "hairline": "#D4D4D2",      # grey-2 1px 发丝线
        "primary": "#002FA7",       # IKB · International Klein Blue（唯一锚点色）
        "primary-2": "#00227A",     # IKB 深阶（图表第二序列，不引入第二色相）
        "accent": "#002FA7", "accent-on": "#FFFFFF",
        "grey-1": "#F0F0EE", "grey-2": "#D4D4D2", "grey-3": "#737373",
        "pos": "#002FA7", "neg": "#737373",
        "on-dark": "#FAFAF8", "on-dark-muted": "#8C8C8C", "glow": "#111111",
    },
    # 角色字体（≤2 族纪律管这里）；Inter/Inter Light/JetBrains Mono 是
    # 中西配对的附加字面，走 embed_families 一起嵌入。
    display_font="Noto Sans SC Light",
    body_font="Noto Sans SC",
    embed_families=["Noto Sans SC", "Noto Sans SC Light",
                    "Inter", "Inter Light", "JetBrains Mono"],
    font_vars={
        "font-display": '"Inter Light", "Noto Sans SC Light", sans-serif',
        "font-mono": '"JetBrains Mono", "Noto Sans SC", monospace',
        "font-body": '"Inter", "Noto Sans SC", "PingFang SC", sans-serif',
    },
    # 单色相纪律：IKB + 灰阶，禁止第二高亮色
    chart_palette=["002FA7", "0A0A0A", "737373", "D4D4D2", "00227A", "F0F0EE"],
    type_scale=TypeScale(ratio=1.333, display=120, h1=64, h2=40, body=18, caption=14, micro=11),
    grid=Grid(cols=16, margin=64, gutter=16, unit=8),
    image=ImageTreatment(style="grayscale"),
    rules=[
        "单一高饱和锚点色（IKB），禁止出现第二高亮色相",
        "越大越细：巨字 Light，正文 Regular，小字加重（角标/label 600）",
        "直角、纯色、不透明：无渐变、无阴影、无圆角",
        "标题左对齐贴左上内容轴，不做水平居中大标题",
        "1px 发丝线只用于建立层级，不做装饰性堆线",
    ],
    rationale="瑞士国际主义——高级灰白底+克莱因蓝单锚点，Helvetica 气质细字重大字与网格纪律，"
              "冷静理性有学术感，适合商业分析、科技发布与设计分享",
)

LOOK = Look(
    spec=SPEC,
    template_dir=str(Path(__file__).parent / "templates"),
    icons=ICONS,                      # 共享细描边集（Swiss 要的就是 1.5px 线性图标）
    image_style_suffix=STYLE_SUFFIX,
    image_postprocess=swiss_ify,
    image_fallback=make_hero,
)
