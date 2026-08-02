"""Crimson look 包 —— 经典深红咨询风（Classic Crimson Consulting）：
暖灰纸底 + 唯一深红锚点（#8B1E1E），思源宋体结论标题 × 思源黑正文的
"经典报告"配对，SCR 叙事纪律（页面标题=完整结论句）、页码徽章、
证据标签、底部 SO WHAT 结论条、墨色表头与来源页脚——MBB 高密度证据版式。
对标 crazyykhllc-bit/CyberPPT 的视觉风格 1（经典深红咨询风）与其
Typography Scale（C0 + T1-T14）/ 统一页面表面系统 / 可读性护栏。
设计规格：./spec.md。"""
from __future__ import annotations
from pathlib import Path

from ...spec import SpecLock, TypeScale, Grid, ImageTreatment
from ...icons import ICONS
from .. import Look
from .image import STYLE_SUFFIX, crimson_ify, make_hero

SPEC = SpecLock(
    id="crimson",
    name="Crimson Consulting",
    look="crimson",
    colors={
        "bg-content": "#F3F4EF",    # 暖灰纸底（CyberPPT 风格 1 原色）
        "surface": "#EAEBE3",       # 面板浅阶 —— 统一表面系统，禁大面积纯白卡
        "bg": "#161412", "bg-2": "#221E1B",
        "ink": "#111111",           # 标题/正文
        "muted": "#555555",         # 次级文字
        "hairline": "#D6D6D2",      # 发丝线
        "primary": "#8B1E1E",       # 深红 —— 唯一强调色，只用于结论/优先级/例外
        "primary-2": "#5E1414",     # 深红暗阶（图表第二序列，不引入第二色相）
        "accent": "#8B1E1E", "accent-on": "#FFFFFF",
        "grey-1": "#EAEBE3", "grey-2": "#D6D6D2", "grey-3": "#555555",
        "pos": "#8B1E1E", "neg": "#555555",
        "on-dark": "#F3F4EF", "on-dark-muted": "#A39A90", "glow": "#221E1B",
    },
    # 对标 CyberPPT 参考版式：黑体加粗（700）担纲结论句标题与大数字，
    # JetBrains Mono 走徽章/证据标签/页脚角标——全 sans 现代咨询配对。
    display_font="Noto Sans SC",
    body_font="Noto Sans SC",
    embed_families=["Noto Sans SC", "JetBrains Mono"],
    font_vars={
        "font-display": '"Noto Sans SC", "PingFang SC", sans-serif',
        "font-mono": '"JetBrains Mono", "Noto Sans SC", monospace',
        "font-body": '"Noto Sans SC", "PingFang SC", sans-serif',
    },
    # 深红 + 墨 + 灰阶：强调序列唯一上红，其余灰阶退后
    chart_palette=["8B1E1E", "111111", "555555", "B9B7B0", "5E1414", "D6D6D2"],
    type_scale=TypeScale(ratio=1.25, display=64, h1=40, h2=30, body=15, caption=12, micro=10),
    grid=Grid(cols=12, margin=56, gutter=20, unit=8),
    image=ImageTreatment(style="duotone"),
    rules=[
        "SCR 纪律：页面主标题必须是完整结论句，不写名词短语标题",
        "唯一强调色深红，只用于结论/优先级/例外，禁第二高亮色相",
        "统一纸面系统：分区靠面板浅阶/发丝线/栏头，禁大面积纯白卡片",
        "内容页收底 SO WHAT 结论条，证据模块挂 E01 证据标签",
        "图表直接标注数值，强调序列上深红，其余序列灰阶退后",
    ],
    rationale="经典深红咨询风——暖灰纸底+唯一深红锚点，宋体结论句标题+高密度"
              "证据版式（SCR 叙事 / SO WHAT 结论条 / 证据标签 / 墨色表头），"
              "MBB 报告气质，适合战略、竞品分析、行业研究与商业计划",
)

LOOK = Look(
    spec=SPEC,
    template_dir=str(Path(__file__).parent / "templates"),
    icons=ICONS,                      # 共享细描边集（1.5px 线性，克制中性）
    image_style_suffix=STYLE_SUFFIX,
    image_postprocess=crimson_ify,
    image_fallback=make_hero,
    pick_when="竞品分析/战略报告/证据密集的论证",
    density={                       # 咨询高密度:证据页信息量下限(critic/density 消费)
        "exhibit_min": 3,           # 全篇 exhibit 页数下限(每章主论证一页,含执行摘要)
        "kpi_stats_min": 3,         # 或任一 stat 带 delta
        "bullets_min": 4,
        "icon_grid_min": 4,
        "table_rows_min": 3,
        "so_what_required": True,   # 内容页必须给 so_what/takeaway
        "lead_required": True,      # 内容页必须给 lead 叙事段(标题下承接语境)
    },
    # 插图槽。aspect 必须与模板图元素盒子宽高比一致,否则原生嵌图变形。
    image_slots={
        # 顶部证据图版条(.ch-strip);超宽条取窗偏上(focus 0.3)保住人像面部
        # (t2i 人像的面部几乎总在画面上三分之一)
        "hero": {"size": "1664*928", "aspect": 1280 / 248, "focus": 0.3},
    },
)
