# morandi 主题的气质
小清新莫兰迪：鼠尾草灰绿满版底 + 暖米白卡片 + 深墨绿点题 + 一抹陶土色。
手绘单线花卉做装饰、有机鹅卵石色块、错位叠放的白框相纸、发丝线分隔。
低饱和、温柔、有呼吸感——像一本生活方式杂志的专题页，不是行政汇报。
中文为主；eyebrow / tag 用「英文大写」宽字距 kicker（如 "ISDIN COMPETITOR REPORT"）。
文案要轻盈准确：标题宜短（8-14 字），少用副词，让色彩与留白说话；语气可以比 swiss 温和，但数字必须硬。

# 版式清单（每页选一个 kind，字段与预算严格遵守；括号内是最大字符数）
- hero      图文页(左侧白框相纸大图 + 右侧标题与竖排大数字)：eyebrow(24) title(28,建议≤14字) subtitle(48) footer(48)
            + prompt(300,英文,**只写画面内容母题**如器物/植物/场景,风格由引擎强制成莫兰迪静物摄影;强烈建议填,不填才退化到手绘植物画)
            + art(16,无网络时的手绘兜底:flora|leaves|blobs|waves) + facts[≤3]{value(10),label(16)}(右侧叠行大数字,建议给满 3 个)
- cover     封面(灰绿花卉底 + 居中米白大卡 + 鹅卵石色块三件套)：eyebrow(24) title(28,建议≤12字) subtitle(48) footer(48)
- toc       目录(色块编号 + 发丝线索引行)：items[2-6]{title(24), desc(32,一句概括), pages(10,如"P03–P05")}（最多 6 条，desc/pages 建议填满，别把 closing 列进去）
- section   章节页(左米白标本卡+手绘花 / 右侧灰绿底大标题)：number(4,如"01") title(20,建议≤12字) subtitle(40)
- kpi       数据账单(逐行大数字+发丝线+涨跌色块)：stats[2-4].value(8) label(16) delta(12) delta_dir(up|down|flat)
- timeline  横向时间轴 2-5 里程碑(圆环节点,末站陶土色)：milestones[].year(10) title(16) desc(44)
- icon_grid 2-6 张白卡(顶部灰绿色带,仅最后一张深绿突出)：title(12) subtitle(32,拉丁) lines[≤3 每条≤14字] punch(20) icon(见图标表)
- comparison 左右对照(深绿卡为主 vs 白卡为次,左强右弱)：left/right = { heading(24), points[1-5](60) }
- two_col   两栏并列(中缝发丝线,绿/陶土双色小标)：结构同 comparison
- pillars   2-4 支柱列(价目卡式:色块头+白卡身+编号脚,末列深绿)：columns[].heading(16) tag(22,拉丁) points[1-5](60)
- process   2-5 步流程(发丝线横轴+圆环节点)：steps[].title(16) desc(48) icon
- chart     原生图表(墨绿/灰绿/陶土配色)+深绿 takeaway 卡：chart_type(column|bar|line) categories[2-8] series[1-4].{name(20),values[数字]} takeaway(60)
- table     表格(深绿表头带+斑马纹+发丝线)：headers[2-5] rows[1-8]
- bullets   叶形符号索引行 1-6：bullets[].text(80) emphasis(bool)
- quote     金句(衬线大字反白+手绘花)：quote(80) attribution(40)
- closing   收尾(米白大卡+鹅卵石色块,右侧致谢)：title(20,建议≤6字) subtitle(48) contact(48)

# 图标表（icon 字段只能从这里选）
target / trending-up / users / zap / shield / layers / bar-chart / check-circle / lightbulb / rocket

# 组稿节奏（一份好 deck）
- 10-16 页；theme 固定 "morandi"；meta.lang "zh"；meta.title 精炼。
- 开场 cover(米白大卡) → toc → 用 2-3 张章节页切分 → 章节内用**多样**版式(kpi/timeline/icon_grid/comparison/chart/pillars/two_col/table)承载 → quote → closing。
- **图像化章节页**：最重要的 1-2 个章节，用 hero 代替 section 做章节页——eyebrow 写 "SECTION 0X"，prompt 换一个贴合本章的静物/植物母题（别和封面重复），facts 放本章 3 个关键数字；其余章节仍用 section 标本卡页。全 deck hero 总数 2-3 张为宜。
- 避免连续两页同一个 kind；让数字页、对照页、图表页、卡片页交错出现，节奏起伏。
- **内容密度**：稀疏页面会被引擎自检拒绝——pillars / comparison / two_col 每栏给 **4-5 条** points（别只给下限），bullets 给 4-6 条，icon_grid 每张卡 lines 给满 3 条 + punch。素材不够撑一页就把它并进相邻页，宁可少一页。
- 每页都要"有信息增量"，不堆废话；morandi 的美来自温柔的秩序，装饰交给主题自带的花卉与色块，文案不要再堆比喻。
