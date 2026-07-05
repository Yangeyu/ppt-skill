"""Render-self-check loop (§10). Two layers:
 - check_layout: cheap structural invariants on resolved geometry (no render).
 - render_preview: the feedback channel — rasterize the real .pptx to PNGs
   for a human / vision model to review."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from .units import CANVAS_W_PX, CANVAS_H_PX

SOFFICE = ["soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice"]


# pages that are intentionally airy / full-bleed — exempt from the sparse check
_AIRY_KINDS = {"cover", "hero", "section", "quote", "closing"}
_SPARSE_FILL = 0.60      # content must reach at least this fraction of canvas height
_FOOT_ZONE = 60          # px above the bottom edge that belongs to footer chrome


def check_layout(slides_prims, bleed: int = 24, kinds: list | None = None) -> list[dict]:
    """Flag out-of-canvas text, overlapping text boxes, and sparse pages whose
    content stops high and leaves a slab of dead paper. Decorative shapes may
    bleed; text may not. Returns a structured issue list (empty == clean)."""
    issues = []
    for i, prims in enumerate(slides_prims, 1):
        kind = kinds[i - 1] if kinds else None
        # sparse page: ignore footer chrome, then ask how far real content reaches
        content = [p for p in prims
                   if not p.get("deco") and p["kind"] in ("text", "icon", "chart", "img")
                   and p["y"] + p["h"] < CANVAS_H_PX - _FOOT_ZONE]
        if kind not in _AIRY_KINDS and len(content) >= 4:
            bottom = max(p["y"] + p["h"] for p in content)
            if bottom < CANVAS_H_PX * _SPARSE_FILL:
                issues.append({"slide": i, "type": "sparse",
                               "detail": f"content ends at {int(bottom)}px "
                                         f"({bottom / CANVAS_H_PX:.0%} of canvas)"})
        # decorative text (ghost numerals etc.) bleeds/overlaps by design — skip it
        texts = [p for p in prims if p["kind"] == "text" and not p.get("deco")]
        for p in texts:
            if (p["x"] < -bleed or p["y"] < -bleed
                    or p["x"] + p["w"] > CANVAS_W_PX + bleed
                    or p["y"] + p["h"] > CANVAS_H_PX + bleed):
                issues.append({"slide": i, "type": "overflow", "detail": p["text"][:20]})
        for a in range(len(texts)):
            for b in range(a + 1, len(texts)):
                t1, t2 = texts[a], texts[b]
                ox = min(t1["x"] + t1["w"], t2["x"] + t2["w"]) - max(t1["x"], t2["x"])
                oy = min(t1["y"] + t1["h"], t2["y"] + t2["h"]) - max(t1["y"], t2["y"])
                if ox > 4 and oy > 6:
                    issues.append({"slide": i, "type": "overlap",
                                   "detail": f'「{t1["text"][:10]}」×「{t2["text"][:10]}」'})
    return issues


def _soffice():
    for c in SOFFICE:
        if shutil.which(c) or Path(c).exists():
            return c
    return None


def render_preview(pptx_path: str, out_dir: str, dpi: int = 110) -> list[Path]:
    """Rasterize the actual pptx -> per-slide PNGs (the review feedback channel)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    soffice = _soffice()
    if not soffice:
        return []
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out), pptx_path],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pdf = out / (Path(pptx_path).stem + ".pdf")
    if not pdf.exists():
        return []
    pdftoppm = shutil.which("pdftoppm") or "/opt/homebrew/bin/pdftoppm"
    subprocess.run([pdftoppm, "-png", "-r", str(dpi), str(pdf), str(out / "slide")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return sorted(out.glob("slide-*.png"))
