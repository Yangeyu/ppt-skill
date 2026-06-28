"""Write our design tokens into the deck's theme1.xml (clrScheme + fontScheme).
This is what makes the output recolorable / re-fontable from the PowerPoint UI:
shapes/text that reference scheme colors follow Design > Colors instantly.

The theme is a generic part (opaque blob in python-pptx), so we parse, edit,
and write its bytes back."""
from __future__ import annotations
from lxml import etree
from pptx.opc.constants import RELATIONSHIP_TYPE as RT

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"a": A}


def _clr(slot: str, hexv: str) -> str:
    return f'<a:{slot}><a:srgbClr val="{hexv.lstrip("#").upper()}"/></a:{slot}>'


def _el(xml: str):
    return etree.fromstring(f'<root xmlns:a="{A}">{xml}</root>')[0]


def inject_theme(prs, theme):
    for master in prs.slide_masters:
        part = master.part.part_related_by(RT.THEME)
        root = etree.fromstring(part.blob)
        elements = root.find("a:themeElements", NS)

        sc = theme.scheme()
        clr_xml = (f'<a:clrScheme name="{theme.name}">'
                   + "".join(_clr(s, sc[s]) for s in
                             ("dk1", "lt1", "dk2", "lt2", "accent1", "accent2",
                              "accent3", "accent4", "accent5", "accent6", "hlink", "folHlink"))
                   + "</a:clrScheme>")
        elements.replace(elements.find("a:clrScheme", NS), _el(clr_xml))

        def font_block(tag, latin, ea):
            return (f'<a:{tag}><a:latin typeface="{latin}"/>'
                    f'<a:ea typeface="{ea}"/><a:cs typeface="{latin}"/></a:{tag}>')

        font_xml = (f'<a:fontScheme name="{theme.name}">'
                    + font_block("majorFont", theme.display_font, theme.display_font)
                    + font_block("minorFont", theme.body_font, theme.body_font)
                    + "</a:fontScheme>")
        elements.replace(elements.find("a:fontScheme", NS), _el(font_xml))

        part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
