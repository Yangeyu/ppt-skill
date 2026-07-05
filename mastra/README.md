# ppt-mastra

ppt-tool 的 **Mastra** 模块（TypeScript）。用 [Mastra](https://mastra.ai/docs) 编排 agent，模型统一走 **`alibaba-cn/qwen3.7-plus`**——它本身支持多模态，识图直接用它，无需单独的 vision 模型。

## 为什么有这个模块

v0.3 七段管线里的**美学评论官（识图）**此前因 DashScope 账号无 `qwen-vl-*` 权限一直降级跑不起来。qwen3.7-plus 多模态补上了这块，于是把 AI 编排层用 Mastra 落成一个独立 TS 工程。

## Agents

| id | 作用 | 管线阶段 | 输入 |
|---|---|---|---|
| `visionCritic` | 识图美学评论官，读页面截图打分（hierarchy/balance/design/boldness/fit）+ 改进建议 | ⑥ | 图片 + 意图 |
| `artDirector` | 艺术总监，为主题现场生成设计语言（配色/字阶/字体/母题/图像处理） | ① | 主题文本 |

评分维度对齐 `../docs/QUALITY.md` 页面层 rubric。

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
        vision-critic.ts    识图美学评论官（多模态）
        art-director.ts     艺术总监
    vision.ts               识图 CLI（本地图片 → base64 → 识图 → 评分卡）
```
