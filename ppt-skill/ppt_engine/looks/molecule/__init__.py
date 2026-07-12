"""Molecule look 包 —— 分子气泡·行业研究报告（源自用户提供的 iSlide
「行业研究报告」模板）：极浅冷灰白底 + 紫蓝渐变分子气泡(景深虚化)唯一色彩
来源 + 思源黑 Black 重字重大标题 × Inter 英文注记；渐变只出现在小面积
徽章/圆点/胶囊,内容页素净留白,气泡装饰只在封面/目录/章节/收尾。
设计规格：./spec.md。"""
from __future__ import annotations
from pathlib import Path

from ...spec import SpecLock, TypeScale, Grid, ImageTreatment
from ...icons import ICONS
from .. import Look
from .image import STYLE_SUFFIX, BUBBLE_ASSETS, make_hero, molecule_ify

SPEC = SpecLock(
    id="molecule",
    name="Molecule",
    look="molecule",
    colors={
        "bg-content": "#F7F7FB",    # 极浅冷灰白（源模板高级灰底,非纯白）
        "surface": "#EFEFF6",       # 浅灰卡底
        "tint": "#ECEBF8",          # 淡紫卡底（two_col 焦点卡）
        "bg": "#22223A", "bg-2": "#1A1A2E",   # 深靛（深色场景兜底）
        "ink": "#1E1E28",           # 近黑标题墨（源模板重黑体标题）
        "muted": "#787887",         # 辅助文字
        "hairline": "#E3E3ED",      # 冷发丝线
        "primary": "#6C5CE0",       # 分子紫（渐变起点）
        "primary-2": "#3D7EDB",     # 分子蓝（渐变终点/大数字）
        "accent": "#6C5CE0", "accent-on": "#FFFFFF",
        "pos": "#2E6FD0", "neg": "#B8437E",
        "on-dark": "#F7F7FB", "on-dark-muted": "#ABABC6", "glow": "#2B2B4A",
    },
    # 角色字体 ≤2 族：思源黑 Black 显示 × 思源黑正文；Inter 是英文注记附加字面。
    display_font="Noto Sans SC Black",
    body_font="Noto Sans SC",
    embed_families=["Noto Sans SC", "Noto Sans SC Black", "Inter"],
    font_vars={
        "font-display": '"Noto Sans SC Black", "PingFang SC", sans-serif',
        "font-body": '"Noto Sans SC", "PingFang SC", sans-serif',
        # 英文眉标/角标/数据注记统一走 Inter（源模板的 Helvetica 气质）
        "font-mono": '"Inter", "Noto Sans SC", sans-serif',
    },
    chart_palette=["6C5CE0", "3D7EDB", "9D8FE8", "23233A", "8A8A9E", "C9D4F0"],
    type_scale=TypeScale(ratio=1.333, display=96, h1=44, h2=30, body=18, caption=14, micro=11),
    grid=Grid(cols=12, margin=64, gutter=20, unit=8),
    image=ImageTreatment(style="none"),   # 统一处理在 molecule_ify 后处理里
    rules=[
        "渐变只用于小面积徽章/胶囊/圆点/图表强调,大面积底保持浅灰白纸,文字无渐变",
        "气泡装饰只出现在封面/目录/章节/金句/收尾,内容页素净留白",
        "标题思源黑 Black 左对齐;英文注记 Inter 小号大写宽字距",
        "圆是形状语言:圆形图窗/渐变圆徽/圆点节点,无投影无描边大色块",
        "配图统一紫蓝高调摄影棚质感,圆窗或圆角裁切,由后处理收敛",
    ],
    rationale="分子气泡研报风——极浅灰白底+紫蓝渐变气泡+重黑体大标题,轻盈的科技感与"
              "大量留白,适合行业研究/市场分析/竞品报告等数据叙事",
)

LOOK = Look(
    spec=SPEC,
    template_dir=str(Path(__file__).parent / "templates"),
    icons={**ICONS, **BUBBLE_ASSETS},  # 共享细描边集 + 气泡装饰 PNG（模板 data-src 用）
    image_style_suffix=STYLE_SUFFIX,
    image_postprocess=molecule_ify,
    image_fallback=make_hero,
    pick_when="行业研究/市场分析/竞品报告,数据叙事与科技感",
    density={                       # 研报的数字页与格状页不许太薄
        "kpi_stats_min": 3,
        "icon_grid_min": 4,
        "bullets_min": 3,
    },
    # 内容页插图槽。aspect 必须与模板图元素盒子宽高比一致,否则原生嵌图变形。
    image_slots={
        "cover":   {"size": "1664*928", "aspect": 16 / 9},     # 全出血封面主视觉(左半烤白雾)
        "hero":    {"size": "1328*1328", "aspect": 1},          # 圆形图窗(后处理烤圆形蒙版)
        "bullets": {"size": "1140*1472", "aspect": 380 / 500},  # 左侧纵向插图列(圆角蒙版)
        # 素材证据图(投放矩阵/榜单截图):不重上墨、不裁切,pad 纸色适配
        "figure":  {"aspect": 16 / 9, "fit": "pad", "pad_color": "#F7F7FB",
                    "postprocess": False, "fallback": False},
    },
)
