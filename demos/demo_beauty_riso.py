"""上海美妆市场 · riso look 样张 —— 2026 消费趋势洞察。

复用 riso(Risograph zine)全套版式:hero 海报封面、mono kicker、
硬边色块卡、套色错位、巨号数字、原生图表,全部原生可编辑。
用法: python demo_beauty_riso.py [out.pptx] [截图目录]
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # 仓库根:可导入 ppt_engine,产物统一进 out/
sys.path.insert(0, str(ROOT))
from ppt_engine.build import Engine
from ppt_engine.selfcheck import check_layout
from ppt_engine.ir import (
    Deck, DeckMeta, Slide,
    HeroData, HeroFact, TocData, TocItem, SectionData,
    TimelineData, Milestone, IconGridData, IconCard,
    PillarsData, Pillar, CompareData, TwoColData, Column, KpiData, Stat,
    ChartData, Series, TableData, QuoteData, ClosingData,
)

DECK = Deck(
    meta=DeckMeta(title="上海美妆 2026"),
    theme="riso",
    slides=[
        # 1 hero 封面 —— t2i 通用路径(prompt 只写内容,风格由 look 强制);art 为无 key 兜底
        Slide(data=HeroData(
            eyebrow="SHANGHAI BEAUTY · 2026", title="智美共生",
            subtitle="2026 上海美妆消费趋势的十个现场",
            footer="INSIGHT · SHANGHAI BEAUTY LAB", art="shanghai",
            prompt="Shanghai Bund skyline with the Oriental Pearl Tower as the main "
                   "silhouette motif, a large sun disc high behind the towers, "
                   "Huangpu river band in the foreground",
            facts=[HeroFact(value="42岁", label="常住中位年龄"),
                   HeroFact(value="130+", label="美妆首店 · 2025"),
                   HeroFact(value="1:4.7", label="体验店转化比")])),
        # 2 目录 —— 简述 + 页码区间芯片
        Slide(data=TocData(
            eyebrow="CONTENTS", title="目录",
            items=[TocItem(title="市场底色", desc="四个数读懂结构跃迁", pages="P03–P05"),
                   TocItem(title="人群重构", desc="年轻化 ≠ Z世代", pages="P06–P07"),
                   TocItem(title="决策动因", desc="从种草可信度到功效证据", pages="P08"),
                   TocItem(title="渠道触点", desc="权重与转化的错位", pages="P09–P11"),
                   TocItem(title="品类风向", desc="修护 · 防晒 · 中式香", pages="P12"),
                   TocItem(title="行动清单", desc="把趋势变成动作", pages="P13–P14")])),
        # 3 章节 01
        Slide(data=SectionData(number="01", title="市场底色", subtitle="BEAUTY × SHANGHAI 2026")),
        # 4 KPI
        Slide(data=KpiData(
            eyebrow="CORE METRICS · 2026 预判", title="结构性跃迁四个数",
            stats=[
                Stat(value="42%", label="Z世代贡献线上美妆GMV", delta="+7pp", delta_dir="up"),
                Stat(value="68%", label="愿为可验证功效溢价", delta="+12pp", delta_dir="up"),
                Stat(value="3.2", label="决策前人均品牌触点", delta="+0.9", delta_dir="up"),
                Stat(value="51%", label="ESG影响高端线购买", delta="+15pp", delta_dir="up"),
            ])),
        # 5 时间线
        Slide(data=TimelineData(
            eyebrow="EVOLUTION", title="从流量到信任的六年", subtitle="2020 → 2026",
            milestones=[
                Milestone(year="2020", title="直播爆发", desc="全域低价拉新"),
                Milestone(year="2022", title="成分党崛起", desc="早C晚A全民科普"),
                Milestone(year="2023", title="情绪护肤", desc="香氛疗愈快速出圈"),
                Milestone(year="2025", title="AI 测肤", desc="肤质适配进入门店"),
                Milestone(year="2026", title="智美共生", desc="算法与人文的信任契约"),
            ])),
        # 6 章节 02 —— 美妆静物 hero(t2i 通用路径,art 兜底)
        Slide(data=HeroData(
            eyebrow="SECTION 02", title="人群重构",
            subtitle="年轻化 ≠ Z世代:增量藏在 55+ 与男士护理",
            footer="WHO IS BUYING · 2026", art="vanity",
            prompt="Cosmetics still life on a dressing table: a tall faceted perfume "
                   "bottle, a lipstick with its cap off, a round compact mirror and a "
                   "mascara wand, a large sun disc behind them",
            facts=[HeroFact(value="35%", label="银发美妆渗透率"),
                   HeroFact(value="42%", label="Z世代线上GMV"),
                   HeroFact(value="+17%", label="男士护理增速")])),
        # 7 六股人群风向
        Slide(data=IconGridData(
            eyebrow="P07 · WHO IS BUYING", title="六股人群风向",
            subtitle="SIX FORCES · SHANGHAI CONSUMERS · 2026",
            cards=[
                IconCard(icon="zap", title="Z世代主力", subtitle="Gen-Z Core",
                         lines=["贡献 42% 线上 GMV", "为联名与限定买单"], punch="兴趣即渠道"),
                IconCard(icon="users", title="银发新客", subtitle="Silver Beauty",
                         lines=["渗透率升至 35%", "上海常住中位 42 岁"], punch="增量在 55+"),
                IconCard(icon="target", title="成分党", subtitle="Ingredient First",
                         lines=["看备案号再下单", "实验室数据披露成标配"], punch="证据 > 故事"),
                IconCard(icon="lightbulb", title="情绪美容", subtitle="Mood Beauty",
                         lines=["香氛与疗愈持续出圈", "「上班妆」到「下班妆」"], punch="悦己是刚需"),
                IconCard(icon="shield", title="敏感肌经济", subtitle="Sensitive Care",
                         lines=["修护类增速 26%", "皮肤学级国货上位"], punch="安全感溢价"),
                IconCard(icon="trending-up", title="男士进阶", subtitle="Men's Grooming",
                         lines=["防晒与底妆破圈", "礼赠场景占四成"], punch="蓝海仍在"),
            ])),
        # 8 对比
        Slide(data=CompareData(
            eyebrow="DECISION DRIVERS", title="2024 vs 2026 · 购买动因",
            left=Column(heading="2024", points=["KOL 推荐可信度", "包装设计吸引力", "促销力度", "品牌知名度"]),
            right=Column(heading="2026", points=["实验室级功效披露", "AI 肤质适配准确率", "门店即时检测反馈", "成分溯源可视化"]))),
        # 9 原生图表
        Slide(data=ChartData(
            eyebrow="TOUCHPOINTS", title="决策旅程触点权重", chart_type="column",
            categories=["小红书种草", "抖音测评", "品牌私域", "线下体验店", "跨境电商"],
            series=[Series(name="权重", values=[32, 28, 18, 15, 7])],
            takeaway="线下体验店权重第四,转化效率却是全渠道最高(1:4.7)")),
        # 10 三大商圈
        Slide(data=PillarsData(
            eyebrow="WHERE", title="三个美妆现场", subtitle="NANJING RD · HUAIHAI RD · QIANTAN",
            columns=[
                Pillar(heading="南京西路", tag="首店经济",
                       points=["全球旗舰首选地", "檐下快闪月月上新", "客单最高的体验层"]),
                Pillar(heading="淮海路", tag="策展式零售",
                       points=["买手制美妆集合店", "小众香与独立品牌", "年轻客群浓度最高"]),
                Pillar(heading="前滩", tag="家庭客群",
                       points=["亲子美护一站式", "会员复购率领先", "周末坪效冠军"]),
            ])),
        # 11 两栏打法
        Slide(data=TwoColData(
            eyebrow="PLAYBOOK", title="线上 / 线下怎么打",
            left=Column(heading="线上", points=["内容即货架:测评先行", "私域承接复购", "AI 试妆降低决策成本"]),
            right=Column(heading="线下", points=["门店 = 检测 + 体验场", "即时反馈驱动转化", "快闪制造稀缺感"]))),
        # 12 品类风向表
        Slide(data=TableData(
            eyebrow="CATEGORY MAP", title="品类风向标", subtitle="CATEGORY / GROWTH / KEYWORD / HEAT",
            headers=["品类", "增速", "关键词", "热度"],
            rows=[
                ["精华修护", "+26%", "屏障修护 · 早C晚A", "★★★"],
                ["防晒", "+21%", "养肤防晒 · 全年化", "★★★"],
                ["香氛", "+19%", "情绪疗愈 · 中式香", "★★★"],
                ["彩妆", "+12%", "伪素颜 · 持妆", "★★"],
                ["男士护理", "+17%", "防晒 · 礼赠", "★★"],
            ])),
        # 13 金句
        Slide(data=QuoteData(
            quote="美不再被定义,而是被验证。", attribution="—— 2026 上海美妆市场的信任契约")),
        # 14 收尾
        Slide(data=ClosingData(
            title="把趋势变成动作。", subtitle="Trends are countdowns for choices",
            contact="Shanghai Beauty Lab · 2026")),
    ],
)


if __name__ == "__main__":
    dest = ROOT / "out" / "beauty_riso"
    out = sys.argv[1] if len(sys.argv) > 1 else str(dest / "beauty_riso.pptx")
    shots = sys.argv[2] if len(sys.argv) > 2 else str(dest / "preview")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(shots).mkdir(parents=True, exist_ok=True)
    prims = Engine().build(DECK, out, screenshot_dir=shots)
    print(f"已生成 {out} — {len(prims)} 页, {sum(len(p) for p in prims)} 原语")
    print("结构自检:", check_layout(prims) or "零问题 ✓")
