---
id: morandi
name: Morandi · 莫兰迪简约
source: 用户提供的「莫兰迪简约工作汇报」模板（1ppt 模板，2026-07-05 逆向提取）
status: seed
---

# Morandi Look 设计规格

## 身份（Identity）

| 令牌 | 值 | 来源 |
|---|---|---|
| 暖纸 bg-content | `#FBF8F1` | 母版底 `#FDFBF7` 的略暖版 |
| 标题灰蓝 slate/primary | `#838995` | 源模板主文字色（106 处） |
| 正文 ink | `#5B6170` | 灰蓝的可读加深档 |
| 点睛 accent | `#DC8D59` 陶土橙 | 源 accent2（chip/圆点） |
| 轮换五色 | 粉 `#DFABA1` 驼 `#B89F90` 灰绿 `#C0C8C6` 金 `#C8A25C` 蓝灰 `#99A3B2` | 源笔刷贴图取样 + slide 色值 |
| 卡底 surface | `#F2EDE3` / 发丝线 `#E2DCD0` | 派生 |
| 深灰蓝 bg | `#767D8B` | 源图文页面板色 |

**字体**：思源宋 Bold（display，对应源模板「思源宋体 CN Heavy」意图）×
思源黑（body，对应微软雅黑）× Inter（英文眉标/角标，对应 Gill Sans 气质）。
角色字体 2 族纪律；Inter 走 embed_families。

**图表**：驼×灰绿打头的低饱和序列（源图表就是驼×灰绿双色柱），陶土橙收尾。

## 签名元素（Signature）

1. **干笔刷交叉肌理**——唯一肌理。满幅（brush-cross）只出现在封面/章节/目录/
   金句/收尾；内容页限角部点缀（brush-tl 驼金 / brush-br 粉）。SVG 版
   （feTurbulence 置换毛边 + 随机枯笔条痕，`image.py BRUSH_ICONS`）经
   `data-ppt="icon"` 栅格化；hero 兜底用 PIL 同款算法。
2. **居中标题头**——EN 眉标（Inter 大字距）+ 宋体重标题 + 细线中断短划分隔。
3. **中文数字序号**——壹贰叁肆（宋体重），配色循环轮换五色。
4. **圆形色底 chip**——图标/序号载体（源模板圆角菱形的圆形化转译）；圆角 10px 卡。
5. **章节/封面构图**——笔刷艺术区在左，文字右置右对齐 + 陶土橙单元 chip。

## 纪律（Rules）

- 低饱和纪律：大面积只用轮换五色 + 灰蓝；陶土橙只做点睛（chip/强调词/末位节点/首位 KPI）。
- 无投影、无渐变、无硬边直角大色块；圆与 8-10px 圆角是形状语言。
- 内容页角部笔刷不与正文区重叠（角部出血 -34px 定位）。
- hero 图（t2i / 源图）经 `morandi_ify` 统一：降饱和 0.42 + 暖纸雾罩 0.14 + matte 曲线。
- t2i 构图纪律：主体置左半，右半留纸白（右侧叠 .80 纸色纱罩承载原生文字）。

## 版式映射（对照源模板页）

cover/hero=P1 封面（笔刷+右置标题）/ toc=P2（左笔刷+圆chip列表）/
section=P3、P8（右置章节题+单元chip）/ icon_grid=P5（色chip卡阵）/
process=P7（序号步骤）/ chart=P9（驼×灰绿柱图）/ kpi=P10（四卡）/
bullets=P12（壹贰叁肆清单）/ closing=P17 感谢页。
