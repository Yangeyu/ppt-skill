# ppt-mastra

ppt-tool 的 **Mastra** 模块（TypeScript）。用 [Mastra](https://mastra.ai/docs) 编排 agent，模型统一走 **`alibaba-cn/qwen3.7-plus`**——它本身支持多模态，识图直接用它，无需单独的 vision 模型。

## 为什么有这个模块

引擎本体**零模型**(所有智能在 agent 侧),所以需要一个真实的外部 agent 消费者
来验证整条链路。这个 TS 工程就是那个消费者:deckGenerator 走 skill 同款快路径
(契约直出 IR + 五重机器复核回喂),visionCritic 提供引擎里没有的识图美学评审
(读 `cli --render` 的 LibreOffice 真渲染)。

## Agents

| id | 作用 | 输入 |
|---|---|---|
| `deckGenerator` | Deck 生成官：素材原文 + 生成契约 → 整份 Deck IR；契约由驱动运行时调 `cli --contract <look>` 现场获取（单一来源），复核回路 = `cli --check-only`（IR 校验 + 事实/密度评论官）回喂自修 | 素材 + 契约 |
| `visionCritic` | 识图美学评论官，读页面截图打分（hierarchy/balance/design/boldness/fit）+ 改进建议（`--vision` 选装） | 图片 + 意图 |

评分维度对齐 `../docs/QUALITY.md` 页面层 rubric。

```bash
# 真 agent e2e:素材 → deckGenerator 自产 IR → 五重机器复核自修 → 原生 pptx
pnpm generate ../demos/data/isdin_report_full.md crimson        # 页数按素材自动推荐
pnpm generate <素材.md> <look> <页数>                            # 显式页数(下限硬控)
#   --staged      三段流(事实清单→大纲→落地):长且无结构的素材才值得
#   --vision      生成后 visionCritic 逐页评分出报告(看 LibreOffice 真渲染)
#   --vision-fix  实验性:低分页自动回喂修订
# 产物: ../out/<素材名>_<look>_mastra/(agent_deck.json 审计 + pptx + preview/ + rendered/)
```

## 用法

```bash
cd mastra
pnpm install
# key 走 DASHSCOPE_API_KEY（本地已配置；或复制 .env.example 到 .env）

# 识图 CLI：对一张幻灯片截图做美学评审
pnpm vision                                   # 默认评审 ../out_v03/slide_01_custom.png
pnpm vision ../out_v03/slide_03_kpi.png "KPI 数据页"
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
