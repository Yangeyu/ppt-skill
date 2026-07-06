"""JSON bridge: read a Deck IR as JSON, build the native .pptx (+ preview PNGs).

This is the entry point external orchestrators use (e.g. the Mastra agent
module under ../mastra): they *generate* the IR with an LLM, we validate it
against the same pydantic contract the Python demos use and run the same Engine.

A single JSON result object is written to **stdout**; every human/progress log
goes to **stderr**, so stdout stays cleanly machine-parseable by the caller.

Usage:
  python3 -m ppt_engine.cli --deck deck.json [--out out.pptx] [--shots dir] [--no-embed]
  cat deck.json | python3 -m ppt_engine.cli                       # deck via stdin
  python3 -m ppt_engine.cli --contract crimson [--slides 15]
      # 生成契约(kind 菜单+预算自动来自 ir.py schema + look guidance.md)。
      # 这是唯一输出纯文本(而非 JSON)的模式:契约本身就是要拼进 prompt 的文档。
  python3 -m ppt_engine.cli --deck deck.json --source material.md [--check-only]
      # --source: 生成后追加事实评论官(数字溯源/闭合槽位)结果 fact_issues
      # --check-only: 只做 IR 校验+事实复核不排版——给 agent 修复回路用的廉价档
  python3 -m ppt_engine.cli --looks                              # look 选型菜单(JSON)
  python3 -m ppt_engine.cli --recommend-pages --source material.md   # 按素材量推荐页数

--out 缺省时按统一约定落盘:out/<deck标题slug>/<slug>.pptx + preview/ 截图。
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from .build import Engine
from .ir import Deck
from .outdir import out_dir
from .selfcheck import check_layout


def _log(*a) -> None:
    print(*a, file=sys.stderr, flush=True)


def _emit(obj: dict) -> None:
    """The one and only thing written to stdout: a machine-readable result."""
    json.dump(obj, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.stdout.flush()


def _normalize_deck(payload):
    """输入宽容:模型偶发漏掉 "data" 包裹(把 {"kind":...} 直接当 slide)。
    纯格式问题代码修掉,不值得花一轮模型修复往返。"""
    if isinstance(payload, dict) and isinstance(payload.get("slides"), list):
        payload["slides"] = [
            {"data": s} if isinstance(s, dict) and "data" not in s and "kind" in s else s
            for s in payload["slides"]
        ]
        for s in payload["slides"]:
            d = s.get("data") if isinstance(s, dict) else None
            if not isinstance(d, dict):
                continue
            # 数字型的排版字段(页码芯片/章节号)容错为字符串
            if isinstance(d.get("number"), (int, float)):
                d["number"] = f"{int(d['number']):02d}"
            for it in d.get("items", []) if isinstance(d.get("items"), list) else []:
                if isinstance(it, dict) and isinstance(it.get("pages"), (int, float)):
                    it["pages"] = f"P{int(it['pages']):02d}"
    return payload


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ppt_engine.cli")
    ap.add_argument("--deck", help="path to Deck JSON (default: read stdin)")
    ap.add_argument("--out", help="output .pptx path (default: out/<title-slug>/<slug>.pptx)")
    ap.add_argument("--shots", default=None, help="dir for per-slide browser preview PNGs")
    ap.add_argument("--no-embed", action="store_true", help="skip font subsetting/embed")
    ap.add_argument("--looks", action="store_true",
                    help="list available looks (id/name/pick_when) as JSON and exit")
    ap.add_argument("--recommend-pages", action="store_true",
                    help="recommend a page count from --source size (single heuristic home)")
    ap.add_argument("--contract", metavar="LOOK", help="print the generation contract (plain text) and exit")
    ap.add_argument("--slides", type=int, default=None,
                    help="target page count: hint for --contract; coverage floor for deck checks")
    ap.add_argument("--source", help="path to source material; enables the facts critic")
    ap.add_argument("--check-only", action="store_true",
                    help="validate IR + facts/density critics only, skip layout/build")
    ap.add_argument("--stage", choices=["factsheet", "outline", "deck"], default="deck",
                    help="generation stage for --contract / --check-only (default: deck)")
    ap.add_argument("--look", help="look id for stage checks (outline has no theme field)")
    ap.add_argument("--factsheet", help="factsheet JSON path (for --check-only --stage outline)")
    ap.add_argument("--render", action="store_true",
                    help="also rasterize the real pptx via LibreOffice (vision review channel: "
                         "browser shots miss native charts/hero art)")
    args = ap.parse_args(argv)

    if args.looks:
        from .looks import list_looks
        _emit({"ok": True, "looks": list_looks()})
        return 0

    if args.recommend_pages:
        if not args.source:
            _emit({"ok": False, "stage": "recommend-pages", "error": "--recommend-pages 需要 --source"})
            return 2
        from .stages import recommend_pages_from_source
        text = Path(args.source).read_text("utf-8")
        _emit({"ok": True, "recommended_pages": recommend_pages_from_source(text)})
        return 0

    if args.contract:
        from .contract import render_contract
        from .looks import LOOKS
        from .stages import FACTSHEET_CONTRACT, outline_contract
        if args.contract not in LOOKS:
            _emit({"ok": False, "stage": "contract",
                   "error": f"unknown look '{args.contract}' (have: {', '.join(LOOKS)})"})
            return 5
        n = args.slides or 14
        if args.stage == "factsheet":
            print(FACTSHEET_CONTRACT)
        elif args.stage == "outline":
            print(outline_contract(args.contract, n))
        else:
            print(render_contract(args.contract, n))
        return 0

    raw = Path(args.deck).read_text("utf-8") if args.deck else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        _emit({"ok": False, "stage": "parse", "error": f"invalid JSON: {e}"})
        return 2

    # 阶段审核(两段式生成的 ①事实清单 / ②大纲):stdin 是阶段 JSON,不是 Deck IR
    if args.check_only and args.stage != "deck":
        from .stages import FactSheet, OutlinePlan, check_factsheet, check_outline
        model = FactSheet if args.stage == "factsheet" else OutlinePlan
        try:
            model.model_validate(payload)
        except ValidationError as e:
            errs = json.loads(e.json())
            _emit({"ok": False, "stage": f"validate-{args.stage}", "errors": errs})
            return 3
        if args.stage == "factsheet":
            if not args.source:
                _emit({"ok": False, "stage": "check", "error": "--stage factsheet 需要 --source"})
                return 2
            issues = check_factsheet(payload, Path(args.source).read_text("utf-8"))
            from .stages import recommend_pages
            _emit({"ok": True, "stage": "check-factsheet", "issues": issues,
                   "recommended_pages": recommend_pages(len(payload.get("facts", [])))})
            _log(f"✓ check factsheet · {len(issues)} issue(s)")
            return 0
        else:
            fs = json.loads(Path(args.factsheet).read_text("utf-8")) if args.factsheet else None
            issues = check_outline(payload, args.look or "", args.slides or 14, factsheet=fs)
        _log(f"✓ check {args.stage} · {len(issues)} issue(s)")
        _emit({"ok": True, "stage": f"check-{args.stage}", "issues": issues})
        return 0

    payload = _normalize_deck(payload)
    try:
        deck = Deck.model_validate(payload)
    except ValidationError as e:
        errs = json.loads(e.json())
        brief = "; ".join(
            f"{'.'.join(str(x) for x in er['loc'])}: {er['msg']}" for er in errs[:8]
        )
        _emit({"ok": False, "stage": "validate", "error": brief, "errors": errs})
        return 3

    fact_issues = None
    if args.source:
        from .critic.facts import check_facts
        source = Path(args.source).read_text("utf-8")
        fact_issues = check_facts(payload, source)

    from .critic.density import check_density
    density_issues = check_density(payload, args.look or deck.theme)
    # 覆盖率页数下限(与 stages.check_outline 同规则):显式传了 --slides 才启用
    if args.slides:
        tol = max(2, round(args.slides * 0.2))
        if len(deck.slides) < args.slides - tol:
            density_issues.append({
                "slide": 0, "type": "page-count",
                "detail": f"仅 {len(deck.slides)} 页,低于目标 {args.slides}-{tol}——"
                          "不要压缩证据:把挤在一页的论点按'一页一论点'拆开,补齐素材中未用的事实"})

    if args.check_only:                   # 廉价修复档:不起浏览器,秒级往返
        result = {"ok": True, "stage": "check", "kinds": [s.kind for s in deck.slides],
                  "fact_issues": fact_issues if fact_issues is not None else [],
                  "density_issues": density_issues}
        _log(f"✓ check-only · {len(deck.slides)} slides · "
             f"{len(result['fact_issues'])} fact · {len(density_issues)} density issue(s)")
        _emit(result)
        return 0

    if not args.out:                      # 统一产物约定:out/<slug>/(pptx + preview/)
        dest = out_dir(deck.meta.title)
        args.out = str(dest / f"{dest.name}.pptx")
        args.shots = args.shots or str(dest / "preview")

    _log(f"→ building '{deck.meta.title}' · theme={deck.theme} · {len(deck.slides)} slides")
    Path(args.out).resolve().parent.mkdir(parents=True, exist_ok=True)
    if args.shots:
        Path(args.shots).mkdir(parents=True, exist_ok=True)
    try:
        prims = Engine().build(deck, args.out, screenshot_dir=args.shots, embed=not args.no_embed)
    except Exception as e:  # engine/browser/render failure — report, don't crash the bridge
        _emit({"ok": False, "stage": "build", "error": f"{type(e).__name__}: {e}"})
        return 4

    issues = check_layout(prims)
    result = {
        "ok": True,
        "out": str(Path(args.out).resolve()),
        "slides": len(prims),
        "prims": sum(len(p) for p in prims),
        "kinds": [s.kind for s in deck.slides],
        "issues": issues,
        "shots": str(Path(args.shots).resolve()) if args.shots else None,
    }
    if fact_issues is not None:
        result["fact_issues"] = fact_issues
    result["density_issues"] = density_issues
    if args.render:
        from .selfcheck import render_preview
        rdir = str(Path(args.out).parent / "rendered")
        files = render_preview(args.out, rdir)
        result["rendered"] = rdir if files else None
    _log(f"✓ {result['slides']} slides · {result['prims']} prims · "
         f"{len(issues)} layout issue(s)"
         + (f" · {len(fact_issues)} fact issue(s)" if fact_issues is not None else "")
         + f" · {len(density_issues)} density issue(s)")
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
