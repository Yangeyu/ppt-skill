---
name: ppt-tool
description: 把素材/主题生成高颜值、原生可编辑的 PPT。当用户要求制作 PPT/幻灯片/汇报 deck 时使用。你负责叙事与内容组织,排版几何全部交给引擎。
---

# ppt-tool:素材 → 咨询级原生 PPT

## 核心心智(先读)

- **你是报告策划,不是排版工**。你产出的是语义化的 Deck IR(JSON):每页选一个版式
  kind、填结构化字段。坐标/字号/折行全部由引擎(浏览器排版 → 原生 pptx)计算,
  **绝不手写任何坐标或 HTML**。
- **契约是现场获取的,不要凭记忆写 IR**。版式菜单、字数预算、该 look 的叙事纪律
  都在契约里,且随代码演进——每次任务第一步都要重新获取。
- **事实红线**:数字与事实只能逐字引用素材原文;禁止推导(加总/比值/换算);
  素材没给的联系方式/信息留空。引擎的事实评论官会机器复核,违规会被退回。

## 工作流(三段生成 + 生成后自查)

**为什么分段**:一步直出整份 IR 时,全局问题(论证链断裂/密度失衡/素材利用率低)
靠单页修补救不回来。先抽事实、再定大纲、最后填格,每段都有机器审核兜底。

0. **选 look**(按内容气质,用户指定则从其指定):
   - `crimson` 深红咨询风——竞品分析/战略报告/证据密集的论证
   - `swiss` 国际主义——数据年报/极简客观的陈述
   - `riso` Riso zine——文化/创意/轻松题材,宣言式表达
   - `morandi` 莫兰迪——工作汇报/项目进展/对上沟通

1. **事实清单**:取契约 → 把素材抽成结构化 facts(逐字摘录) → 机器审核:
   ```bash
   python -m ppt_engine.cli --contract <look> --stage factsheet
   # 产出 factsheet.json 后:
   python -m ppt_engine.cli --check-only --stage factsheet --source material.md < factsheet.json
   ```
2. **叙事大纲**:取契约 → 规划每页论点/版式/证据分配(先组织后填格) → 机器审核
   (页数硬控 ±20%、每证据页必须引用 fact_id、素材利用率、exhibit 配额):
   ```bash
   python -m ppt_engine.cli --contract <look> --stage outline --slides <页数>
   python -m ppt_engine.cli --check-only --stage outline --look <look> --slides <页数> \
       --factsheet factsheet.json < outline.json
   ```
3. **落地 Deck IR**:取 deck 契约,按已批准的大纲逐页填格(thesis 是标题底稿,
   fact_ids 指向证据;数字逐字以素材原文为准) → 三重复核:
   ```bash
   python -m ppt_engine.cli --contract <look> --slides <页数>          # deck 契约
   python -m ppt_engine.cli --deck deck.json --source material.md --check-only
   ```
   返回 IR 校验错误 + `fact_issues`(事实)+ `density_issues`(密度)。循环到全零。
4. **生成与自查**:
   ```bash
   python -m ppt_engine.cli --deck deck.json --source material.md
   ```
   返回 `out`(pptx)、`shots`(截图)、`issues`(布局)、`fact_issues`、`density_issues`。
   逐张读截图检查观感(层级/拥挤/空旷),三类 issues 全零才算完成;有问题改 IR 重来。

每段的中间产物(factsheet.json / outline.json / deck.json)都保存下来供用户审计。

## 边界

- 不要绕过契约自创 kind 或字段;不要为"填满版面"补素材里没有的内容。
- 截图里 hero 配图与原生图表不显示(只进 pptx),LibreOffice 预览的字体替换伪影
  不是 bug——细节见 references/workflow.md。
