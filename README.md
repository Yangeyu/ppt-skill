# ppt-tool

两个模块,一条边界:**被测物与测试者分开**。

| 模块 | 是什么 | 入口 |
|---|---|---|
| [`ppt-skill/`](ppt-skill/) | **skill 本体**:SKILL.md 引导层 + 零模型排版引擎 + 机器评论官。自包含、可直接装载 | [`ppt-skill/SKILL.md`](ppt-skill/SKILL.md) · [`ppt-skill/README.md`](ppt-skill/README.md) |
| [`mastra/`](mastra/) | **外部 agent 消费者**(TypeScript/Mastra):用真实 LLM(qwen3.7-plus)走完整生成链路,验证 skill 的引导与评论官闭环 | [`mastra/README.md`](mastra/README.md) |

依赖方向单向:mastra → ppt-skill(spawn 其 cli、读其素材、产物落其 `out/`);
ppt-skill 对 mastra 零感知——换掉 mastra 或再加别的 agent 消费者,skill 不动。

## 快速开始

```bash
# 装载为 skill(agent 用)
ln -s "$(pwd)/ppt-skill" ~/.claude/skills/ppt-tool

# 初始化引擎环境
cd ppt-skill
python -m venv .venv && .venv/bin/python -m pip install -e ".[dev,mcp]"
.venv/bin/python -m playwright install chromium
.venv/bin/python -m pytest tests/ -q          # 25 项,毫秒级

# 真 agent e2e 验证(需 DASHSCOPE_API_KEY)
cd ../mastra && pnpm install
pnpm generate ../ppt-skill/demos/data/isdin_report_full.md crimson
```
