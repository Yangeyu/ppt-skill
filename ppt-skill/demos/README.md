# demos/ —— 演示脚本统一入口

约定:**脚本在 `demos/`,产物在 `out/<名字>/`**(pptx + `preview/` 浏览器截图放一起,
整个 `out/` 已被 .gitignore 忽略,可随时重新生成)。

三个生成入口共用同一约定(`ppt_engine/outdir.py`):
- demos 脚本 → `out/<slug>/`(见下表)
- `python -m ppt_engine.cli`(JSON bridge,mastra 用)——`--out` 缺省 → `out/<deck标题>/`
- MCP `build_deck` —— `out_path` 缺省 → `out/<deck标题>/`

从仓库根运行(脚本自带 sys.path 引导,任意 cwd 均可):

```bash
.venv/bin/python demos/demo_isdin_crimson.py          # → out/isdin_crimson/
.venv/bin/python demos/demo_isdin_swiss.py            # → out/isdin_swiss/
.venv/bin/python demos/demo_isdin_riso.py             # → out/isdin_riso/
.venv/bin/python demos/demo_isdin_morandi.py          # → out/isdin_morandi/
.venv/bin/python demos/demo_beauty_riso.py            # → out/beauty_riso/
.venv/bin/python demos/demo.py                        # → out/growth_review/

# agent 端到端(正式入口是 mastra:cd mastra && pnpm generate ../ppt-skill/demos/data/isdin_report_full.md crimson 15)
# 本 Python 版为无 Node 环境的冒烟件;两者共用同一契约(cli --contract)与复核回路
.venv/bin/python demos/agent_generate.py demos/data/isdin_report_full.md crimson 15
```

前两个参数可覆盖默认位置:`demo_xxx.py [out.pptx] [截图目录]`。

| 脚本 | look | 内容 |
|---|---|---|
| demo_isdin_crimson.py | crimson | 怡思丁竞品分析·深红咨询版(15 页,含 exhibit 复合证据版面) |
| demo_isdin_swiss.py | swiss | 怡思丁双抗防晒竞品分析(16 页,验收标的) |
| demo_isdin_riso.py | riso | 同上内容的 riso 版 |
| demo_isdin_morandi.py | morandi | 同上内容的莫兰迪工作汇报版 |
| demo_beauty_riso.py | riso | 上海美妆 2026 趋势(14 页) |
| demo.py | riso | 企业增长复盘(v0.2 时代 A 层案例) |
| agent_generate.py | crimson | **真 agent e2e**:素材 md(`demos/data/isdin_report*.md`)→ LLM 自产 IR → 校验回喂 → 引擎;原始 IR 存 `out/<名>_<look>_agent/agent_deck.json` 供审计 |

注意:hero 页含 t2i(DashScope qwen-image-2.0),同 prompt 构图有波动;
无网络/无 key 时自动落到各 look 的程序化兜底图。浏览器截图不含 hero 图与
原生图表(只进 pptx),真效果看 LibreOffice/PowerPoint。
