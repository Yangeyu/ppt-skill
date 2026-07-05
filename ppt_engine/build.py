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
from .measure import MEASURE_JS
from .render import render_deck
from .fonts import prepare_fonts
from .embed_fonts import embed_fonts
from . import genimage
from .units import CANVAS_W_PX, CANVAS_H_PX


class Engine:
    def __init__(self):
        self._envs = {}

    def _env_for(self, theme):
        if theme.id not in self._envs:
            self._envs[theme.id] = Environment(
                loader=FileSystemLoader(str(theme.templates_dir)),  # looks are self-contained
                autoescape=select_autoescape(["html", "j2"]),
            )
        return self._envs[theme.id]

    def _context(self, slide, theme, fonts=None, extra=None):
        d = slide.data.model_dump()
        ctx = {"d": d, "css_vars": theme.css_vars(), "colors": theme.colors,
               "icons": theme.icons, "fonts": fonts}
        if extra:
            ctx.update(extra)
        if slide.kind == "chart":
            ctx["chart_json"] = json.dumps({
                "type": d["chart_type"],
                "categories": d["categories"],
                "series": [{"name": s["name"], "values": s["values"]} for s in d["series"]],
            }, ensure_ascii=False)
        return ctx

    def html_for(self, slide, theme, fonts=None, extra=None):
        env = self._env_for(theme)
        tpl = env.get_template(f"{slide.kind}.html.j2")
        return tpl.render(**self._context(slide, theme, fonts, extra))

    def build(self, deck: Deck, out_path: str, screenshot_dir: str | None = None,
              embed: bool = True):
        theme = THEMES[deck.theme]
        fonts = prepare_fonts(deck, theme) if embed else None
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
                extra = {}
                if slide.kind == "hero" and theme.art:
                    art = theme.art  # the look's image hooks (STYLE_SUFFIX / hero_* fns)
                    hp = str(asset_dir / f"hero_{idx}.png")
                    src = getattr(slide.data, "src", "")
                    prompt = getattr(slide.data, "prompt", "")
                    if prompt and not src:
                        # generic path: t2i content prompt -> the look's post-pass
                        src = genimage.generate(prompt, str(asset_dir / f"hero_{idx}_raw.png"),
                                                getattr(art, "STYLE_SUFFIX", "")) or ""
                    (art.hero_from_source(src, theme, hp) if src
                     else art.hero_generate(getattr(slide.data, "art", "sun"), theme, hp))
                    extra["hero_img"] = hp
                page.set_content(self.html_for(slide, theme, fonts, extra), wait_until="load")
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
