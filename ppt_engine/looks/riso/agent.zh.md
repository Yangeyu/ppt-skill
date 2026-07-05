# riso 主题的气质
硬边色块、套色错位、巨号数字、拉丁文 mono 副标题压中文黑体大标题。锐利、克制、数据前置。
中文为主；eyebrow / subtitle / tag 多用「英文大写」做 mono kicker（如 "SHANGHAI BEAUTY · 2026"）。

# 版式清单（每页选一个 kind，字段与预算严格遵守；括号内是最大字符数）
- hero      海报封面(全出血 riso 图)：eyebrow(24) title(28) subtitle(48) footer(48) art(母题种子:city|sun|wave…)
- cover     纯文字封面：eyebrow(24) title(28) subtitle(48) footer(48)
- toc       目录：items[2-6].title(24)（目录是概览，最多 6 条，不要逐页罗列，更别把 closing 列进去）
- section   章节分隔大数字：number(4,如"01") title(20) subtitle(40)
- kpi       2-4 个核心数字：stats[].value(8) label(16) delta(12) delta_dir(up|down|flat)
- timeline  演进时间线 2-5 里程碑：milestones[].year(10) title(16) desc(44)
- icon_grid 2-6 张硬边色块卡(人群/要点)：title(12) subtitle(32,拉丁) lines[≤3 每条≤14字] punch(20,彩色收束) icon(见图标表)
- comparison 左右对照：left/right = { heading(24), points[1-5](60) }
- two_col   两栏并列(如线上/线下)：结构同 comparison
- pillars   2-4 支柱(如商圈/战略)：columns[].heading(16) tag(22,拉丁) points[1-5](60)
- process   2-5 步流程：steps[].title(16) desc(48) icon
- chart     原生图表：chart_type(column|bar|line) categories[2-8] series[1-4].{name(20),values[数字]} takeaway(60)
- table     表格：headers[2-5] rows[1-8]
- bullets   要点 1-6：bullets[].text(80) emphasis(bool)
- quote     金句：quote(80) attribution(40)
- closing   收尾/行动号召：title(20) subtitle(48) contact(48)

# 组稿节奏（一份好 deck）
- 10-15 页；theme 固定 "riso"；meta.lang "zh"；meta.title 精炼。
- 开场 hero 封面 → toc 目录 → 用 2-3 张 section 切分章节 → 章节内用**多样**版式(kpi/timeline/icon_grid/comparison/chart/pillars/two_col/table)承载 → quote 金句 → closing 行动号召。
- 避免连续两页同一个 kind；让数字页、对照页、图表页、卡片页交错出现，节奏起伏。
- 每页都要"有信息增量"，不堆废话。
