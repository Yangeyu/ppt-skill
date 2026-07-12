"""Orchestrator: IR -> archetype HTML -> browser layout/measure -> native pptx.
Optionally writes a PNG per slide (the faithful design preview).

Templates resolve through the look package first (looks/<id>/templates/), then
looks/_shared/ (创作轨 custom 等跨 look 公共原型) — 模板只有 look 包库一个家。
Hero image discipline — t2i style suffix / re-ink post-pass / procedural
fallback — lives in the look package too; the engine never special-cases a look."""
from __future__ import annotations
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from urllib import request as _urlreq
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

TPL_DIR = Path(__file__).parent / "looks" / "_shared"

# 标题强调词标记：**词** —— 模板把每段拆成独立文本原语，标记段上强调色。
# （文本原语是叶子级单色 run，行内混色必须拆段才能原生进 pptx。）
_MARK_RE = re.compile(r"\*\*(.+?)\*\*")


def _crop_to_aspect(path: str, aspect: float) -> None:
    """Center-crop a PNG to the slot's w/h aspect (native images can't srcRect)."""
    from PIL import Image
    im = Image.open(path)
    w, h = im.size
    if abs(w / h - aspect) < 0.02:
        return
    if w / h > aspect:
        nw = int(h * aspect)
        box = ((w - nw) // 2, 0, (w - nw) // 2 + nw, h)
    else:
        nh = int(w / aspect)
        box = (0, (h - nh) // 2, w, (h - nh) // 2 + nh)
    im.crop(box).save(path)


def _pad_to_aspect(path: str, aspect: float, color: str = "#FFFFFF") -> None:
    """Letterbox-pad a PNG to the slot aspect — evidence figures (data
    screenshots) must reach the native image box undistorted and uncropped."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if abs(w / h - aspect) < 0.02:
        return
    if w / h > aspect:
        nw, nh = w, int(w / aspect)
    else:
        nw, nh = int(h * aspect), h
    bg = Image.new("RGB", (nw, nh), color)
    bg.paste(im, ((nw - w) // 2, (nh - h) // 2))
    bg.save(path)


def _fetch_remote(url: str, asset_dir: Path, idx: int) -> str:
    """素材原文引用的远程证据图:下载落地;失败返回 ""(该页降级为无图)。"""
    ext = Path(url.split("?")[0]).suffix or ".png"
    dst = asset_dir / f"src_{idx}{ext}"
    try:
        opener = _urlreq.build_opener(_urlreq.ProxyHandler({}))
        req = _urlreq.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with opener.open(req, timeout=45) as r, open(dst, "wb") as f:
            f.write(r.read())
        return str(dst)
    except Exception as e:  # noqa: BLE001 — 网络失败不阻塞构建
        print(f"[build] src download failed ({e}): {url[:100]}", file=sys.stderr)
        return ""


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
        if d.get("chart_type") and d.get("series"):   # chart 页与 exhibit 复合页都带原生图表
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

    def _slide_image(self, slide, theme, look, asset_dir: Path, idx: int) -> str:
        """The look-owned image pipeline: prompt -> t2i (+style suffix) ->
        re-ink post-pass; else source image re-inked; else procedural fallback.
        Content-page slots (look.image_slots) pick the t2i size and get a
        center-crop to the slot's aspect so the native image never distorts."""
        slot = look.image_slots.get(slide.kind, {})
        out = str(asset_dir / f"hero_{idx}.png")
        src = getattr(slide.data, "src", "")
        if src.startswith(("http://", "https://")):   # 素材图通道:远程证据图先落地
            src = _fetch_remote(src, asset_dir, idx)
        if src and not Path(src).exists():   # 模型偶发往 src 填废值——忽略,走 prompt/兜底
            src = ""
        prompt = getattr(slide.data, "prompt", "")
        if prompt and not src:
            src = genimage.generate(prompt, str(asset_dir / f"hero_{idx}_raw.png"),
                                    style_suffix=look.image_style_suffix,
                                    size=slot.get("size", "1664*928")) or ""
        if src:
            # 证据截图类槽位声明 postprocess=False:再上墨会伤数据图可读性
            if look.image_postprocess and slot.get("postprocess", True):
                look.image_postprocess(src, theme, out)
            else:
                shutil.copyfile(src, out)
        elif look.image_fallback and slot.get("fallback", True):
            look.image_fallback(getattr(slide.data, "art", "sun"), theme, out)
        else:
            return ""
        if slot.get("aspect"):
            # fit=pad:证据图不裁不变形,纸色补边;默认居中裁切
            if slot.get("fit") == "pad":
                _pad_to_aspect(out, slot["aspect"], slot.get("pad_color", "#FFFFFF"))
            else:
                _crop_to_aspect(out, slot["aspect"])
        return out

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
                if slide.kind in ("hero", "figure") or getattr(slide.data, "prompt", ""):
                    extra["hero_img"] = self._slide_image(slide, theme, look, asset_dir, idx)
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
