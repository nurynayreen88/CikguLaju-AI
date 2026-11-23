"""Align only existing Jawi *value paragraphs* in active native PI RPH Word.

The native RTL tables already reverse their physical cell order. LibreOffice's
logical left paragraph justification is displayed on the physical RIGHT of
these RTL tables; changing only w:jc does not touch any academic text/font.
Never use on non-Jawi content, 696-archive layouts, or unverified structures.
"""
from __future__ import annotations

from collections import Counter
from copy import copy
from io import BytesIO
from zipfile import ZipFile, BadZipFile

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOCUMENT = "word/document.xml"
TITLE = "رنچڠن ڤڠاجرن هارين"


def _text(node):
    return "".join(x.text or "" for x in node.iter(W + "t"))


def _tokens(root):
    protected = {W + "t", W + "instrText", W + "delText", W + "delInstrText"}
    return Counter((n.tag, n.text or "") for n in root.iter() if n.tag in protected)


def align_active_pi_rtl_value_bytes(original):
    """Return styled bytes for known 4-table native PI Word, else original."""
    if not isinstance(original, bytes) or not original.startswith(b"PK\x03\x04"):
        return original
    try:
        with ZipFile(BytesIO(original)) as source:
            names = source.namelist()
            if DOCUMENT not in names or source.testzip() is not None:
                return original
            root = etree.fromstring(source.read(DOCUMENT))
            body = root.find(W + "body")
            if body is None:
                return original
            tables = body.findall(W + "tbl")
            if len(tables) != 4:
                return original
            title = next((p for p in body.findall(W + "p")
                          if body.index(p) < body.index(tables[0])
                          and _text(p).strip() == TITLE), None)
            if title is None:
                return original
            first = tables[0]
            header_rows = first.findall(W + "tr")
            if (len(header_rows) != 1
                    or len(header_rows[0].findall(W + "tc")) != 2
                    or first.find(W + "tblPr/" + W + "bidiVisual") is None):
                return original
            if "ڤنديديقن اسلام" not in _text(header_rows[0].findall(W + "tc")[0]):
                return original
            if "کلس" not in _text(header_rows[0].findall(W + "tc")[1]):
                return original
            for idx, table in enumerate(tables[1:]):
                width = (2, 3, 2)[idx]
                rows = table.findall(W + "tr")
                if (not rows
                        or table.find(W + "tblPr/" + W + "bidiVisual") is None
                        or any(len(r.findall(W + "tc")) != width for r in rows)):
                    return original
            before = _tokens(root)
            changed = False
            for table in tables[1:]:
                for row in table.findall(W + "tr"):
                    # Only value-column paragraphs. Do not flip label fonts,
                    # table order or teacher details, nor reflow the prose.
                    value = row.findall(W + "tc")[1]
                    for p in value.findall(W + "p"):
                        text = _text(p)
                        if not any("\u0600" <= c <= "\u08ff" for c in text):
                            continue
                        pr = p.find(W + "pPr")
                        if pr is None:
                            pr = etree.Element(W + "pPr")
                            p.insert(0, pr)
                        jc = pr.find(W + "jc")
                        if jc is None:
                            jc = etree.SubElement(pr, W + "jc")
                        if jc.get(W + "val") != "left":
                            jc.set(W + "val", "left")
                            changed = True
                        bidi = pr.find(W + "bidi")
                        if bidi is None:
                            bidi = etree.SubElement(pr, W + "bidi")
                        if bidi.get(W + "val") != "1":
                            bidi.set(W + "val", "1")
                            changed = True
            if not changed or _tokens(root) != before:
                return original
            updated = etree.tostring(root, xml_declaration=True,
                                     encoding="UTF-8", standalone=True)
            out = BytesIO()
            with ZipFile(out, "w") as target:
                for item in source.infolist():
                    target.writestr(copy(item), updated if item.filename == DOCUMENT
                                    else source.read(item.filename))
            output = out.getvalue()
            with ZipFile(BytesIO(output)) as checked:
                if (checked.namelist() != names or checked.testzip() is not None
                        or _tokens(etree.fromstring(checked.read(DOCUMENT))) != before
                        or any(checked.read(n) != source.read(n)
                               for n in names if n != DOCUMENT)):
                    return original
            return output
    except (OSError, ValueError, TypeError, BadZipFile, etree.XMLSyntaxError) as exc:
        # Diagnostic type only; no school, teacher or academic text in logs.
        print("PI RTL alignment skipped:", type(exc).__name__, flush=True)
        return original
