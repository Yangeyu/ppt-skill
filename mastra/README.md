# ppt-riso-mastra

用 [Mastra](https://mastra.ai) + 通义千问 **`alibaba-cn/qwen3.7-plus`** 把一段「市场 brief」自动变成一套 **riso（Risograph zine）风格、原生可编辑**的 `.pptx`。

```
brief ──(qwen3.7-plus, 结构化输出)──▶ Deck IR (JSON) ──(ppt_engine, Python)──▶ 原生 riso .pptx + 预览 PNG
        └── deck-architect agent ──┘   └─ Zod schema 校验 ─┘   └─ 浏览器测量 + python-pptx 渲染 ─┘
```

- LLM 只负责「选版式、填内容」；排版由上一层的 Python `ppt_engine` 引擎完成，产出的是**可在 PowerPoint 里编辑**的原生形状 / 图表 / 图片，而非一张图。
- IR 契约（`src/mastra/schema.ts`）是 `../ppt_engine/ir.py` 的 Zod 镜像：同样的判别联合 `kind`、同样的字数预算。TS 侧生成时约束，Python 侧构建时再校验一遍。
- **look 包单一来源**：agent 的美学指令、版式 cheat-sheet、图标白名单、跨字段约束（如 toc≤6）都来自引擎的 look 包（`../ppt_engine/looks/riso/`），启动时经 `python3 -m ppt_engine.cli --describe riso` 动态拼装——本模块不手抄任何一份副本。

## 前置条件

- Node ≥ 20、已安装依赖（`npm install`）。
- 上一级仓库的 Python 引擎可用：`python3 -m ppt_engine.cli` 依赖 playwright(chrome) / jinja2 / pydantic / python-pptx / Pillow。
- **`DASHSCOPE_API_KEY`**（阿里云 DashScope 密钥，Mastra 的 model router 自动读取）。已在 shell 里 export 即可，无需 `.env`；也可复制 `.env.example` 为 `.env` 填入。

## 用法

```bash
npm run smoke      # 连通性冒烟：小 schema 验证模型 + 密钥 + 结构化输出（也会顺带验证 --describe 桥）
npm run beauty     # 内置「2026 中国美妆趋势洞察」brief → ../out/beauty_riso_ai/
npm run generate -- "你的自由 brief 文本"  [out.pptx]  [截图目录]
```

产物统一写到仓库根的 `out/<run-name>/`（gitignored）：
- `deck.pptx` —— 原生可编辑的 riso 演示。
- `deck.json` —— LLM 生成的 Deck IR，可手改后用 `python3 -m ppt_engine.cli --deck out/<run>/deck.json --out out/<run>/deck.pptx` **确定性重建**（不再调用 LLM）。
- `shots/` —— 每页浏览器截图（文字/版式的真实排版）。
  > 注意：原生**图表**与 hero **海报图**只在真实 `.pptx` 里出现，浏览器截图里是空占位；要看它们请渲染 pptx（`ppt_engine.selfcheck.render_preview` 走 LibreOffice）。

## 结构

| 文件 | 作用 |
|---|---|
| `src/mastra/schema.ts` | Deck IR 的 Zod 契约（镜像 `ir.py`） |
| `src/mastra/agents/deck-architect.ts` | 生成 Deck 的 agent：通用框架 + look 包指令片段动态拼装 |
| `src/mastra/tools/build-pptx.ts` | 把 ppt_engine 封装成 Mastra 工具 |
| `src/mastra/run-python.ts` | 桥接：`buildPptx()` 驱动 cli 构建；`describeLook()` 读 look 契约 |
| `src/mastra/index.ts` | Mastra 实例（注册 agent + 工具） |
| `src/briefs/beauty.ts` | 美妆市场测试 brief |
| `src/smoke.ts` / `src/generate.ts` | 冒烟测试 / 端到端驱动 |

## 换 look / 换选题

- 换 look：设 `PPT_LOOK=<id>`（look 需存在于 `../ppt_engine/looks/`，当前只有精调过的 `riso`）。指令、图标、约束会自动跟着 look 包走。
- 换选题：直接 `npm run generate -- "<brief>"`，或在 `src/briefs/` 里加一个新 brief 并登记进 `BRIEFS`。
