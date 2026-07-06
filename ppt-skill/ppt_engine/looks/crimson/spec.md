---
id: crimson
name: Crimson Consulting（经典深红咨询风）
source: crazyykhllc-bit/CyberPPT · 视觉风格 1
---

# Crimson Consulting 设计规格

## 身份

| 令牌 | 值 | 用途 |
|---|---|---|
| paper | `#F3F4EF` | 暖灰纸底（全局内容底，禁大面积纯白卡） |
| surface | `#EAEBE3` | 面板浅阶（SO WHAT 条 / 双栏面板 / 表格隔行） |
| ink | `#111111` | 标题/正文/表头带 |
| muted | `#555555` | 次级文字 |
| hairline | `#D6D6D2` | 发丝线 |
| crimson | `#8B1E1E` | 唯一强调色：结论/优先级/例外/徽章/章节幕 |
| crimson-2 | `#5E1414` | 深红暗阶（图表第二序列，不引入第二色相） |

字体：思源黑体 700（结论句标题 / 章节巨号 / KPI 大数字，对标 CyberPPT
参考版式的黑体加粗）× 思源黑（正文）× JetBrains Mono（页码徽章 /
证据标签 / 页脚角标）。

## 版式纪律（对标 CyberPPT）

- **SCR 叙事**：页面主标题 = 完整结论句（T2），不是名词短语。
- **页码徽章**（T1）：左上角 30px 深红方块反白页码。
- **双线规**：页首收口 2px 墨线 + 1px 发丝线（经典账簿）。
- **证据标签**（T5）：KPI / 证据格 / 对开列挂 `E01` 深红 mono 标签。
- **SO WHAT 结论条**（T9/T10）：内容页收底——深红标签块 + 浅阶面板正文；
  IR 侧走各 kind 的可选 `so_what` 字段（chart 复用 `takeaway`）。
- **页脚**（T14）：发丝线 + 左 deck 名 · 中 CONFIDENTIAL · 右深红方点+页码。
- **统一表面系统**：分区靠 surface 浅阶 / 栏头带 / 发丝线，无阴影无圆角无渐变。
- **图表**：直接标注，强调序列深红、其余灰阶退后（chart_palette 顺序即纪律）。
- 墨色表头带反白 + 隔行 surface 浅阶 = 证据表。

## exhibit 复合证据版面（本 look 的招牌）

对标参考页的「一页多模块」组织：完整结论句大标题（≤72 字，可两行 +
`**强调**`）→ 主图表模块（栏头 + 原生图表 + 虚线标注框）→ 侧栏结构条
模块（横条按组内最大值归一，`em` 条上深红）→ ①② 编号洞察框 → 底部
「对企业的意义」条（深红标签 + 图标四栏）→ 来源页脚。IR 侧是新增的
`exhibit` kind（SideModule/SideBar/InsightBox/Implication），字段见
`ir.py`。原 chart/comparison/timeline 三页的信息量可折叠进一页。

## 版式映射

cover=纸底+顶红细带+底红座 / section=深红满屏 C0 巨号 / hero=顶部 248px
酒红双色调图版+结论标题+事实条 / table=墨头带+隔行浅阶 / two_col=浅阶面板
+红/墨栏头带 / comparison=对开+E 标签 / icon_grid=证据格 3×2 / closing=墨色
满屏+红标点。图像：`crimson_ify` 酒红双色调（#26110E → #7C4038 → paper）；
无源图走 `make_hero` 直角几何兜底（红块面+墨条组+12 列发丝网格）。
