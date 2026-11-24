"""Fail-closed Word-only layout for the isolated Web English Year 6 RPH route.

The underlying generator supplies and owns ALL lesson text. We only move the
original paragraphs into a BM-KP2027-style, aligned A4 table layout. If a
future generator changes structure, return the original DOCX byte-for-byte.
Never call this on PI/Arabic/Jawi (their true RTL renderers are separate).
"""
from __future__ import annotations

from collections import Counter
from io import BytesIO
import re
from zipfile import BadZipFile, ZipFile

try:
    from lxml import etree
except ImportError:
    etree = None

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOCUMENT = "word/document.xml"
WIDTH = 10606  # A4 width 11906 twips minus existing 650 twips on each side
PASTEL = "E9F3F9"
NEUTRAL = "F5F7FA"
ACTIVITY = re.compile(r"^Activity [1-3]\s*\(\d+ minutes\)$", re.I)


def _node(name, **attrs):
    obj = etree.Element(W + name)
    for key, value in attrs.items():
        obj.set(W + key, str(value))
    return obj


def _text(paragraph):
    return "".join(element.text or "" for element in paragraph.iter(W + "t"))


def _cell(paragraphs, *, width, fill=None):
    cell = _node("tc")
    props = etree.SubElement(cell, W + "tcPr")
    props.append(_node("tcW", w=width, type="dxa"))
    if fill:
        props.append(_node("shd", val="clear", fill=fill))
    for paragraph in paragraphs:
        cell.append(paragraph)
    return cell


def _table(rows, widths, *, fills=None):
    table = _node("tbl")
    props = etree.SubElement(table, W + "tblPr")
    props.append(_node("tblW", w=WIDTH, type="dxa"))
    props.append(_node("tblInd", w=0, type="dxa"))
    props.append(_node("jc", val="left"))
    props.append(_node("tblLayout", type="fixed"))
    borders = etree.SubElement(props, W + "tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        borders.append(_node(side, val="single", sz=5, color="444444"))
    margins = etree.SubElement(props, W + "tblCellMar")
    for side, amount in (("top", 60), ("bottom", 60),
                         ("left", 85), ("right", 85)):
        margins.append(_node(side, w=amount, type="dxa"))
    grid = etree.SubElement(table, W + "tblGrid")
    for width in widths:
        grid.append(_node("gridCol", w=width))
    for parts in rows:
        row = etree.SubElement(table, W + "tr")
        for index, part in enumerate(parts):
            row.append(_cell(part, width=widths[index],
                             fill=fills[index] if fills else None))
    return table


def _bold_existing_activity_titles(paragraphs):
    # Styling an existing isolated heading does not alter a single w:t token.
    for paragraph in paragraphs:
        if not ACTIVITY.fullmatch(_text(paragraph).strip()):
            continue
        for run in paragraph.findall(W + "r"):
            props = run.find(W + "rPr")
            if props is None:
                props = etree.Element(W + "rPr")
                run.insert(0, props)
            if props.find(W + "b") is None:
                props.append(_node("b", val=1))


def _source_text(root):
    protected = (W + "t", W + "instrText", W + "delText",
                 W + "delInstrText")
    return Counter((node.tag, node.text or "")
                   for node in root.iter() if node.tag in protected)


def boxed_word_bytes(original, field_pairs):
    """Restyle only a recognisable *English Year 6* raw DOCX; preserve text.

    Returns original bytes on unsupported layout, malformed ZIP, unknown
    labels, source changes, or package modification. The three source header
    paragraphs and every original field paragraph survive untouched except
    optional bold typography for existing Activity 1/2/3 headings.
    """
    if etree is None or not isinstance(original, bytes) or not original.startswith(b"PK\x03\x04"):
        return original
    try:
        with ZipFile(BytesIO(original), "r") as source:
            names = source.namelist()
            if DOCUMENT not in names or source.testzip() is not None:
                return original
            xml = source.read(DOCUMENT)
            root = etree.fromstring(xml)
            body = root.find(W + "body")
            if body is None or any(child.tag not in (W + "p", W + "sectPr")
                                   for child in body):
                return original
            paras = body.findall(W + "p")
            if len(paras) < 3 + 2 * len(field_pairs):
                return original
            if (not _text(paras[0]).startswith("CIKGULAJU AI")
                    or "RANCANGAN PENGAJARAN HARIAN" not in _text(paras[0])
                    or not _text(paras[1]).startswith("ENGLISH YEAR 6 |")
                    or _text(paras[2]) != "Class:    Date:    Time:"):
                return original
            labels = [label + ":" for _, label in field_pairs]
            positions = []
            cursor = 3
            for label in labels:
                index = next((i for i in range(cursor, len(paras))
                              if _text(paras[i]) == label), None)
                if index is None:
                    return original
                # No source paragraph may be discarded between fields.
                if positions and index <= positions[-1]:
                    return original
                positions.append(index)
                cursor = index + 1
            if positions[0] != 3:
                return original
            chunks = []
            for i, pos in enumerate(positions):
                end = positions[i + 1] if i + 1 < len(positions) else len(paras)
                if end == pos + 1:
                    return original
                # Every paragraph, including blank lines, remains in place
                # in its original field and original sequence.
                chunks.append(([paras[pos]], paras[pos + 1:end]))
            before = _source_text(root)
            original_section = body.find(W + "sectPr")
            header = _table([([paras[0], paras[1]], [paras[2]])],
                            (7500, WIDTH - 7500), fills=(PASTEL, NEUTRAL))
            for index, (field, _) in enumerate(field_pairs):
                if field == "AKTIVITI UTAMA":
                    _bold_existing_activity_titles(chunks[index][1])
            transformed = [header]
            for start, end in ((0, 9), (9, 12), (12, len(field_pairs))):
                transformed.append(_table(chunks[start:end], (2920, WIDTH - 2920),
                                          fills=(PASTEL, None)))
            for child in list(body):
                body.remove(child)
            for child in transformed:
                body.append(child)
            if original_section is not None:
                body.append(original_section)
            if _source_text(root) != before:
                return original
            updated = etree.tostring(root, xml_declaration=True,
                                     encoding="UTF-8", standalone=True)
            if updated == xml:
                return original
            out = BytesIO()
            with ZipFile(out, "w") as target:
                for item in source.infolist():
                    target.writestr(item, updated if item.filename == DOCUMENT
                                    else source.read(item.filename))
            value = out.getvalue()
            # One last audit after serialization; any packaging issue fails
            # closed to the user's existing, working export.
            with ZipFile(BytesIO(value)) as check:
                if (check.namelist() != names or check.testzip() is not None
                        or any(check.read(name) != source.read(name)
                               for name in names if name != DOCUMENT)
                        or _source_text(etree.fromstring(check.read(DOCUMENT))) != before):
                    return original
            return value
    except (OSError, ValueError, TypeError, BadZipFile, etree.XMLSyntaxError):
        return original
