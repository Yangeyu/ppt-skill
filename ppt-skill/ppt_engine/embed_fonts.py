"""Embed subsetted fonts into a saved .pptx (python-pptx can't). We add the
font parts, content-type, relationships, and <p:embeddedFontLst>, and flip
embedTrueTypeFonts on — so the deck renders identically with no fonts installed.
Handles several families (e.g. a serif headline + a sans body face)."""
from __future__ import annotations
import os
import zipfile
from lxml import etree

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
FONT_RT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"


def _bytes(el):
    return etree.tostring(el, xml_declaration=True, encoding="UTF-8", standalone=True)


def embed_fonts(pptx_path: str, fonts: dict):
    families = fonts["families"]
    with zipfile.ZipFile(pptx_path) as z:
        items = {n: z.read(n) for n in z.namelist()}

    # 1) content type for .fntdata
    ct = etree.fromstring(items["[Content_Types].xml"])
    if not any(d.get("Extension") == "fntdata" for d in ct.findall(f"{{{CT}}}Default")):
        d = etree.SubElement(ct, f"{{{CT}}}Default")
        d.set("Extension", "fntdata")
        d.set("ContentType", "application/x-fontdata")
    items["[Content_Types].xml"] = _bytes(ct)

    # 2/3) font binaries + relationships (fresh rIds)
    rels = etree.fromstring(items["ppt/_rels/presentation.xml.rels"])
    used = {r.get("Id") for r in rels.findall(f"{{{PR}}}Relationship")}

    def fresh():
        i = 1
        while f"rId{i}" in used:
            i += 1
        used.add(f"rId{i}")
        return f"rId{i}"

    n = 0
    embedded = []  # (typeface, rid_regular, rid_bold)
    for fam in families:
        rid_reg, rid_bold = fresh(), fresh()
        for rid, blob in ((rid_reg, fam["regular"]), (rid_bold, fam["bold"])):
            n += 1
            part = f"fonts/font{n}.fntdata"
            items[f"ppt/{part}"] = blob
            rel = etree.SubElement(rels, f"{{{PR}}}Relationship")
            rel.set("Id", rid)
            rel.set("Type", FONT_RT)
            rel.set("Target", part)
        embedded.append((fam["typeface"], rid_reg, rid_bold))
    items["ppt/_rels/presentation.xml.rels"] = _bytes(rels)

    # 4) presentation.xml: embed flags + <p:embeddedFontLst> (ordered after notesSz)
    pres = etree.fromstring(items["ppt/presentation.xml"])
    pres.set("embedTrueTypeFonts", "1")
    pres.set("saveSubsetFonts", "1")
    efl = etree.Element(f"{{{P}}}embeddedFontLst")
    for typeface, rid_reg, rid_bold in embedded:
        ef = etree.SubElement(efl, f"{{{P}}}embeddedFont")
        etree.SubElement(ef, f"{{{P}}}font").set("typeface", typeface)
        etree.SubElement(ef, f"{{{P}}}regular").set(f"{{{R}}}id", rid_reg)
        etree.SubElement(ef, f"{{{P}}}bold").set(f"{{{R}}}id", rid_bold)
    notes_sz = pres.find(f"{{{P}}}notesSz")
    notes_sz.addnext(efl)
    items["ppt/presentation.xml"] = _bytes(pres)

    # 5) rewrite the package ([Content_Types].xml first)
    tmp = pptx_path + ".tmp"
    order = ["[Content_Types].xml"] + [k for k in items if k != "[Content_Types].xml"]
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in order:
            zf.writestr(name, items[name])
    os.replace(tmp, pptx_path)
