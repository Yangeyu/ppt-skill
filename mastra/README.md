# ppt-mastra

ppt-tool 的 **Mastra** 模块（TypeScript）。用 [Mastra](https://mastra.ai/docs) 编排 agent，模型统一走 **`alibaba-cn/qwen3.7-plus`**——它本身支持多模态，识图直接用它，无需单独的 vision 模型。

## 为什么有这个模块

引擎本体**零模型决策**(所有智能在 agent 侧),所以需要真实的外部 agent 消费者
来验证。本工程提供**两种消费形态**,测的东西不同:

| 形态 | 命令 | 编排者 | 验证对象 |
|---|---|---|---|
| **skill 装载** | `pnpm skillgen`(别名 `pnpm test:e2e`) | **agent 自主**:SKILL.md 全文进 instructions,agent 只有平台通用工具(`bash`+`write_file`),skill 教的命令原样执行 | **skill 的引导力与可迁移性**(零适配代码;与 Claude Code 装载 ppt-master 同构) |
| **pipeline** | `pnpm generate` | 驱动代码(generate.ts)编排回路,agent 只产 IR | 引擎+契约+评论官(确定性、便宜,适合回归) |

> **e2e 验证以 `skillgen` 为唯一入口:agent 就是测试路口,由它自主跑完整个 PPT 流程。**
> 验证时不要传页数(页数由 agent 走引擎 `--recommend-pages` 按内容决定),更不要为绕开
> 环境问题改用 `generate` 或压页数——那会把"skill 自主出片能力"的验证污染成"驱动代码能出片"。
> `generate` 只用于引擎/契约的确定性回归,它的通过**不能**代表 skill 引导力通过。

## Agents

| id | 作用 | 输入 |
|---|---|---|
| `skillRunner` | **skill 装载形态主 agent**:运行时读入 `../ppt-skill/SKILL.md` 作 instructions;工具只有平台通用的 `bash`(在 skill 根执行)与 `write_file`(写 deck.json),**零 skill 专用逻辑**;无驱动代劳,工作流由 agent 按 skill 自主执行 | 素材路径(+可选 look/页数) |
| `deckGenerator` | Deck 生成官(pipeline 形态):素材原文 + 生成契约 → 整份 Deck IR;契约由驱动运行时调 `cli --contract <look>` 现场获取(单一来源),复核回路 = `cli --check-only` 回喂自修 | 素材 + 契约 |
| `visionCritic` | 识图美学评论官,读页面截图打分(hierarchy/balance/design/boldness/fit)+ 改进建议(`--vision` 选装) | 图片 + 意图 |

评分维度对齐 `../ppt-skill/docs/QUALITY.md` 页面层 rubric。

```bash
# skill 装载形态:通用 agent(bash+write_file)装载 SKILL.md,自主走完整工作流
pnpm skillgen demos/data/isdin_report_full.md riso   # 素材路径相对 skill 根,agent 自己 cat
pnpm skillgen <素材路径> [look] [页数]               # look/页数可省,agent 按 skill 决策

# pipeline 形态:驱动编排,agent 只产 IR(回归/CI 用)
pnpm generate ../ppt-skill/demos/data/isdin_report_full.md crimson        # 页数按素材自动推荐
pnpm generate <素材.md> <look> <页数>                            # 显式页数(下限硬控)
#   --staged      三段流(事实清单→大纲→落地):长且无结构的素材才值得
#   --vision      生成后 visionCritic 逐页评分出报告(看 LibreOffice 真渲染)
#   --vision-fix  实验性:低分页自动回喂修订
# 产物: ../ppt-skill/out/<素材名>_<look>_mastra/(agent_deck.json 审计 + pptx + preview/ + rendered/)
```

## 用法

```bash
cd mastra
pnpm install
# key 走 DASHSCOPE_API_KEY（本地已配置；或复制 .env.example 到 .env）

# 识图 CLI：对一张幻灯片截图做美学评审
pnpm vision                                   # 默认评审 ../ppt-skill/out/isdin_crimson/preview/slide-01.png
pnpm vision ../ppt-skill/out/isdin_crimson/preview/slide-05.png "KPI 数据页"
pnpm vision https://example.com/x.jpg "封面页"

# playground（浏览器里直接调 agent，可上传图片）
pnpm dev
```

## 模型路由

`src/mastra/config.ts` 里的 `QWEN_MODEL = "alibaba-cn/qwen3.7-plus"`。Mastra model router 按 `provider/model` 解析：`alibaba-cn` → DashScope 兼容端点，自动读取 `DASHSCOPE_API_KEY`。换模型只改这一处。

## 结构

```
mastra/
  src/
    mastra/
      index.ts              Mastra 实例（注册 agents，pnpm dev 入口）
      config.ts             QWEN_MODEL 模型常量
      agents/
        deck-generator.ts   Deck 生成官（人设;契约由驱动运行时注入）
        vision-critic.ts    识图美学评论官（多模态）
    generate.ts             e2e 驱动（pnpm generate;快路径默认,--staged/--vision 选装）
    vision.ts               识图 CLI（本地图片 → base64 → 识图 → 评分卡）
```
