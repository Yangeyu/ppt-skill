"""Design tokens. One definition drives both the CSS (for browser layout)
and the renderer (fonts / chart palette). Swapping a theme re-skins the deck.

A theme carries two type roles — `display_font` (headlines, the serif star in
editorial themes) and `body_font` (running text) — mapped to majorFont/minorFont
in theme1.xml so PowerPoint can re-font from the UI."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Theme:
    id: str
    name: str
    colors: dict          # css-var name -> value
    display_font: str     # headlines / big type  -> majorFont
    body_font: str        # running text          -> minorFont
    chart_palette: list   # hex strings, no '#'

    def css_vars(self) -> str:
        rows = [f"--{k}: {v};" for k, v in self.colors.items()]
        rows.append(f'--font-serif: "{self.display_font}", "Songti SC", "STSong", serif;')
        rows.append(f'--font-sans: "{self.body_font}", "PingFang SC", '
                    '"Hiragino Sans GB", system-ui, sans-serif;')
        return ":root{\n  " + "\n  ".join(rows) + "\n}"

    def families(self) -> list:
        """Unique font families this theme needs embedded (body first)."""
        out = [self.body_font]
        if self.display_font not in out:
            out.append(self.display_font)
        return out

    def scheme(self) -> dict:
        """clrScheme slots -> hex. Written into theme1.xml so the whole deck
        is recolorable from PowerPoint's Design > Variants > Colors."""
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
        """Reverse map: 'RRGGBB' (upper, no #) -> schemeClr val. Lets the
        renderer emit theme refs instead of baked RGB so recolor propagates."""
        c = self.colors
        hx = lambda v: v.lstrip("#").upper()
        return {
            hx(c["ink"]): "tx1", hx(c["bg-content"]): "bg1",
            hx(c["bg"]): "tx2", hx(c["surface"]): "bg2",
            hx(c["primary"]): "accent1", hx(c["primary-2"]): "accent2",
        }


# Editorial — warm paper + ink + a single 朱砂 (vermilion) accent, serif headlines.
# Light content + paper cover; ink "chapter break" slides (section / quote / closing).
EDITORIAL = Theme(
    id="editorial",
    name="Editorial",
    colors={
        "bg": "#1C1815",            # deep warm ink (dark slides)
        "bg-2": "#2A2320",          # gradient companion / ghost tone on ink
        "bg-content": "#F5F0E6",    # warm paper (content + cover background)
        "ink": "#211C18",           # primary text on paper
        "muted": "#8A7F70",         # secondary text (warm taupe)
        "hairline": "#D9CFBE",      # hairline rules / borders
        "surface": "#ECE5D7",       # subtle card fill (a shade deeper than paper)
        "primary": "#C0392B",       # 朱砂 vermilion — the one accent
        "primary-2": "#A6703C",     # bronze / terracotta — secondary accent
        "pos": "#4F7A52",           # muted editorial green
        "neg": "#B23A2E",           # muted red (vermilion family)
        "on-dark": "#F2EBDD",       # paper text on ink
        "on-dark-muted": "#A99E8B", # muted paper on ink
        "glow": "#2A2320",          # ghost numeral / decorative tone on ink
    },
    display_font="Noto Serif SC",
    body_font="Noto Sans SC",
    chart_palette=["C0392B", "A6703C", "C8A15A", "7C6F5B", "4F7A52", "8A7F70"],
)

AURORA = Theme(
    id="aurora",
    name="Aurora",
    colors={
        "bg": "#0B1020", "bg-2": "#171544", "bg-content": "#FFFFFF",
        "ink": "#0F172A", "muted": "#64748B", "hairline": "#E2E8F0",
        "surface": "#F1F5F9", "primary": "#4F46E5", "primary-2": "#0E7490",
        "pos": "#059669", "neg": "#E11D48", "on-dark": "#F8FAFC",
        "on-dark-muted": "#94A3B8", "glow": "#232157",
    },
    display_font="Noto Sans SC",
    body_font="Noto Sans SC",
    chart_palette=["4F46E5", "0E7490", "8B5CF6", "F59E0B", "059669", "E11D48"],
)

EMBER = Theme(
    id="ember",
    name="Ember",
    colors={
        "bg": "#1A1110", "bg-2": "#3B1416", "bg-content": "#FFFFFF",
        "ink": "#1C1917", "muted": "#78716C", "hairline": "#E7E5E4",
        "surface": "#FAF7F5", "primary": "#E11D48", "primary-2": "#F97316",
        "pos": "#16A34A", "neg": "#DC2626", "on-dark": "#FFF7ED",
        "on-dark-muted": "#D6A78F", "glow": "#3F1D1B",
    },
    display_font="Noto Sans SC",
    body_font="Noto Sans SC",
    chart_palette=["E11D48", "F97316", "F59E0B", "84CC16", "06B6D4", "8B5CF6"],
)

THEMES = {t.id: t for t in (EDITORIAL, AURORA, EMBER)}
