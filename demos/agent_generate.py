"""agent 端到端(Python 冒烟版):素材原文 → LLM 自产 Deck IR → 复核回喂 → 引擎排版。

正式的外部 agent 消费者是 mastra/src/generate.ts(qwen3.7-plus);本脚本是
无 Node 环境下验证同一回路的冒烟件。契约不手写——与所有消费方一样从
ppt_engine.contract 现场渲染(单一来源);复核 = pydantic 校验 + 事实评论官。

用法: python demos/agent_generate.py demos/data/isdin_report.md [look=crimson] [页数=14]
需要 DASHSCOPE_API_KEY / OPENAI_API_KEY。原始 IR 存 out/<名>_<look>_agent/agent_deck.json。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from pydantic import ValidationError

from ppt_engine import llm
from ppt_engine.build import Engine
from ppt_engine.contract import render_contract
from ppt_engine.critic.facts import check_facts
from ppt_engine.ir import Deck
from ppt_engine.looks import LOOKS
from ppt_engine.selfcheck import check_layout

SYS = """你是顶级咨询公司的报告策划,擅长把研究素材组织成高质量演示文稿的结构化 IR。
严格遵守下面的契约(尤其字数上限与事实纪律)。只输出一个合法 JSON 对象,
不要围栏、不要解释。

{contract}"""


def _problems(data: dict, source: str) -> list[str]:
    """一轮复核:IR 校验 + 事实评论官,返回给模型的修复清单(空 = 通过)。"""
    out: list[str] = []
    try:
        Deck.model_validate(data)
    except ValidationError as e:
        for er in json.loads(e.json())[:12]:
            out.append(f"- [IR校验] {'.'.join(str(x) for x in er['loc'])}: {er['msg']}")
        return out                     # 结构都不对时先修结构,事实复核下一轮再说
    for fi in check_facts(data, source):
        out.append(f"- [事实复核] slide {fi['slide']} {fi['type']}: {fi['detail']}")
    return out


def gen_deck(source: str, look_id: str, n_slides: int, max_repair: int = 3):
    sys_p = SYS.format(contract=render_contract(look_id, n_slides))
    usr = f"素材如下,请组织成约 {n_slides} 页的 deck(JSON):\n\n{source}"
    feedback = ""
    for rnd in range(max_repair + 1):
        print(f"→ LLM 生成 IR(第 {rnd + 1} 次)…", file=sys.stderr)
        data = llm.chat_json(sys_p, usr + feedback, temperature=0.4, max_tokens=8000)
        probs = _problems(data, source)
        if not probs:
            return Deck.model_validate(data), data, rnd
        print(f"  ✗ {len(probs)} 处问题,回喂修复", file=sys.stderr)
        feedback = ("\n\n上一版未通过机器复核,请修正后重新输出完整 JSON"
                    "(字数超限请精炼;素材中查无的数字请删除或改写):\n"
                    + "\n".join(probs[:14])
                    + f"\n\n上一版:\n{json.dumps(data, ensure_ascii=False)}")
    raise SystemExit("模型多轮仍未通过复核,中止")


def main():
    if not llm.available():
        raise SystemExit("未配置 DASHSCOPE_API_KEY / OPENAI_API_KEY")
    src_path = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "demos/data/isdin_report.md")
    look_id = sys.argv[2] if len(sys.argv) > 2 else "crimson"
    n_slides = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    assert look_id in LOOKS, f"未知 look {look_id}(可选: {', '.join(LOOKS)})"

    source = Path(src_path).read_text("utf-8")
    deck, raw, rounds = gen_deck(source, look_id, n_slides)
    if deck.theme != look_id:                    # 模型忘写 theme 时兜底,不改内容
        deck = deck.model_copy(update={"theme": look_id})

    dest = ROOT / "out" / f"{Path(src_path).stem}_{look_id}_agent"
    (dest / "preview").mkdir(parents=True, exist_ok=True)
    (dest / "agent_deck.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=1), "utf-8")

    out = str(dest / f"{dest.name}.pptx")
    prims = Engine().build(deck, out, screenshot_dir=str(dest / "preview"))
    issues = check_layout(prims)
    print(f"已生成 {out}")
    print(f"  {len(prims)} 页 · {sum(len(p) for p in prims)} 原语 · 复核修复 {rounds} 轮")
    print(f"  版式路由: {[s.kind for s in deck.slides]}")
    print(f"  结构自检: {issues or '零问题 ✓'}")


if __name__ == "__main__":
    main()
