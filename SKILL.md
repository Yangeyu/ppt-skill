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
- 所有命令在**本 skill 根目录**(本文件所在目录)执行;首次使用需
  `pip install -e .` + `python -m playwright install chromium`。

## 工作流(默认快路径)

0. **选 look**(按内容气质,用户指定则从其指定;权威菜单看
   `python -m ppt_engine.cli --looks`):
   - `crimson` 深红咨询风——竞品分析/战略报告/证据密集的论证
   - `swiss` 国际主义——数据年报/极简客观的陈述
   - `riso` Riso zine——文化/创意/轻松题材,宣言式表达
   - `morandi` 莫兰迪——工作汇报/项目进展/对上沟通

1. **定页数 N**:用户指定则用之;否则问引擎(按素材体量推荐):
   ```bash
   python -m ppt_engine.cli --recommend-pages --source material.md
   ```
   页数是覆盖率承诺:宁可拆页也不要把证据挤扁。

2. **取契约并写整份 Deck IR**:
   ```bash
   python -m ppt_engine.cli --contract <look> --slides <N>
   ```
   按契约的版式菜单/字数预算/叙事纪律逐页填格;数字逐字以素材原文为准。

3. **廉价复核回路**(秒级,不起浏览器,反复用):
   ```bash
   python -m ppt_engine.cli --deck deck.json --source material.md --check-only --slides <N>
   ```
   返回 IR 校验错误 + `fact_issues`(事实)+ `density_issues`(密度/页数下限)。
   循环修到全零,修复策略见 references/workflow.md。

4. **生成与自查**:
   ```bash
   python -m ppt_engine.cli --deck deck.json --source material.md --slides <N>
   ```
   返回 `out`(pptx)、`shots`(截图)、`issues`(布局)、`fact_issues`、`density_issues`。
   逐张读截图检查观感(层级/拥挤/空旷),三类 issues 全零才算完成;有问题改 IR 重来。

**升级路径**:素材长且无结构(口述稿/聊天记录/杂乱笔记)时,先抽事实清单、再定
大纲、最后落 IR 的三段流更稳,命令与审核见 references/workflow.md「三段流」节。
结构化报告直接走快路径——实测质量相当、耗时约 1/4。

中间产物(deck.json 等)保存下来供用户审计。

## 边界

- 不要绕过契约自创 kind 或字段;不要为"填满版面"补素材里没有的内容。
- 截图里 hero 配图与原生图表不显示(只进 pptx),LibreOffice 预览的字体替换伪影
  不是 bug——细节见 references/workflow.md。
