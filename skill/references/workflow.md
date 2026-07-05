# workflow.md —— cli 往返细节与修复策略

## stdout 约定

cli 的 stdout 永远是**一行 JSON**(唯一例外:`--contract` 输出纯文本契约,
因为它本身就是要拼进上下文的文档);人类可读日志全部走 stderr。

## 各阶段返回

| 场景 | 关键字段 | 处理 |
|---|---|---|
| JSON 解析失败 | `stage:"parse"` | 修 JSON 语法 |
| IR 校验失败 | `stage:"validate"`, `errors[].loc/msg` | 按 loc 定位字段修;超限=精炼文本,不是截断 |
| 阶段审核(`--stage factsheet/outline`) | `stage:"check-*"`, `issues[]` | quote 非原文=重新逐字摘抄;页数/配额/证据分配按 detail 调大纲 |
| `--check-only`(deck)通过 | `stage:"check"`, `fact_issues[]`, `density_issues[]` | 逐条修(见下) |
| 生成成功 | `out/shots/issues/fact_issues/density_issues` | 三零 + 截图过目才交付 |
| 引擎失败 | `stage:"build"` | 通常是环境问题(Playwright/字体),报告用户 |

## fact_issues 修复策略

- `number-unsourced`:该数字素材里没有。**不要找个相近的数替换**——回素材找原数;
  是推导值(比值/加总)就改写成素材里的原始两个数;找不到就删掉这个说法。
- `fabricated-contact`:contact 一律给 `""`(素材明确提供联系方式时除外)。
- `too-many-sections`:合并相邻主题,删章节幕页,总数 ≤3。

## density_issues 修复策略

- `exhibit-quota`:把有数字支撑的主论证页(chart/table/kpi)升格为 exhibit 复合版面。
- `thin-page`:按 detail 的指示补内容——**从素材/事实清单里补,不是编**;
  素材确实薄就并页,不要为凑数造事实。

已知误报边界:分数写法(如"1/3")与单个数字不检;"素材里有这个数但换了单位"会被
标出(如 2.46万 写成 24.6k)——写法跟素材保持一致即可避免。

## 修复回路的成本档位

- `--check-only`:纯校验+事实复核,不起浏览器,**秒级**。修 IR 时反复用它。
- 完整生成:浏览器排版+截图+pptx,分钟级。只在 check 双零后跑。

## 预览的三个已知伪影(不是 bug,不要试图"修")

1. 逐页截图(shots)里 **hero 配图与原生图表是空白**——它们只进 pptx
   (t2i 图与 DrawingML 原生图表不经过浏览器预览)。
2. 用 LibreOffice 打开 pptx 时**中文标题可能折行/重叠**——LO 会替换嵌入字体,
   PowerPoint 下无此问题。
3. 同一 hero prompt 两次生成构图有波动(t2i 非确定);无网络/无 key 时
   自动落程序化兜底图。

## 产物位置约定

`--out` 缺省时:`out/<deck标题slug>/<slug>.pptx` + `out/<slug>/preview/*.png`。
