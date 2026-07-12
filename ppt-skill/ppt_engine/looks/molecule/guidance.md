本 look 的叙事与组织纪律 —— 分子气泡研报(molecule):

叙事声音(研究陈述):
- 内容页 title 写**研究发现/判断句**,不写栏目名(对:"投放体量仅为竞品 1/5";
  错:"投放分析")。封面/章节/目录才用栏目式命名。
- 结论先行:每章开局先给结论页(kpi/chart/hero),证据页(table/comparison/
  bullets)跟在后面;so_what 写"这意味着什么/该做什么"。
- 客观分寸:负面发现如实呈现(delta_dir:"down"),同页 so_what 给应对方向。

deck 弧线(研报骨架):
- cover → toc(章节即研究维度,4~6 项,每项必写 desc 一句话结论)→
  [section N → 本章结论页 → 本章证据页 ×1~2] 循环 → 综合研判(two_col/pillars)
  → 建议与节奏(process/timeline)→ quote(全篇核心判断,可选)→ closing。
- section 的 number 用两位数字("01");全篇 section 数与 toc 项一一对应。

版式路由:
- 规模/量效数字 → kpi;趋势与分布 → chart;结构明细对照 → table;
  竞品/方案对打 → comparison(右列是本品/焦点侧);维度盘点 → icon_grid;
  策略步骤 → process;节奏节点 → timeline;问题与对策 → two_col(左焦点);
  章核心意象+关键事实 → hero(每章至多一页)。

图像纪律(两条通道,互斥使用):
- **素材图通道(figure 版式)**:素材里已有编号配图(如 "![图3-1 …](URL)")时,
  **优先用 figure 版式呈现**——src 逐字抄素材里的图片 URL,caption 抄图注原文,
  title 写这张图支撑的发现;禁止用 prompt 重新生成素材已有的图。
  每章至多 1 页 figure,选最能支撑该章结论的那张。
- **生成图通道(prompt 字段——引擎统一风格,你只描述画面内容)**:
- **cover.prompt 必写**:一句英文描述报告主题的具象画面(如品类产品/场景意象),
  主体放画面右侧;引擎会把左半烤白雾给标题,不必自己留白。
- **hero.prompt 必写**:该章核心意象的**单主体特写**(英文),主体居中——
  引擎裁成圆形图窗,四角会被裁掉,不要写多主体全景。
- **bullets.prompt 可选**:仅当该页讲场景/人群/生活方式时写,纵向构图单场景;
  纯论点页不写(留空则版面自动放满全宽,不会空)。
- prompt 只写内容不写风格词(风格由 look 统一注入);禁止要求画面里出现文字。
- cover/hero/bullets 之外的 kind 一律不写 prompt(无图槽,写了浪费生成)。
- 全篇 hero ≤3 页;连续两页都带图会显重,图页之间隔至少一页纯排版页。

避免视觉空白(硬纪律,页面槽位没吃满就是排版事故):
- toc 每项必写 desc;hero 页 facts ≥2 条且 subtitle 必写;
- kpi stats ≥3;bullets ≥3 条(带插图时 3~4 条,不带时 4~6 条);
- icon_grid cards ≥4 且每卡至少 1 条 lines;table rows ≥3;
- kpi/bullets/table/icon_grid/two_col/comparison/process/timeline 的 so_what
  尽量写——它是页面底部收束条,留空则页面下缘发虚。
- 反向红线:单页 bullets >6 条、table >6 行 → 拆页;标题超一行 → 精简。

数据表现:
- 数字口径写进 label/subtitle(时间窗/平台/来源);同组数据同口径;
- delta 必带方向;chart 一页一图,takeaway 写"说明什么+意味着什么"。

强调标记:
- title/quote 里可用 **词** 标一处重点(渲染成 look 主紫色);
  每页至多一处;so_what/points/lines 不用 **。

结构约定:
- cover.subtitle 是渐变胶囊里的项目说明(如"XX 2026 策略研究"),≤30 字;
- closing.title 用致谢或行动号召("谢谢观看"/"下一步,现在开始"),
  subtitle 写一句收束陈述;素材没有联系方式则 contact 留空。
