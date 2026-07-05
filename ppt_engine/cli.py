"""JSON bridge: read a Deck IR as JSON, build the native .pptx (+ preview PNGs).

This is the entry point external orchestrators use (e.g. the Mastra agent
module under ../mastra): they *generate* the IR with an LLM, we validate it
against the same pydantic contract the Python demos use and run the same Engine.

A single JSON result object is written to **stdout**; every human/progress log
goes to **stderr**, so stdout stays cleanly machine-parseable by the caller.

Usage:
  python3 -m ppt_engine.cli --deck deck.json --out out.pptx [--shots dir] [--no-embed]
  cat deck.json | python3 -m ppt_engine.cli --out out.pptx        # deck via stdin
  python3 -m ppt_engine.cli --describe riso   # look metadata for generators
                                              # (icons / constraints / agent fragment)
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from .build import Engine
from .ir import Deck
from .selfcheck import check_layout


def _log(*a) -> None:
    print(*a, file=sys.stderr, flush=True)


def _emit(obj: dict) -> None:
    """The one and only thing written to stdout: a machine-readable result."""
    json.dump(obj, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.stdout.flush()


def describe(look_id: str) -> int:
    """Emit a look's generator-facing contract: the single source generators
    (mastra & co.) assemble prompts and normalization rules from."""
    from .theme import THEMES
    theme = THEMES.get(look_id)
    if theme is None:
        _emit({"ok": False, "stage": "describe",
               "error": f"unknown look '{look_id}' (have: {', '.join(THEMES)})"})
        return 5
    _emit({
        "ok": True,
        "id": theme.id,
        "name": theme.name,
        "icons": sorted(theme.icons),
        "constraints": theme.constraints(),
        "agent_instructions": theme.agent_instructions(),
    })
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ppt_engine.cli")
    ap.add_argument("--deck", help="path to Deck JSON (default: read stdin)")
    ap.add_argument("--out", help="output .pptx path")
    ap.add_argument("--shots", default=None, help="dir for per-slide browser preview PNGs")
    ap.add_argument("--no-embed", action="store_true", help="skip font subsetting/embed")
    ap.add_argument("--describe", metavar="LOOK", help="print look metadata as JSON and exit")
    args = ap.parse_args(argv)

    if args.describe:
        return describe(args.describe)
    if not args.out:
        ap.error("--out is required (unless using --describe)")

    raw = Path(args.deck).read_text("utf-8") if args.deck else sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        _emit({"ok": False, "stage": "parse", "error": f"invalid JSON: {e}"})
        return 2

    try:
        deck = Deck.model_validate(payload)
    except ValidationError as e:
        errs = json.loads(e.json())
        brief = "; ".join(
            f"{'.'.join(str(x) for x in er['loc'])}: {er['msg']}" for er in errs[:8]
        )
        _emit({"ok": False, "stage": "validate", "error": brief, "errors": errs})
        return 3

    _log(f"→ building '{deck.meta.title}' · theme={deck.theme} · {len(deck.slides)} slides")
    Path(args.out).resolve().parent.mkdir(parents=True, exist_ok=True)
    if args.shots:
        Path(args.shots).mkdir(parents=True, exist_ok=True)
    try:
        prims = Engine().build(deck, args.out, screenshot_dir=args.shots, embed=not args.no_embed)
    except Exception as e:  # engine/browser/render failure — report, don't crash the bridge
        _emit({"ok": False, "stage": "build", "error": f"{type(e).__name__}: {e}"})
        return 4

    issues = check_layout(prims, kinds=[s.kind for s in deck.slides])
    result = {
        "ok": True,
        "out": str(Path(args.out).resolve()),
        "slides": len(prims),
        "prims": sum(len(p) for p in prims),
        "kinds": [s.kind for s in deck.slides],
        "issues": issues,
        "shots": str(Path(args.shots).resolve()) if args.shots else None,
    }
    _log(f"✓ {result['slides']} slides · {result['prims']} prims · "
         f"{len(issues)} layout issue(s)")
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
