"""Morandi look 包 —— 莫兰迪简约（源自用户提供的「莫兰迪简约工作汇报」模板）：
暖纸 #FBF8F1 + 灰蓝 #838995 标题 + 粉/驼/灰绿/金/蓝灰五色低饱和轮换 +
陶土橙 #DC8D59 唯一点睛；签名元素是对角交叉的干笔刷肌理
（封面/章节页满幅、内容页角部点缀），思源宋 Bold 标题 × 思源黑正文 ×
Inter 英文注记。设计规格：./spec.md。"""
from __future__ import annotations
from pathlib import Path

from ...spec import SpecLock, TypeScale, Grid, ImageTreatment
from ...icons import ICONS
from .. import Look
from .image import STYLE_SUFFIX, BRUSH_ASSETS, make_hero, morandi_ify

SPEC = SpecLock(
    id="morandi",
    name="Morandi",
    look="morandi",
    colors={
        "bg-content": "#FBF8F1",    # 暖纸（源模板母版底 #FDFBF7 的略暖版）
        "surface": "#F2EDE3",       # 浅暖卡底
        "bg": "#6A7180", "bg-2": "#5F6775",   # 深灰蓝（收尾/深色卡;on-dark 对比 ≥4.5）
        "ink": "#5B6170",           # 正文深灰蓝（标题灰蓝的可读加深档）
        "muted": "#9CA1AB",         # 辅助文字
        "hairline": "#E2DCD0",      # 暖发丝线
        "primary": "#838995",       # 标题灰蓝（源模板主文字色）
        "primary-2": "#DC8D59",     # 陶土橙 —— 唯一点睛色（源 accent2）
        "accent": "#DC8D59", "accent-on": "#FFFFFF",
        "slate": "#838995",
        # 莫兰迪五色轮换（图标底/序号/图表）
        "pink": "#DFABA1", "tan": "#B89F90", "sage": "#C0C8C6",
        "gold": "#C8A25C", "blue": "#99A3B2",
        "grey-1": "#F2EDE3", "grey-2": "#E2DCD0", "grey-3": "#9CA1AB",
        "pos": "#7C8A77", "neg": "#B96A4B",
        "on-dark": "#FBF8F1", "on-dark-muted": "#C9CDD6", "glow": "#6A7180",
    },
    # 角色字体 ≤2 族：宋 Bold 显示 × 黑 正文；Inter 是英文注记的附加字面。
    display_font="Noto Serif SC",
    body_font="Noto Sans SC",
    embed_families=["Noto Sans SC", "Noto Serif SC", "Inter"],
    font_vars={
        "font-display": '"Noto Serif SC", "Songti SC", "STSong", serif',
        "font-body": '"Noto Sans SC", "PingFang SC", sans-serif',
        # 英文眉标/角标/数据注记统一走 Inter（源模板的 Gill Sans 气质）
        "font-mono": '"Inter", "Noto Sans SC", sans-serif',
    },
    # 低饱和轮换：驼/灰绿/粉/蓝灰/金 + 陶土橙收尾（源图表就是驼×灰绿）
    chart_palette=["B89F90", "C0C8C6", "DFABA1", "99A3B2", "C8A25C", "DC8D59"],
    type_scale=TypeScale(ratio=1.333, display=76, h1=48, h2=32, body=18, caption=14, micro=11),
    grid=Grid(cols=12, margin=72, gutter=20, unit=8),
    image=ImageTreatment(style="none"),   # 统一处理在 morandi_ify 后处理里
    rules=[
        "低饱和纪律：大面积只用五色轮换 + 灰蓝，陶土橙只做点睛（chip/强调词/末位节点）",
        "标题居中 + 细线中断短划分隔；章节/封面文字右置，笔刷艺术区在左",
        "干笔刷是唯一肌理：满幅只出现在封面/章节/目录/金句/收尾，内容页限角部点缀",
        "序号用中文数字（壹贰叁肆），配色循环取轮换五色",
        "圆与圆角（8px）是形状语言；无投影、无渐变、无硬边直角大色块",
    ],
    rationale="莫兰迪低饱和灰调——暖纸底+灰蓝标题+五色轮换+陶土橙点睛，干笔刷肌理"
              "温柔文艺有质感，适合品牌/美妆/生活方式类汇报与提案",
)

LOOK = Look(
    spec=SPEC,
    template_dir=str(Path(__file__).parent / "templates"),
    icons={**ICONS, **BRUSH_ASSETS},  # 共享细描边集 + 笔刷 PNG 路径（模板 data-src 用）
    image_style_suffix=STYLE_SUFFIX,
    image_postprocess=morandi_ify,
    image_fallback=make_hero,
    pick_when="工作汇报/项目进展/对上沟通",
    density={                       # 汇报版:数字页与格状页不许太薄
        "kpi_stats_min": 3,
        "icon_grid_min": 4,
    },
)
