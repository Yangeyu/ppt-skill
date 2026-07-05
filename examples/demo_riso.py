"""Riso-look sample deck — exercises the full Risograph archetype set, all
rendered as native, editable pptx (paper + Federal Blue/Fluo Pink/Mustard,
Anton × 思源黑 Black display, mono captions, hard-edge color blocks, 套色错位)."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root, so examples run without install
from ppt_engine.build import Engine
from ppt_engine.selfcheck import check_layout
from ppt_engine.ir import (
    Deck, DeckMeta, Slide,
    CoverData, HeroData, TocData, TocItem, SectionData, BulletsData, Bullet,
    TimelineData, Milestone, ProcessData, Step, IconGridData, IconCard,
    PillarsData, Pillar, CompareData, TwoColData, Column, KpiData, Stat,
    ChartData, Series, TableData, QuoteData, ClosingData,
)

DECK = Deck(
    meta=DeckMeta(title="Zine 文化指南"),
    theme="riso",
    slides=[
        Slide(data=HeroData(
            eyebrow="ISSUE №01 · 2026", title="ZINE 文化指南",
            subtitle="一份从一张纸到一家书店的独立出版地图",
            footer="PPT ENGINE · RISO ZINE DEMO", art="sun")),
        Slide(data=TocData(
            eyebrow="CONTENTS", title="目录",
            items=[TocItem(title="zine 是什么"), TocItem(title="简史四浪潮"),
                   TocItem(title="Risograph 工艺"), TocItem(title="6 种内容"),
                   TocItem(title="全球独立书店"), TocItem(title="怎么逛与收藏")])),
        Slide(data=SectionData(number="01", title="zine 是什么", subtitle="MAGAZINE 减去商业逻辑")),
        Slide(data=BulletsData(
            eyebrow="WHAT IS ZINE", title="zine = magazine − 商业",
            bullets=[
                Bullet(text="自制、非商业、印量极小——多在 1000 份以内", emphasis=True),
                Bullet(text="装订简单、内容混合、完全作者主权"),
                Bullet(text="与杂志的边界:印量 + 商业意图 + 编辑流程"),
                Bullet(text="复印机就是它的印刷厂"),
            ])),
        Slide(data=TimelineData(
            eyebrow="HISTORY", title="zine 的四次浪潮", subtitle="ONE HUNDRED YEARS",
            milestones=[
                Milestone(year="1920s", title="业余出版", desc="哈莱姆文艺 Fire!! 创刊"),
                Milestone(year="1930s", title="科幻同人志", desc="“fanzine” 一词 1940 诞生"),
                Milestone(year="1976", title="朋克", desc="Sniffin' Glue + 复印机普及"),
                Milestone(year="1991", title="Riot Grrrl", desc="Bikini Kill + Riot Grrrl Press"),
                Milestone(year="2010s", title="当代复兴", desc="zine fair 全球爆发"),
            ])),
        Slide(data=ProcessData(
            eyebrow="METHOD", title="Risograph 工艺 5 步",
            steps=[
                Step(title="数字图像", desc="接收数字稿"),
                Step(title="烧蚀母版", desc="像素化制版"),
                Step(title="包裹墨筒", desc="母版裹上彩色墨筒"),
                Step(title="滚压油墨", desc="墨筒滚印到纸"),
                Step(title="多次过纸", desc="逐色叠印完成"),
            ])),
        Slide(data=IconGridData(
            eyebrow="P07 · CONTENT TYPES", title="你能填的东西 > 6种内容",
            subtitle="SIX CONTENT TYPES · THERE ARE NO MISTAKES · JUST WHIMS",
            cards=[
                IconCard(icon="pencil", title="草图 / 漫画", subtitle="Sketches & Mini-comics",
                         lines=["涂鸦、4 格漫画、手绘日记", "字丑也行，构图弱也行"], punch="画得不像 = 风格"),
                IconCard(icon="pen-nib", title="诗 / 宣言 / 短文", subtitle="Poetry & Manifestos",
                         lines=["100 字宣言、一句口号", "Riot Grrrl Manifesto 范本"], punch="短而准 > 长而虚"),
                IconCard(icon="note", title="食谱 + 插图", subtitle="Recipes & How-tos",
                         lines=["外婆的腌菜配方 + 工具", "“如何修自行车”教学"], punch="日常实用 = 最普及"),
                IconCard(icon="book", title="照片 + 私人写作", subtitle="Photos & Personal Writing",
                         lines=["老照片复印件 + 旁注", "家族故事 / 旅行札记"], punch="主权 > 隐私"),
                IconCard(icon="scissors", title="拼贴 + 混合媒材", subtitle="Collage & Mixed Media",
                         lines=["杂志撕页 + 胶带 + 印章", "字典页 + 票据 + 蕾丝"], punch="物质感 = 复印机救不了"),
                IconCard(icon="brush", title="实验性视觉", subtitle="Experimental Visuals",
                         lines=["纯色块、纯纹理、纯字", "空白页 = 阅读节奏"], punch="没有信息 = 一种信息"),
            ])),
        Slide(data=HeroData(
            eyebrow="PART 05", title="全球独立书店",
            subtitle="从神保町到布鲁克林,纸的栖息地",
            footer="GLOBAL BOOKSTORES", art="city")),
        Slide(data=PillarsData(
            eyebrow="GLOBAL", title="三座城市三家店", subtitle="PARIS · LONDON · NEW YORK",
            columns=[
                Pillar(heading="巴黎", tag="Shakespeare & Co.",
                       points=["1951 现址 George Whitman", "接纳数千写作者过夜", "塞纳河左岸地标"]),
                Pillar(heading="伦敦", tag="Word on the Water",
                       points=["1920s 荷兰运河驳船", "漂在水上的书店", "Daunt 按国家分类"]),
                Pillar(heading="纽约", tag="Strand",
                       points=["1927 创立至今", "18 英里书架", "二手书天堂"]),
            ])),
        Slide(data=CompareData(
            eyebrow="ART BOOK FAIR", title="中国书展双子星",
            left=Column(heading="abC", points=["2015 创办,京沪双城", "上海展 145 家中国展商", "10000+ 参观人次"]),
            right=Column(heading="UNFOLD", points=["abC 后一周举办", "更高的摊位费", "更大的客流量"]))),
        Slide(data=TwoColData(
            eyebrow="HOW-TO", title="怎么逛 / 怎么收藏",
            left=Column(heading="逛店", points=["看选品 = 看店主", "留至少 1 小时", "带现金、拍照先问"]),
            right=Column(heading="收藏", points=["从一本起步", "用塑封保护", "跟踪作者 Instagram"]))),
        Slide(data=KpiData(
            eyebrow="JIMBOCHO", title="神保町数字",
            stats=[
                Stat(value="130+", label="书店数量", delta="全球最大", delta_dir="up"),
                Stat(value="1875", label="最早开业", delta="高山本店", delta_dir="flat"),
                Stat(value="1本", label="森冈书店", delta="每周一本", delta_dir="flat"),
                Stat(value="#1", label="全球最酷", delta="Time Out", delta_dir="up"),
            ])),
        Slide(data=ChartData(
            eyebrow="TREND", title="zine fair 增长", chart_type="column",
            categories=["2016", "2018", "2020", "2022", "2024", "2026"],
            series=[Series(name="书展数", values=[12, 20, 28, 41, 63, 88])],
            takeaway="十年里中国艺术书展数量翻了约 7 倍")),
        Slide(data=TableData(
            eyebrow="CHINA MAP", title="独立书店地图", subtitle="BOOKSTORE / CITY / FOCUS / ZINE",
            headers=["书店", "城市", "特色", "zine"],
            rows=[
                ["单向空间", "北京", "文化沙龙", "★★"],
                ["码字人", "北京", "诗歌 + zine", "★★★"],
                ["香蕉鱼", "上海", "艺术书 + 自出版", "★★★"],
                ["假杂志", "宁波", "摄影书", "★★★"],
                ["方所", "广州", "设计选品", "★★"],
            ])),
        Slide(data=QuoteData(
            quote="一本 zine,是世界上最小的出版社。", attribution="—— 它也可以是你的")),
        Slide(data=ClosingData(
            title="印一份。送一份。", subtitle="A zine can also be yours",
            contact="growth@company.com · 2026")),
    ],
)


if __name__ == "__main__":
    run_dir = Path(__file__).resolve().parents[1] / "out" / "riso_demo"
    out = sys.argv[1] if len(sys.argv) > 1 else str(run_dir / "deck.pptx")
    shots = sys.argv[2] if len(sys.argv) > 2 else str(run_dir / "shots")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(shots).mkdir(parents=True, exist_ok=True)
    prims = Engine().build(DECK, out, screenshot_dir=shots)
    print(f"已生成 {out} — {len(prims)} 页, {sum(len(p) for p in prims)} 原语")
    print("结构自检:", check_layout(prims) or "零问题 ✓")
