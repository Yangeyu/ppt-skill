"""Look loader. A *look* is a self-contained package under looks/<id>/:

    manifest.json     design tokens: colors, font stacks, embed list, chart palette,
                      major/minor fonts, and the family -> ttf file map
    templates/*.j2    the full archetype template set (self-contained, no fallback)
    fonts/*.ttf       every typeface the look embeds
    icons.json        look-specific icon glyphs, merged over the base stroke set
    art.py            optional image hooks: STYLE_SUFFIX (t2i prompt discipline),
                      hero_generate(seed, theme, out), hero_from_source(src, theme, out)
    constraints.json  cross-field layout caps (consumed by generators, e.g. mastra)
    agent.zh.md       LLM instruction fragment (aesthetic + archetype cheat-sheet)

Adding a look = adding one directory; the engine code does not change.
font_vars are emitted as CSS custom properties; templates reference them
(`var(--font-display)` etc.). major_font/minor_font map to theme1.xml."""
from __future__ import annotations
import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path
from .icons import ICONS

LOOKS_DIR = Path(__file__).parent / "looks"


@dataclass
class Theme:
    id: str
    name: str
    colors: dict           # css-var name -> value
    font_vars: dict        # css-var name -> font stack
    embed_fonts: list      # family names to subset + embed
    major_font: str        # display -> majorFont
    minor_font: str        # body    -> minorFont
    chart_palette: list    # hex strings, no '#'
    dir: Path              # the look package directory
    font_files: dict       # family name -> (regular ttf, bold ttf) under dir/fonts/
    icons: dict = field(default_factory=lambda: ICONS)
    _art: object = field(default=None, repr=False)

    @property
    def templates_dir(self) -> Path:
        return self.dir / "templates"

    @property
    def art(self):
        """Lazy-load the look's image hooks module (None if the look ships no art.py)."""
        if self._art is None:
            art_py = self.dir / "art.py"
            if not art_py.exists():
                return None
            spec = importlib.util.spec_from_file_location(f"ppt_engine.looks.{self.id}.art", art_py)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self._art = mod
        return self._art

    def constraints(self) -> dict:
        p = self.dir / "constraints.json"
        data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        return {k: v for k, v in data.items() if not k.startswith("_")}

    def agent_instructions(self) -> str:
        p = self.dir / "agent.zh.md"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def css_vars(self) -> str:
        rows = [f"--{k}: {v};" for k, v in self.colors.items()]
        rows += [f"--{k}: {v};" for k, v in self.font_vars.items()]
        return ":root{\n  " + "\n  ".join(rows) + "\n}"

    def families(self) -> list:
        return list(dict.fromkeys(self.embed_fonts))

    def scheme(self) -> dict:
        """clrScheme slots -> hex (written into theme1.xml for recolor)."""
        c = self.colors
        return {
            "dk1": c["ink"], "lt1": c["bg-content"],
            "dk2": c["bg"], "lt2": c["surface"],
            "accent1": c["primary"], "accent2": c["primary-2"],
            "accent3": "#" + self.chart_palette[2], "accent4": "#" + self.chart_palette[3],
            "accent5": "#" + self.chart_palette[4], "accent6": "#" + self.chart_palette[5],
            "hlink": c["primary"], "folHlink": c["primary-2"],
        }

    def color_slot(self) -> dict:
        """Reverse map 'RRGGBB' -> schemeClr val so the renderer emits theme refs."""
        c = self.colors
        hx = lambda v: v.lstrip("#").upper()
        return {
            hx(c["ink"]): "tx1", hx(c["bg-content"]): "bg1",
            hx(c["bg"]): "tx2", hx(c["surface"]): "bg2",
            hx(c["primary"]): "accent1", hx(c["primary-2"]): "accent2",
        }


def _load_look(look_dir: Path) -> Theme:
    m = json.loads((look_dir / "manifest.json").read_text(encoding="utf-8"))
    icons = dict(ICONS)  # base stroke icons stay resolvable under every look
    icons_json = look_dir / "icons.json"
    if icons_json.exists():
        extra = json.loads(icons_json.read_text(encoding="utf-8"))
        icons.update({k: v for k, v in extra.items() if not k.startswith("_")})
    return Theme(
        id=m["id"], name=m["name"], colors=m["colors"], font_vars=m["font_vars"],
        embed_fonts=m["embed_fonts"], major_font=m["major_font"], minor_font=m["minor_font"],
        chart_palette=m["chart_palette"], dir=look_dir,
        font_files={k: tuple(v) for k, v in m.get("fonts", {}).items()}, icons=icons,
    )


THEMES = {
    t.id: t for t in (
        _load_look(d) for d in sorted(LOOKS_DIR.iterdir())
        if (d / "manifest.json").exists()
    )
}
