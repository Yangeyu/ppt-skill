"""MCP Server —— 智能体一行生成高颜值可编辑 pptx（DESIGN §13）。

工具：
 - list_seeds          列出可选 seed 主题（freedom 的起点/兜底）
 - art_direct_preview  仅生成并校验「设计语言」(spec)，给智能体先看气质
 - generate_deck       端到端：主题 → 七段管线 → 原生可编辑 .pptx（可选出截图+美学评审）

运行：`ppt-mcp`（stdio）。需要 LLM key（DASHSCOPE_API_KEY / OPENAI_API_KEY）走 freedom 路径，
无 key 时自动降级确定性 seed。"""
from __future__ import annotations
import os
from mcp.server.fastmcp import FastMCP

from ppt_engine.spec import THEMES, SpecLock
from ppt_engine.artdirect import art_direct, DesignBrief
from ppt_engine.compose import generate

mcp = FastMCP("ppt-engine")


@mcp.tool()
def list_seeds() -> list[dict]:
    """列出可选 seed 主题（艺术总监的起点/兜底）。"""
    return [{"id": t.id, "name": t.name,
             "primary": t.colors["primary"], "paper": t.colors["bg-content"],
             "display_font": t.display_font, "body_font": t.body_font}
            for t in THEMES.values()]


@mcp.tool()
def art_direct_preview(topic: str, audience: str = "", tone: str = "",
                       seed_theme: str | None = None) -> dict:
    """为主题现场生成「设计语言」(spec) 并过身份评论官，返回配色/字阶/母题/校验结果。
    用于让用户先确认气质，再决定是否出整套 deck。"""
    spec, issues = art_direct(DesignBrief(topic=topic, audience=audience,
                                          tone=tone, seed_theme=seed_theme))
    errs = [str(i) for i in issues if not isinstance(i, str) and getattr(i, "level", "") == "error"]
    return {
        "name": spec.name,
        "rationale": spec.rationale,
        "palette": {k: spec.colors[k] for k in ("bg-content", "ink", "primary", "primary-2", "muted")},
        "type_scale": spec.type_scale.sizes(),
        "fonts": {"display": spec.display_font, "body": spec.body_font},
        "image_treatment": spec.image.style,
        "motifs": [m.name for m in spec.motifs],
        "rules": spec.rules,
        "identity_errors": errs,
        "identity_ok": not errs,
    }


@mcp.tool()
def generate_deck(topic: str, out_path: str, audience: str = "", tone: str = "",
                  seed_theme: str | None = None, n_slides: int = 10,
                  screenshot_dir: str | None = None, aesthetic: bool = False) -> dict:
    """端到端生成高颜值原生可编辑 .pptx。返回路径 + 评论官摘要。
    out_path 为输出 .pptx 绝对路径；screenshot_dir 给定则同时出每页 PNG 预览。"""
    r = generate(topic, out_path=out_path, audience=audience, tone=tone,
                 seed_theme=seed_theme, n_slides=n_slides,
                 screenshot_dir=screenshot_dir, aesthetic=aesthetic)
    return {
        "out_path": r.out_path,
        "spec_name": r.spec.name,
        "n_slides": len(r.deck.slides),
        "routing": [("creative:" + s.data.role) if s.kind == "custom" else ("structured:" + s.kind)
                    for s in r.deck.slides],
        "structural_errors": [str(i) for i in r.structural_errors],
        "structural_warnings": len([i for i in r.structural_issues if i.level == "warning"]),
        "repair_rounds": r.rounds,
        "aesthetic": [{"slide": a.slide, "scores": a.scores, "suggestion": a.suggestion}
                      for a in r.aesthetic_reports],
        "summary": r.summary(),
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
