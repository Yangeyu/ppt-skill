# ppt-skill —— 素材进,咨询级原生 PPT 出

**本目录是一个 agent skill**([`SKILL.md`](SKILL.md) 在目录根):把本目录放进(或软链到)
`~/.claude/skills/ppt-tool/`,任何 agent 即可装载。agent 负责叙事与内容组织,
排版几何全部交给引擎——产物不是把页面拍扁成图,而是真·DrawingML:文字是文本框、
形状是矢量、图表是原生图表对象、配色走主题色引用(PowerPoint 一键换肤)、字体已嵌入。

```bash
# agent 视角的最小闭环(SKILL.md 教的快路径)
python -m ppt_engine.cli --looks                                   # ① 选 look
python -m ppt_engine.cli --recommend-pages --source material.md    # ② 定页数
python -m ppt_engine.cli --contract crimson --slides 22            # ③ 取契约,写 Deck IR
python -m ppt_engine.cli --deck deck.json --source material.md --check-only --slides 22   # ④ 秒级复核,修到全零
python -m ppt_engine.cli --deck deck.json --source material.md --slides 22                # ⑤ 生成+自查
```

> 设计文档:[`docs/DESIGN.md`](docs/DESIGN.md)(v0.3 北极星与实现状态注记)、
> [`docs/QUALITY.md`](docs/QUALITY.md)(可执行的高颜值 rubric)。

## 三层分工

- **skill 管"怎么想"**:`SKILL.md` 引导 agent——第一步永远是现场取**生成契约**
  (版式菜单+字数预算从 `ir.py` schema 自动生成;叙事/组织/数据表现纪律来自各
  look 包的 `guidance.md`——**每个 look 是一种报告哲学,不只是一种配色**)。
- **引擎管"怎么排"**:agent 只产语义 IR,坐标/字号/折行由无头浏览器的 CSS 引擎
  算出,**绝不由模型目测**;导出原生可编辑 pptx。**引擎零模型**——不含任何
  LLM 调用,全部智能在 agent 侧。
- **评论官管"对不对"**:五重机器关卡回喂自修——① pydantic schema(硬拒)、
  ② 事实评论官(数字溯源/闭合槽位,抓推导与编造)、③ 密度评论官(页面信息量
  下限,档位声明在 look 包)、④ 结构评论官(真实几何的越界/重叠/离板色/低对比)、
  ⑤ 覆盖率(页数下限硬控,不许压缩证据)。prompt 说服不了的,机器把关。

## 它和别的方案有什么不同

颜值 = **A 层·体系纪律**(字阶/中西混排/留白/对比/网格/配色克制,可编码=地板)+
**B 层·艺术指导**(套印错位/戏剧裁切/打破网格,靠品味=天花板)。AI deck 之所以丑,
99% 丑在 A 层塌了。本引擎据此设计:

- **排版几何由浏览器(CSS 引擎)算出** —— 绕开「LLM 手写绝对坐标 SVG」漂移
  10–50px 的根本缺陷(对标 ppt-master 的自承问题)。
- **look 包 = 冻结的设计语言 + 版式库 + 叙事纪律 + 图像纪律**(四段自包含,
  身份必须过身份评论官门禁)——B 层由人预先精修,A 层由机器逐页保证。
- **事实是红线**:数字只能逐字引用素材原文,禁止推导;评论官机器复核,
  实测抓住"18.7 倍(8.77万÷4689)""超80%(81.88% 圆整)"这类幻觉。
- **产物原生可编辑** —— 颜色映射回 `schemeClr` 主题引用,可一键换色;
  图表是原生图表对象,可改数据。

## 安装

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,mcp]"
python -m playwright install chromium
# hero 配图 t2i 需 DASHSCOPE_API_KEY;无 key 自动落各 look 的程序化兜底图
```

## 消费形态

| 形态 | 入口 | 说明 |
|---|---|---|
| **skill** | `SKILL.md` | agent 装载本目录,按快路径四步走(默认形态) |
| **cli** | `python -m ppt_engine.cli` | JSON bridge:stdout 一行 JSON,日志走 stderr |
| **MCP** | `ppt-mcp`(stdio) | 与 skill 同构:`list_looks_tool / recommend_pages / get_contract / check_deck / build_deck` |
| **mastra** | `cd ../mastra && pnpm generate <素材.md> <look>` | 兄弟模块:外部真 agent e2e(qwen3.7-plus),验证整条链路 |

## 工程结构

```
SKILL.md       skill 入口:引导 agent 的工作流(契约→IR→复核回路→自查)
references/    skill 二级文档(cli 往返细节/三段流/修复策略/已知伪影)
ppt_engine/    执行引擎(零模型)
  looks/       模板库=look 包(crimson/swiss/riso/morandi,每包四段:
               身份 SpecLock + 版式 templates/*.j2 + 图像 image.py + 叙事 guidance.md,
               选型 pick_when 与密度配额 density 也在包内;_shared/ 放跨 look 公共原型)
  contract.py  生成契约单一来源(kind 菜单+字数预算自动来自 ir.py ⊕ 事实纪律 ⊕ look guidance)
  ir.py        受约束语义 IR(pydantic,判别联合;字数上限即 schema)
  stages.py    三段流模型与审核 + 页数派生(recommend_pages*)
  build.py     浏览器编排(Playwright 排版+量测+截图)
  measure.py   MEASURE_JS 抽取 data-ppt 原语
  render.py    原语 → 原生 DrawingML(schemeClr / 原生图表 / 嵌字)
  critic/      评论官:identity(look 门禁)+ structural(几何)+ facts(事实)+ density(密度)
  genimage.py  hero t2i(qwen-image-2.0)+ look 后处理再上墨
ppt_mcp/       MCP 接入(契约面,与 skill 同构)
demos/         手写基准 deck(各 look 一份)+ 无 Node 冒烟(agent_generate.py)
tests/         确定性地板测试(评论官/令牌纪律/质量链,无需浏览器/LLM)
docs/          DESIGN.md(北极星)+ QUALITY.md(rubric)
```

测试:`pytest tests/ -q`(25 项,毫秒级,无需浏览器/LLM/网络)。

## 北极星(尚未实现,方向见 docs/DESIGN.md)

「按主题现场生成设计语言(freedom)」:艺术总监(LLM)为任意主题现场发明一套
身份,过身份评论官(`critic/identity.py`,已实现并服役)后冻结为**新的 look 包**。
正确形态是"生成 look 包",而非绕过 look 包渲染——版式已按 look 特化,杂交渲染
会破坏身份一致性(旧 compose 管线因此于 2026-07-06 拆除,git 历史可考)。
