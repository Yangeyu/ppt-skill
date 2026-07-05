"""Orchestrator: IR -> archetype HTML -> browser layout/measure -> native pptx.
Optionally writes a PNG per slide (the faithful design preview).

Templates resolve through the look package first (looks/<id>/templates/), then
the shared templates/ dir (创作轨 custom 等公共原型). Hero image discipline —
t2i style suffix / re-ink post-pass / procedural fallback — lives in the look
package too; the engine never special-cases a look."""
from __future__ import annotations
import json
import re
import shutil
import tempfile
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright
from .spec import SpecLock, resolve_spec
from .looks import get_look
from .ir import Deck
from .icons import ICONS
from .measure import MEASURE_JS
from .render import render_deck
from .fonts import prepare_fonts
from .embed_fonts import embed_fonts
from . import genimage
from .units import CANVAS_W_PX, CANVAS_H_PX

TPL_DIR = Path(__file__).parent / "templates"

# 标题强调词标记：**词** —— 模板把每段拆成独立文本原语，标记段上强调色。
# （文本原语是叶子级单色 run，行内混色必须拆段才能原生进 pptx。）
_MARK_RE = re.compile(r"\*\*(.+?)\*\*")


def marksplit(s: str) -> list[dict]:
    out, pos = [], 0
    s = s or ""
    for m in _MARK_RE.finditer(s):
        if m.start() > pos:
            out.append({"text": s[pos:m.start()], "mark": False})
        out.append({"text": m.group(1), "mark": True})
        pos = m.end()
    if pos < len(s):
        out.append({"text": s[pos:], "mark": False})
    return out or [{"text": "", "mark": False}]


class Engine:
    def __init__(self):
        self._envs = {}

    def _env_for(self, template_dir: str):
        if template_dir not in self._envs:
            dirs = [template_dir, str(TPL_DIR)] if template_dir else [str(TPL_DIR)]
            env = Environment(
                loader=FileSystemLoader(dirs),
                autoescape=select_autoescape(["html", "j2"]),
            )
            env.filters["marksplit"] = marksplit
            self._envs[template_dir] = env
        return self._envs[template_dir]

    def _context(self, slide, theme, look, fonts=None, extra=None):
        d = slide.data.model_dump()
        ctx = {"d": d, "css_vars": theme.css_vars(), "colors": theme.render_colors(),
               "icons": look.icons or ICONS, "fonts": fonts,
               "page_no": 0, "page_total": 0, "deck_title": ""}
        if extra:
            ctx.update(extra)
        if slide.kind == "chart":
            ctx["chart_json"] = json.dumps({
                "type": d["chart_type"],
                "categories": d["categories"],
                "series": [{"name": s["name"], "values": s["values"]} for s in d["series"]],
            }, ensure_ascii=False)
        return ctx

    def html_for(self, slide, theme, fonts=None, extra=None, look=None):
        look = look or get_look(theme)
        env = self._env_for(look.template_dir)
        tpl = env.get_template(f"{slide.kind}.html.j2")
        return tpl.render(**self._context(slide, theme, look, fonts, extra))

    def _hero_image(self, slide, theme, look, asset_dir: Path, idx: int) -> str:
        """The look-owned image pipeline: prompt -> t2i (+style suffix) ->
        re-ink post-pass; else source image re-inked; else procedural fallback."""
        out = str(asset_dir / f"hero_{idx}.png")
        src = getattr(slide.data, "src", "")
        prompt = getattr(slide.data, "prompt", "")
        if prompt and not src:
            src = genimage.generate(prompt, str(asset_dir / f"hero_{idx}_raw.png"),
                                    style_suffix=look.image_style_suffix) or ""
        if src:
            if look.image_postprocess:
                look.image_postprocess(src, theme, out)
            else:
                shutil.copyfile(src, out)
            return out
        if look.image_fallback:
            look.image_fallback(getattr(slide.data, "art", "sun"), theme, out)
            return out
        return ""

    def build(self, deck: Deck, out_path: str, screenshot_dir: str | None = None,
              embed: bool = True, spec: SpecLock | None = None):
        # v0.3: 排版/渲染统一吃一份 SpecLock（与 theme.Theme 接口兼容）。
        # 优先用显式 spec；否则按 deck.theme 解析（look / seed / 兜底）。
        theme = spec if spec is not None else resolve_spec(deck.theme)
        look = get_look(theme)
        fonts = prepare_fonts(deck, theme.embed_list()) if embed else None
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
                extra = {"page_no": idx + 1, "page_total": len(deck.slides),
                         "deck_title": deck.meta.title}
                if slide.kind == "hero":
                    extra["hero_img"] = self._hero_image(slide, theme, look, asset_dir, idx)
                page.set_content(self.html_for(slide, theme, fonts, extra, look),
                                 wait_until="load")
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
