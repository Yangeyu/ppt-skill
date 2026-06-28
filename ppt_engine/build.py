"""Orchestrator: IR -> archetype HTML -> browser layout/measure -> native pptx.
Optionally writes a PNG per slide (the faithful design preview)."""
from __future__ import annotations
import json
import tempfile
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright
from .theme import THEMES
from .ir import Deck
from .icons import ICONS
from .measure import MEASURE_JS
from .render import render_deck
from .fonts import prepare_fonts
from .embed_fonts import embed_fonts
from .units import CANVAS_W_PX, CANVAS_H_PX

TPL_DIR = Path(__file__).parent / "templates"


class Engine:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(TPL_DIR)),
            autoescape=select_autoescape(["html", "j2"]),
        )

    def _context(self, slide, theme, fonts=None):
        d = slide.data.model_dump()
        ctx = {"d": d, "css_vars": theme.css_vars(), "colors": theme.colors,
               "icons": ICONS, "fonts": fonts}
        if slide.kind == "chart":
            ctx["chart_json"] = json.dumps({
                "type": d["chart_type"],
                "categories": d["categories"],
                "series": [{"name": s["name"], "values": s["values"]} for s in d["series"]],
            }, ensure_ascii=False)
        return ctx

    def html_for(self, slide, theme, fonts=None):
        tpl = self.env.get_template(f"{slide.kind}.html.j2")
        return tpl.render(**self._context(slide, theme, fonts))

    def build(self, deck: Deck, out_path: str, screenshot_dir: str | None = None,
              embed: bool = True):
        theme = THEMES[deck.theme]
        fonts = prepare_fonts(deck, theme.families()) if embed else None
        asset_dir = Path(tempfile.mkdtemp(prefix="ppt_assets_"))
        slides_prims = []
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(channel="chrome")
            except Exception:
                browser = pw.chromium.launch()  # fall back to bundled chromium
            page = browser.new_page(
                viewport={"width": CANVAS_W_PX, "height": CANVAS_H_PX},
                device_scale_factor=2,
            )
            for idx, slide in enumerate(deck.slides):
                page.set_content(self.html_for(slide, theme, fonts), wait_until="load")
                page.evaluate("async () => { await document.fonts.ready; }")
                prims = page.evaluate(MEASURE_JS)
                # asset pipeline: rasterize each icon element to a transparent PNG
                icon_prims = [p for p in prims if p["kind"] == "icon"]
                if icon_prims:
                    els = page.query_selector_all('[data-ppt="icon"]')
                    for j, (p, el) in enumerate(zip(icon_prims, els)):
                        path = asset_dir / f"s{idx}_icon{j}.png"
                        el.screenshot(path=str(path), omit_background=True)
                        p["src"] = str(path)
                slides_prims.append(prims)
                if screenshot_dir:
                    page.screenshot(path=str(Path(screenshot_dir) / f"slide_{idx + 1:02d}_{slide.kind}.png"))
            browser.close()
        render_deck(deck, slides_prims, theme, out_path)
        if embed and fonts and fonts["families"]:
            embed_fonts(out_path, fonts)
        return slides_prims
