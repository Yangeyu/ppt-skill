# swiss 主题的气质
瑞士国际主义（International Typographic Style）：纸白底 + 近黑正文 + **唯一强调色克莱因蓝 IKB**。
1px 发丝线、直角、16 列网格纪律、大字用**细字重**、大量有秩序的留白、严格左对齐。
克制、理性、数据说话——像一份精密的年报，不是海报集市。
中文为主；eyebrow / tag 用「英文大写」mono kicker（如 "ISDIN COMPETITOR REPORT"）。
文案要冷静精准：标题宜短（8-14 字最佳），别用感叹号，让数字与结构制造张力。

# 版式清单（每页选一个 kind，字段与预算严格遵守；括号内是最大字符数）
- hero      图文页(上 60% 全幅图 + 下方三列大数字)：eyebrow(24) title(28,建议≤14字) subtitle(48) footer(48)
            + prompt(300,英文,**只写画面内容母题**如器物/场景,风格由引擎强制成极简摄影;强烈建议填,不填才退化到几何图形)
            + art(16,无网络时的几何兜底:dots|rings|bars|grid) + facts[≤3]{value(10),label(16)}(下方三列大数字,建议给满 3 个)
- cover     纯文字封面(满屏 IKB 蓝 + 反白细体大字)：eyebrow(24) title(28,建议≤12字) subtitle(48) footer(48)
- toc       目录(发丝线索引行)：items[2-6]{title(24), desc(32,一句概括), pages(10,如"P03–P05")}（最多 6 条，desc/pages 建议填满，别把 closing 列进去）
- section   章节陈述页(大幽灵数字)：number(4,如"01") title(20,建议≤12字) subtitle(40)
- kpi       数据账单(逐行大数字+发丝线)：stats[2-4].value(8) label(16) delta(12) delta_dir(up|down|flat)
- timeline  横向时间轴 2-5 里程碑：milestones[].year(10) title(16) desc(44)
- icon_grid 2-6 张网格卡(仅最后一张 IKB 蓝底突出)：title(12) subtitle(32,拉丁) lines[≤3 每条≤14字] punch(20) icon(见图标表)
- comparison 左右对照(IKB 蓝板 vs 灰板,左强右弱)：left/right = { heading(24), points[1-5](60) }
- two_col   两栏并列(中缝发丝线)：结构同 comparison
- pillars   2-4 支柱列(顶部粗线+底部大编号,末列 IKB)：columns[].heading(16) tag(22,拉丁) points[1-5](60)
- process   2-5 步流程(发丝线横轴+方点)：steps[].title(16) desc(48) icon
- chart     原生图表(IKB 主色)+takeaway 蓝块：chart_type(column|bar|line) categories[2-8] series[1-4].{name(20),values[数字]} takeaway(60)
- table     表格(仅横向发丝线,无边框底色)：headers[2-5] rows[1-8]
- bullets   编号索引行 1-6：bullets[].text(80) emphasis(bool)
- quote     金句(细体大字+IKB 引号)：quote(80) attribution(40)
- closing   收尾(左半 IKB 宣言+右半白底行动项)：title(20,建议≤6字) subtitle(48) contact(48)

# 图标表（icon 字段只能从这里选）
target / trending-up / users / zap / shield / layers / bar-chart / check-circle / lightbulb / rocket

# 组稿节奏（一份好 deck）
- 10-16 页；theme 固定 "swiss"；meta.lang "zh"；meta.title 精炼。
- 开场 hero(带图) 或 cover(IKB 大字) → toc → 用 2-3 张章节页切分 → 章节内用**多样**版式(kpi/timeline/icon_grid/comparison/chart/pillars/two_col/table)承载 → quote → closing。
- **图像化章节页**：最重要的 1-2 个章节，用 hero 代替 section 做章节页——eyebrow 写 "SECTION 0X"，prompt 换一个贴合本章的静物/场景母题（别和封面重复），facts 放本章 3 个关键数字；其余章节仍用 section 大数字页。全 deck hero 总数 2-3 张为宜。
- 避免连续两页同一个 kind；让数字页、对照页、图表页、卡片页交错出现，节奏起伏。
- **内容密度**：稀疏页面会被引擎自检拒绝——pillars / comparison / two_col 每栏给 **4-5 条** points（别只给下限），bullets 给 4-6 条，icon_grid 每张卡 lines 给满 3 条 + punch。素材不够撑一页就把它并进相邻页，宁可少一页。
- 每页都要"有信息增量"，不堆废话；swiss 的美来自秩序与准确，不是装饰。
