---
id: swiss
name: Swiss（瑞士国际主义）
kind: brand+layout
source: op7418/guizang-ppt-skill（themes-swiss / layouts-swiss / swiss-layout-lock）
palette: paper #FAFAF8 · ink #0A0A0A · grey #F0F0EE/#D4D4D2/#737373 · accent IKB #002FA7
type: Inter Light × Noto Sans SC Light（细大字） / Inter × Noto Sans SC（正文） / JetBrains Mono（数字角标）
image: 黑白双色调纪实照（ink×paper colorize）；程序化几何兜底（IKB 圆 + 墨条 + 细线网格）
---

# Swiss International Typographic Style

## 身份纪律（来自 guizang 主题规范）

- **单一锚点色**：高级灰白底 + 唯一高饱和 IKB 蓝。禁止第二高亮色相;
  图表第二序列用 IKB 深阶/灰阶,不引入新色。
- **灰阶是校色过的"高级灰"**：paper 不是纯白、ink 不是纯黑,不许改。
- **越大越细**：巨字 Light(细),正文 Regular,小字(mono 角标/label)反而加重。
  大字收紧字距(-.02em ~ -.04em)。
- **直角、纯色、不透明**：无渐变、无阴影、无圆角。
- **左对齐纪律**：顶部中文标题贴左上内容轴;只有 statement/split 版式可居中。
- **发丝线只用于层级**：1px grey-2 分隔、2px ink 强分隔,不做装饰堆线。
  所有分隔线都是显式 `data-ppt="rect"`（CSS border 不进 pptx）。

## 版式对应（guizang 登记版式 → 本 look 原型）

| 原型 | 登记版式 | 处理 |
|---|---|---|
| cover | S01 IKB 满屏 | 反白细字重大标题 + 白 .24 发丝线 + 底部副标/元信息 |
| hero | S22 Image Hero | 顶部全宽黑白图条(268px) + 左对齐大标题 + 底部 KPI 三列(首列 accent) |
| section | S03 Split | 左 42% IKB 巨号编号,右纸底章节标题 |
| toc | Index rows | 编号(accent mono) + 细标题 + 页码,发丝线分级,space-evenly 满高 |
| kpi | S06/kpi-row | 顶部 2px 墨线 + 细巨数(首个 accent) + 加重 label + mono delta |
| table | Ledger | mono 表头 + 2px 墨线,行间 1px 灰线,首列加重,行 flex 满高 |
| chart | S07 | 原生图表(IKB+灰阶) + 右侧 IKB takeaway 块(唯一色块焦点) |
| comparison | S08 Duo | 中线对开;左灰方点,右 accent 方点(焦点侧) |
| two_col | 卡片填充 | 左 card-accent(唯一焦点) × 右 card-fill 灰,编号 mono |
| icon_grid | S04 Six Cells | 3×2,格顶 2px 墨线,1.5px 细描边图标,punch=accent |
| timeline | S11 | 1px 墨轴 + 方形节点,末站 accent 点亮 |
| bullets | Ledger list | mono 编号 + 发丝线,强调行 3px accent 左条 + 加重 |
| quote | S09 Statement | 细字重巨字宣言 + 角部 3×3 方阵(1 格 accent) |
| closing | S10 Split | 左 56% 墨色反白宣言,右纸底联系信息;与 IKB 封面色彩闭环 |

## 中西配对

拉丁/数字走 Inter(Light/Regular/SemiBold) + JetBrains Mono,中文回落
Noto Sans SC(Light/Regular/Bold);渲染层按 CJK_FAMILIES 分 a:latin / a:ea。
角色字体 2 族(display=Noto Sans SC Light / body=Noto Sans SC),
Inter×JBM 为配对附加字面,走 embed_families 嵌入。
