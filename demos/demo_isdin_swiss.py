"""怡思丁双抗防晒竞品分析 · swiss look —— 源自完整版报告(2026-07-03)。

数据口径:千瓜 2025.01-10 小红书商业投放;详见报告参考文献。
用法: python demo_isdin_swiss.py [out.pptx] [截图目录]
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
    HeroData, HeroFact, TocData, TocItem, SectionData, BulletsData, Bullet,
    TimelineData, Milestone, IconGridData, IconCard,
    CompareData, TwoColData, Column, KpiData, Stat,
    ChartData, Series, TableData, QuoteData, ClosingData,
)

DECK = Deck(
    meta=DeckMeta(title="怡思丁双抗防晒竞品分析"),
    theme="swiss",
    slides=[
        # 1 封面 hero —— 防晒主题 t2i(内容 prompt,风格由 look 强制)
        Slide(data=HeroData(
            eyebrow="ISDIN COMPETITIVE · 2026", title="双抗防晒**攻防战**",
            subtitle="怡思丁 × 蜜丝婷 × 安热沙 × 理肤泉 · 小红书五维竞品分析",
            footer="KIWOO INSIGHT · 2026-07-03 · 内部资料", art="sun",
            prompt="A tall sunscreen tube standing upright on a beach, a huge "
                   "blazing sun disc high in the sky with radiating rays, palm "
                   "leaf and beach umbrella silhouettes, calm sea horizon band "
                   "in the foreground",
            facts=[HeroFact(value="138篇", label="本品商业笔记"),
                   HeroFact(value="7.59万", label="本品互动总量"),
                   HeroFact(value="0", label="头部达人合作")])),
        # 2 目录
        Slide(data=TocData(
            eyebrow="CONTENTS", title="目录",
            items=[TocItem(title="竞品格局", desc="市场底色与五品牌对照", pages="P03–P06"),
                   TocItem(title="达人结构", desc="三种分工模式 vs 头部缺位", pages="P07–P08"),
                   TocItem(title="内容打法", desc="四条需求线与场景占位", pages="P09"),
                   TocItem(title="传播节奏", desc="双峰节奏与 Q3 失速", pages="P10"),
                   TocItem(title="卖点攻防", desc="双抗差异化 vs 竞品概念", pages="P11–P12"),
                   TocItem(title="攻防建议", desc="三主攻 · 四避让 · 证据缺口", pages="P13–P16")])),
        # 3 章节 01
        Slide(data=SectionData(number="01", title="竞品格局",
                               subtitle="LANDSCAPE · XHS 2025.01–10")),
        # 4 市场底色 KPI
        Slide(data=KpiData(
            eyebrow="CORE MARKET · 2025", title="市场底色**四个数**",
            stats=[
                Stat(value="244亿+", label="品类市场规模", delta="+10-15%", delta_dir="up"),
                Stat(value="78%", label="线上渠道占比", delta="电商主导", delta_dir="flat"),
                Stat(value="52.4%", label="抖音线上市占", delta="超越天猫", delta_dir="up"),
                Stat(value="68.6%", label="社媒信息获取", delta="KOL 56.6%", delta_dir="up"),
            ])),
        # 5 五品牌对照表
        Slide(data=TableData(
            eyebrow="HEAD TO HEAD", title="**五品牌**投放对照",
            subtitle="XHS COMMERCIAL NOTES · QIANGUA 2025.01–10",
            headers=["品牌", "笔记数", "投放金额", "互动总量", "爆文率"],
            rows=[
                ["理肤泉", "632篇", "553万", "105.7万", "52.06%"],
                ["蜜丝婷·摇摇乐", "997篇", "374万", "151.8万", "45.34%"],
                ["蜜丝婷·小黄帽", "581篇", "236万", "65.8万", "42.69%"],
                ["安热沙", "371篇", "449万", "32.4万", "34.23%"],
                ["怡思丁", "138篇", "67.6万", "7.6万", "32.61%"],
            ])),
        # 6 互动体量图表
        Slide(data=ChartData(
            eyebrow="ENGAGEMENT GAP", title="互动体量:**1/5 到 1/14**", chart_type="column",
            categories=["摇摇乐", "理肤泉", "小黄帽", "安热沙", "怡思丁"],
            series=[Series(name="互动总量(万)", values=[151.8, 105.7, 65.8, 32.4, 7.6])],
            takeaway="怡思丁体量仅为竞品 1/5–1/14,天花板锁在「头部达人零合作」")),
        # 7 章节 02
        Slide(data=SectionData(number="02", title="打法拆解",
                               subtitle="PLAYBOOK DECODED · 4 DIMENSIONS")),
        # 8 达人结构对比
        Slide(data=CompareData(
            eyebrow="KOL STRUCTURE", title="达人结构:**三种模式**",
            left=Column(heading="竞品三种分工", points=[
                "理肤泉:头部挑大梁,贡献 30% 互动,单篇爆文 8.77 万",
                "蜜丝婷:365 位初级达人铺量,贡献 53% 互动",
                "安热沙:172 位腰部主力,贡献 66% 互动",
                "三种模式各有分工,声量天花板都被拉开"]),
            right=Column(heading="怡思丁:头部缺位", points=[
                "头部达人合作数 = 0",
                "腰部 41 人贡献 51%,初级 86 人贡献 48%",
                "互动体量仅为理肤泉的 1/14",
                "爆文率 32.61% 垫底,单篇上限锁死"]))),
        # 9 内容四条需求线 + 两个杠杆
        Slide(data=IconGridData(
            eyebrow="P09 · CONTENT PLAYS", title="内容需求线与**杠杆**",
            subtitle="FOUR DEMAND LINES × TWO LEVERS · XHS 2025",
            cards=[
                IconCard(icon="zap", title="极端实测", subtitle="Extreme Proof",
                         lines=["40°C 暴晒实测互动 4689", "已验证高效但体量小"], punch="记忆点,深耕它"),
                IconCard(icon="target", title="旅游攻略", subtitle="Travel Scene",
                         lines=["安热沙深绑日本旅游", "猫猫岛攻略 2.46 万互动"], punch="场景要抢占"),
                IconCard(icon="lightbulb", title="泛生活破圈", subtitle="Lifestyle",
                         lines=["理肤泉人文内容 8.77 万", "调性靠头部才能拉起"], punch="破圈靠头部"),
                IconCard(icon="shield", title="护肤功效", subtitle="Skincare",
                         lines=["油皮 175 篇被蜜丝婷占", "同质化竞争激烈"], punch="避让此赛道"),
                IconCard(icon="trending-up", title="视频优先", subtitle="Video First",
                         lines=["视频 40% 数量贡 54% 互动", "爆款率有提升空间"], punch="效率杠杆"),
                IconCard(icon="users", title="军训增量", subtitle="Back To School",
                         lines=["军训好物单篇 4.8 万互动", "本品 Q3 声量 -69%"], punch="Q3 关键补位"),
            ])),
        # 10 传播节奏时间线
        Slide(data=TimelineData(
            eyebrow="RHYTHM", title="全年**声量节奏**", subtitle="DUAL PEAK + SUMMER PLATEAU",
            milestones=[
                Milestone(year="2-3月", title="春季开囤", desc="品类首峰,早春种草启动"),
                Milestone(year="5-6月", title="618+法网", desc="摇摇乐峰值 8 万,前置窗口被强占"),
                Milestone(year="7月", title="暑期放量", desc="玩水旅游高位,蜜丝婷双峰值集中"),
                Milestone(year="8-9月", title="军训开学", desc="军训好物 4.8 万互动,本品布局不足"),
                Milestone(year="Q3", title="本品失速", desc="话题互动 3.63万 → 1.12万,-69%"),
            ])),
        # 11 卖点 hero —— 抗热老差异化
        Slide(data=HeroData(
            eyebrow="SECTION 03 · USP", title="**双抗**,独一无二",
            subtitle="抗光老 + 抗热老:有事实差异化,缺传播力度",
            footer="ANTI PHOTOAGING × ANTI HEAT AGING", art="sun",
            prompt="Close-up still life of a sunscreen bottle beside a large "
                   "vintage thermometer showing extreme heat, bold sun rays and "
                   "rising heat waves behind them",
            facts=[HeroFact(value="52篇", label="本品「专研」声量"),
                   HeroFact(value="171篇", label="理肤泉麦色滤"),
                   HeroFact(value="175篇", label="蜜丝婷油皮词")])),
        # 12 概念占位表
        Slide(data=TableData(
            eyebrow="MINDSHARE MAP", title="科技概念**占位战**",
            subtitle="TECH CONCEPT × SCENE · XHS 2025.01–10",
            headers=["品牌", "科技概念", "笔记数", "核心场景"],
            rows=[
                ["理肤泉", "麦色滤 + 大哥大昵称", "171篇", "泛生活 · 军训"],
                ["蜜丝婷", "油皮 · 成膜", "175篇", "户外 253 篇"],
                ["安热沙", "#防晒大膜王", "话题绑定", "日本旅游"],
                ["怡思丁", "双抗 · 热保护科技", "专研仅52篇", "40°C 实测 · 海岛"],
            ])),
        # 13 攻防清单
        Slide(data=TwoColData(
            eyebrow="PLAYBOOK 2026", title="**攻防**清单",
            left=Column(heading="主攻 OFFENSE", points=[
                "引入 1-2 位头部达人,目标单篇破圈 5 万+",
                "深耕 40°C 暴晒实测,补军训/大促/泛生活场景",
                "主攻「抗热老」:科技概念从 52 篇冲 150+ 篇",
                "视频优先:不加投放量也能放大互动"]),
            right=Column(heading="避让 DEFENSE", points=[
                "通勤/油皮/养肤:被蜜丝婷强占,高同质化",
                "618 前置窗口:理肤泉/摇摇乐正面强压",
                "初级铺量模式:365 人体量,预算不支撑",
                "网球 IP 未确认授权,品牌资产线慎动"]))),
        # 14 局限与证据缺口
        Slide(data=BulletsData(
            eyebrow="CAVEATS", title="局限与证据缺口",
            bullets=[
                Bullet(text="搜索占位数据缺失:无法判断搜索入口的拦截关系", emphasis=True),
                Bullet(text="人群画像缺失:候选人群为内容样本反推,缺直接验证", emphasis=True),
                Bullet(text="时间窗止于 10 月:双 11 节点表现未纳入"),
                Bullet(text="理肤泉/安热沙达人层级与分形式互动数据不完整"),
                Bullet(text="仅覆盖小红书;抖音已成线上第一渠道,跨平台需另行分析"),
            ])),
        # 15 金句
        Slide(data=QuoteData(
            quote="双抗写在配方里,也要写进**心智**里。", attribution="—— 2026 攻防主线")),
        # 16 收尾
        Slide(data=ClosingData(
            title="把**差异化**讲出来。", subtitle="Own the anti-heat-aging story",
            contact="怡思丁 2026 小红书种草策略 · 内部资料")),
    ],
)


if __name__ == "__main__":
    dest = ROOT / "out" / "isdin_swiss"
    out = sys.argv[1] if len(sys.argv) > 1 else str(dest / "isdin_swiss.pptx")
    shots = sys.argv[2] if len(sys.argv) > 2 else str(dest / "preview")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(shots).mkdir(parents=True, exist_ok=True)
    prims = Engine().build(DECK, out, screenshot_dir=shots)
    print(f"已生成 {out} — {len(prims)} 页, {sum(len(p) for p in prims)} 原语")
    print("结构自检:", check_layout(prims) or "零问题 ✓")
