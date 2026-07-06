"""MCP Server —— skill 工作流的 MCP 形态(与 SKILL.md 同构)。

工具(对应 skill 快路径的四步):
 - list_looks_tool     look 选型菜单(id/pick_when/summary)
 - recommend_pages     按素材体量推荐页数(全工程唯一启发式的 MCP 出口)
 - get_contract        取生成契约(kind 菜单+字数预算+look 叙事纪律,拼进 prompt)
 - check_deck          廉价复核:IR 校验 + 事实/密度评论官,秒级,修复回路用
 - build_deck          生成原生可编辑 .pptx(+ 布局评论官/截图)

引擎零模型:本服务不调用任何 LLM——写 IR 的智能在 MCP 客户端(agent)侧。"""
from __future__ import annotations
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ppt_engine.contract import render_contract
from ppt_engine.looks import LOOKS, list_looks

mcp = FastMCP("ppt-tool")


def _deck_payload(deck_json: str) -> dict:
    from ppt_engine.cli import _normalize_deck
    return _normalize_deck(json.loads(deck_json))


def _critique(payload: dict, source_path: str, n_slides: int) -> dict:
    """IR 校验 + 事实/密度评论官 —— check_deck 与 build_deck 共用的复核面。"""
    from pydantic import ValidationError
    from ppt_engine.critic.density import check_density
    from ppt_engine.critic.facts import check_facts
    from ppt_engine.ir import Deck
    try:
        deck = Deck.model_validate(payload)
    except ValidationError as e:
        return {"ok": False, "errors": json.loads(e.json())}
    fact_issues = []
    if source_path:
        fact_issues = check_facts(payload, Path(source_path).read_text("utf-8"))
    density_issues = check_density(payload, deck.theme)
    if n_slides:
        tol = max(2, round(n_slides * 0.2))
        if len(deck.slides) < n_slides - tol:
            density_issues.append({
                "slide": 0, "type": "page-count",
                "detail": f"仅 {len(deck.slides)} 页,低于目标 {n_slides}-{tol}——"
                          "不要压缩证据:按'一页一论点'拆开,补齐素材中未用的事实"})
    return {"ok": True, "deck": deck, "fact_issues": fact_issues,
            "density_issues": density_issues}


@mcp.tool()
def list_looks_tool() -> list[dict]:
    """look 选型菜单:每个 look 的 id、适用场景(pick_when)与气质摘要。"""
    return list_looks()


@mcp.tool()
def recommend_pages(source_path: str) -> dict:
    """按素材体量推荐页数(页数是覆盖率承诺,宁可拆页不要挤压证据)。"""
    from ppt_engine.stages import recommend_pages_from_source
    text = Path(source_path).read_text("utf-8")
    return {"recommended_pages": recommend_pages_from_source(text)}


@mcp.tool()
def get_contract(look: str, n_slides: int = 14) -> str:
    """取生成契约(纯文本,拼进你的上下文):kind 菜单与字数预算自动来自
    IR schema,叙事/密度纪律来自该 look 包的 guidance.md。写 IR 前必读。"""
    if look not in LOOKS:
        return f"unknown look '{look}' (have: {', '.join(LOOKS)})"
    return render_contract(look, n_slides)


@mcp.tool()
def check_deck(deck_json: str, source_path: str = "", n_slides: int = 0) -> dict:
    """廉价复核(不起浏览器,秒级):IR 校验 + 事实评论官(需 source_path)+
    密度/页数评论官。循环修到全零再 build_deck。"""
    r = _critique(_deck_payload(deck_json), source_path, n_slides)
    if not r["ok"]:
        return {"ok": False, "errors": r["errors"]}
    return {"ok": True, "slides": len(r["deck"].slides),
            "fact_issues": r["fact_issues"], "density_issues": r["density_issues"]}


@mcp.tool()
def build_deck(deck_json: str, source_path: str = "", n_slides: int = 0,
               out_path: str = "") -> dict:
    """生成原生可编辑 .pptx。返回产物路径 + 布局/事实/密度评论官结果;
    三类 issues 全零才算合格,有问题改 IR 重来。"""
    from ppt_engine.build import Engine
    from ppt_engine.selfcheck import check_layout

    payload = _deck_payload(deck_json)
    r = _critique(payload, source_path, n_slides)
    if not r["ok"]:
        return {"ok": False, "errors": r["errors"]}
    deck = r["deck"]

    if not out_path:
        from ppt_engine.outdir import out_dir
        dest = out_dir(deck.meta.title)
        out_path = str(dest / f"{dest.name}.pptx")
    shots = str(Path(out_path).parent / "preview")
    Path(out_path).resolve().parent.mkdir(parents=True, exist_ok=True)

    prims = Engine().build(deck, out_path, screenshot_dir=shots)
    return {
        "ok": True,
        "out_path": str(Path(out_path).resolve()),
        "shots": shots,
        "slides": len(prims),
        "kinds": [s.kind for s in deck.slides],
        "layout_issues": check_layout(prims),
        "fact_issues": r["fact_issues"],
        "density_issues": r["density_issues"],
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
