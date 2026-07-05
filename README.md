# 高颜值 AI PPT 生成引擎 · v0.3

给一个**主题**，产出**原生可编辑、设计感强、贴合主题**的 `.pptx`。

不是把页面拍扁成图，而是真·DrawingML：文字是文本框、形状是矢量、图表是原生图表对象、配色走主题色引用（可在 PowerPoint 一键换肤）、字体已嵌入。

```bash
python demo_v03.py "独立书店与 zine 文化指南"
```

> 设计文档见 [`docs/DESIGN.md`](docs/DESIGN.md)（架构 v0.3，15 节）与 [`docs/QUALITY.md`](docs/QUALITY.md)（可执行的高颜值 rubric）。

## 组织形态:skill + 引擎 + 评论官

- **skill 管"怎么想"**:[`skill/SKILL.md`](skill/SKILL.md) 引导任何 agent 用本工具——
  第一步永远是 `python -m ppt_engine.cli --contract <look>` 现场取**生成契约**
  (版式菜单+字数预算从 `ir.py` schema 自动生成;叙事/组织/数据表现纪律来自各
  look 包第四段 `guidance.md`——每个 look 是一种报告哲学,不只是一种配色)。
- **引擎管"怎么排"**:agent 只产语义 IR,几何由浏览器算,导出原生可编辑 pptx。
- **评论官管"对不对"**:`--check-only --source` 秒级返回 IR 校验错误 + 事实复核
  (数字溯源/闭合槽位/结构数量),agent 回喂自修;prompt 说服不了的,机器把关。

外部 agent 消费者示例:`mastra/`(deckGenerator,`pnpm generate`)。

---

## 它和别的方案有什么不同

颜值 = **A 层·体系纪律**（字阶/中西混排/留白/对比/网格/配色克制，可编码=地板）+ **B 层·艺术指导**（套印错位/戏剧裁切/打破网格，靠品味=天花板）。AI deck 之所以丑，99% 丑在 A 层塌了。本引擎据此设计：

- **排版几何由浏览器（CSS 引擎）算出，绝不由模型目测坐标** —— 绕开「LLM 手写绝对坐标 SVG」漂移 10–50px 的根本缺陷。
- **视觉身份按主题现场生成（freedom）** —— LLM 当「艺术总监」为每个主题发明整套设计语言（给 zine 就长出 Riso 套印感），而非套固定模板。
- **递归 A/B：AI 提出美学，机器校验体系** —— 身份层(LLM 发明 → 身份评论官校验字阶/配色/对比) + 页面层(LLM 构图 → 结构评论官校验越界/对比/字阶)。地板由「浏览器正确几何 + 评论官循环」保证，非确定性也可证。
- **创作轨也原生可编辑** —— 创作页的颜色映射回 `schemeClr` 主题引用，可一键换色（ppt-master 写死 HEX 做不到）。

---

## 七段管线

```
主题
 ① 艺术总监(LLM)      为主题发明设计语言 → 候选 spec_lock（配色/字阶/字体/母题/图像处理）
 ② 身份评论官         校验设计系统是否体系成立（A 层递归）→ 不过则重生成
 ③ 套件实例化         通用骨架 ⊕ 生成令牌值 ⊕ 生成母题组件
 ④ 按角色路由         表现页→创作轨(LLM 写 HTML/CSS) ；结构页→模板轨(填 IR)
 ⑤ 浏览器排版         无头 Chrome 算几何 → 量原语 + 截图
 ⑥ 页面评论官         结构评论官(零模型) + 美学评论官(视觉模型) → 重生成 ≤N 轮
 ⑦ 渲染导出           原语 → 原生 DrawingML → 可编辑 .pptx
```

两条轨共用一份现场生成的 spec_lock、同走浏览器、同落原生 pptx → 同一 deck 内混排、身份一致、都可编辑。

---

## 安装

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[llm,dev,mcp]"
python -m playwright install chromium
# freedom 路径需 LLM key（任一）：
export DASHSCOPE_API_KEY=...    # 阿里 Qwen
# 或 export OPENAI_API_KEY=...  # OpenAI
```

无 key 时自动降级为确定性 seed 主题（editorial / aurora / ember），仍可出 deck。

---

## 用法

**命令行**
```bash
python demo_v03.py "2026 上半年增长复盘" 10
# → 增长复盘.pptx + out_v03/ 每页预览 PNG
```

**Python API**
```python
from ppt_engine.compose import generate
r = generate("独立书店与 zine 文化指南", out_path="zine.pptx",
             tone="复古印刷·手作感", n_slides=9, screenshot_dir="shots", aesthetic=True)
print(r.summary())          # 路由 / 评论官 error / 重生成轮次
```

**只看设计语言（先确认气质再出整套）**
```python
from ppt_engine.artdirect import art_direct, DesignBrief
spec, issues = art_direct(DesignBrief(topic="独立书店与 zine", tone="复古印刷"))
print(spec.name, spec.colors["primary"], [m.name for m in spec.motifs])
```

**MCP（智能体接入）** —— `ppt-mcp`（stdio），工具：`list_seeds` / `art_direct_preview` / `generate_deck`。

---

## 工程结构

```
ppt_engine/
  artdirect/   艺术总监 + 身份评论官（§4）   director.py  identity_critic.py
  spec.py      生成式 SpecLock（令牌/字阶/网格/母题）+ WCAG + 可读性归一
  theme.py     seed 主题（editorial/aurora/ember，可选起点/兜底）
  planner.py   主题 → Deck IR（双轨路由）
  ir.py        受约束 IR（结构页字数预算 + 创作页 CustomData）
  templates/   结构轨版式 j2 + custom.html.j2（设计系统套件）
  build.py     浏览器编排（Playwright 排版+量测+截图）
  measure.py   MEASURE_JS 抽取 data-ppt 原语
  render.py    原语 → 原生 DrawingML（schemeClr / 原生图表 / 嵌字）
  critic/      结构评论官(structural) + 美学评论官(aesthetic)
  compose.py   七段管线总入口 generate()
  llm.py       OpenAI 兼容封装（DashScope / OpenAI）
ppt_mcp/server.py   MCP 接入
tests/test_floor.py 确定性地板测试（11 项，无需浏览器/LLM）
```

测试：`pytest tests/ -q`
