"""Per-deck font subsetting. Take the open Noto statics (OFL) and keep only the
glyphs this deck uses — the same subset feeds BOTH the browser (@font-face, so
measurement is exact) AND the embedded pptx (so every viewer sees identical
type). A serif headline family + a sans body family come out a few KB each,
not 20 MB."""
from __future__ import annotations
import io
import base64
import string
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options

FONT_DIR = Path(__file__).parent / "assets" / "fonts"

# typeface name -> (regular file, bold file) under assets/fonts/
FONT_FILES = {
    "Noto Sans SC": ("NotoSansSC-Regular.ttf", "NotoSansSC-Bold.ttf"),
    "Noto Serif SC": ("NotoSerifSC-Regular.ttf", "NotoSerifSC-Bold.ttf"),
}

# glyphs templates inject beyond the IR text (punctuation, quotes, latin, digits)
BASE_CHARS = set(string.printable) | set("，。、·—–“”‘’：；％（）《》【】！？…　@&%")


def collect_chars(deck) -> set:
    chars: set[str] = set()

    def walk(o):
        if isinstance(o, str):
            chars.update(o)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                walk(v)

    walk(deck.model_dump())
    return chars | BASE_CHARS


def _subset(path: Path, unicodes: list[int]) -> bytes:
    font = TTFont(str(path))
    opt = Options()
    opt.name_IDs = ["*"]          # keep name table so family name survives
    opt.notdef_outline = True
    opt.recalc_timestamp = False
    ss = Subsetter(options=opt)
    ss.populate(unicodes=unicodes)
    ss.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def _family(typeface: str, unicodes: list[int]) -> dict:
    reg_file, bold_file = FONT_FILES[typeface]
    reg = _subset(FONT_DIR / reg_file, unicodes)
    bold = _subset(FONT_DIR / bold_file, unicodes)
    return {
        "typeface": typeface,
        "regular": reg, "bold": bold,
        "regular_b64": base64.b64encode(reg).decode(),
        "bold_b64": base64.b64encode(bold).decode(),
    }


def prepare_fonts(deck, families: list[str]) -> dict:
    """Subset every requested family over the deck's character set."""
    unicodes = [ord(c) for c in collect_chars(deck)]
    seen, fams = set(), []
    for tf in families:
        if tf in seen or tf not in FONT_FILES:
            continue
        seen.add(tf)
        fams.append(_family(tf, unicodes))
    return {"families": fams}
