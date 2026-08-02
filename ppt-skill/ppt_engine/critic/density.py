"""密度评论官 —— 页面信息量下限的机器把关(零模型,读 IR)。

背景:实测发现"丰富度"类 prompt 指令(icon_grid 填满/kpi 带 delta/别只剩
三行字)遵守度不稳定,单模块版式容易产出稀页。与 section≤3 同理,下沉为
机器规则回喂。档位是 look 知识,声明在各 look 包的 LOOK.density 里
(crimson 咨询高密度最严;swiss/riso 的哲学本就是稀疏克制,留空=不设下限),
本评论官只消费注册表,不特判任何 look。"""
from __future__ import annotations

from ..looks import LOOKS

_CONTENT_KINDS = {"kpi", "bullets", "two_col", "comparison", "process",
                  "icon_grid", "timeline", "table", "pillars"}


def density_profile(look_id: str) -> dict:
    """该 look 的密度档位(exhibit_min 同时被 stages.check_outline 用作大纲配额)。"""
    look = LOOKS.get(look_id)
    return look.density if look else {}


def check_density(deck: dict, look_id: str | None = None) -> list[dict]:
    """deck 为 Deck IR 的 dict 形态。返回 issues(空 = 达标)。"""
    prof = density_profile(look_id or deck.get("theme", ""))
    if not prof:
        return []
    issues = []
    slides = deck.get("slides", [])

    n_exhibit = sum(1 for s in slides if s.get("data", {}).get("kind") == "exhibit")
    if prof.get("exhibit_min") and n_exhibit < prof["exhibit_min"]:
        issues.append({"slide": 0, "type": "exhibit-quota",
                       "detail": f"exhibit 复合版面仅 {n_exhibit} 页,本风格要求 ≥{prof['exhibit_min']}"
                                 "——把有数字支撑的主论证升格为 exhibit"})

    # 图表类型多样性:量级/占比/结构/画像各有对应图型,整本只用一种 = 选型失职
    if (m := prof.get("chart_variety_min")):
        types = [s.get("data", {}).get("chart_type", "column") for s in slides
                 if s.get("data", {}).get("kind") in ("chart", "exhibit")
                 and s.get("data", {}).get("series")]
        need = min(m, len(types))
        if len(types) >= 3 and len(set(types)) < need:
            issues.append({"slide": 0, "type": "chart-monoculture",
                           "detail": f"全篇 {len(types)} 页图表只用了 {len(set(types))} 种类型"
                                     f"({'/'.join(sorted(set(types)))}),要求 ≥{need} 种——"
                                     "占比/份额用 donut 或 pie,层级/构成用 stacked_column 或 "
                                     "stacked_bar,多对象多维画像用 radar,趋势用 line,量级对比用 column/bar"})

    for idx, slide in enumerate(slides, 1):
        d = slide.get("data", {})
        kind = d.get("kind", "")

        def thin(msg: str):
            issues.append({"slide": idx, "type": "thin-page",
                           "detail": f"第 {idx} 页({kind}){msg}"})

        if kind == "kpi" and (m := prof.get("kpi_stats_min")):
            stats = d.get("stats", [])
            if len(stats) < m and not any(s.get("delta") for s in stats):
                thin(f"仅 {len(stats)} 个数字且无 delta——补到 ≥{m} 个或给出环比/同比")
        if kind == "bullets" and (m := prof.get("bullets_min")):
            if len(d.get("bullets", [])) < m:
                thin(f"要点仅 {len(d.get('bullets', []))} 条——补到 ≥{m} 条或并页")
        if kind == "icon_grid" and (m := prof.get("icon_grid_min")):
            if len(d.get("cards", [])) < m:
                thin(f"仅 {len(d.get('cards', []))} 格——补到 ≥{m} 格(2~3 格会显得页面空)")
        if kind == "table" and (m := prof.get("table_rows_min")):
            if len(d.get("rows", [])) < m:
                thin(f"仅 {len(d.get('rows', []))} 行——数据太薄,并入相邻页或补行")
        if kind == "exhibit":
            if not d.get("insights"):
                thin("缺 insights 解读框——补 1~2 个编号解读")
            if len(d.get("implications", [])) < 2:
                thin("implications 不足 2 条——补齐'对企业的意义'")
            if not d.get("series") and not d.get("side"):
                thin("主图表与侧栏条都为空——至少给一个数据模块")
        if prof.get("so_what_required"):
            if kind in _CONTENT_KINDS and not d.get("so_what"):
                thin("缺 so_what 结论条——给决策者一句含义")
            if kind == "chart" and not d.get("takeaway"):
                thin("缺 takeaway——图表必须直接标注要读者看什么")
        if prof.get("lead_required"):
            if kind in (_CONTENT_KINDS | {"chart"}) and not d.get("lead"):
                thin("缺 lead 叙事段——标题下给 1~2 句承接语境(本页讲什么、为何重要)")
    return issues
