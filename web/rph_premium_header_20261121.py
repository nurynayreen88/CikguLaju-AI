"""Conservative premium right-hand teacher banner for legacy three-table RPH Word.

Move existing display nodes (not lesson text) into a compact two-column banner.
Fail closed when the native layout differs from the audited structure. Specialty
Sains/DLP/PPKI/Jawi/Arabic renderers must not call this adapter.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from io import BytesIO
from zipfile import ZipFile

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOCUMENT = "word/document.xml"
FIELDS = ("subject", "year", "date", "day", "time", "class", "students", "topic")
ALIASES = {
    "mata pelajaran": "subject", "subject": "subject",
    "tahun/tingkatan": "year", "year / form": "year",
    "tarikh": "date", "date": "date",
    "hari": "day", "day": "day",
    "masa": "time", "time": "time",
    "kelas": "class", "class": "class",
    "bilangan murid": "students", "number of pupils": "students",
    "tajuk": "topic", "topic": "topic",
}
TITLES = {"rancangan pengajaran harian", "daily lesson plan"}


def _node(parent, tag, **attributes):
    node = etree.SubElement(parent, W + tag)
    for key, value in attributes.items():
        node.set(W + key, str(value))
    return node


def _text(node):
    return "".join(child.text or "" for child in node.iter(W + "t"))


def _cell_fill(cell, fill):
    props = _node(cell, "tcPr")
    _node(props, "tcW", w="6900", type="dxa")
    _node(props, "shd", val="clear", fill=fill)
    margins = _node(props, "tcMar")
    for side, amount in (("top", "80"), ("bottom", "70"), ("left", "125"), ("right", "125")):
        _node(margins, side, w=amount, type="dxa")
    return props


def _styled_paragraph(cell, label_cell, value_cell, *, font_size=17):
    paragraph = _node(cell, "p")
    props = _node(paragraph, "pPr")
    _node(props, "spacing", before=0, after=0, line=220, lineRule="auto")
    for i, old_cell in enumerate((label_cell, value_cell)):
        if i:
            separator = _node(paragraph, "r")
            _node(separator, "tab")
        for old_paragraph in old_cell.findall(W + "p"):
            for child in old_paragraph:
                if child.tag != W + "pPr":
                    item = deepcopy(child)
                    # Source strings are unchanged; only the banner's font size differs.
                    for run in item.iter(W + "r"):
                        rpr = run.find(W + "rPr")
                        if rpr is None:
                            rpr = etree.Element(W + "rPr")
                            run.insert(0, rpr)
                        sz = rpr.find(W + "sz")
                        if sz is None:
                            sz = _node(rpr, "sz")
                        sz.set(W + "val", str(font_size))
                    paragraph.append(item)
    return paragraph


def _make_banner(body, first_table, title, rows, fill):
    banner = etree.Element(W + "tbl")
    properties = _node(banner, "tblPr")
    _node(properties, "tblW", w="10630", type="dxa")
    _node(properties, "tblLayout", type="fixed")
    borders = _node(properties, "tblBorders")
    for edge in ("top", "bottom", "left", "right", "insideV"):
        _node(borders, edge, val="single", sz=6, color="6D7C8B")
    grid = _node(banner, "tblGrid")
    _node(grid, "gridCol", w="6900")
    _node(grid, "gridCol", w="3730")
    table_row = _node(banner, "tr")
    left = _node(table_row, "tc")
    leftpr = _cell_fill(left, fill)
    leftpr.find(W + "tcW").set(W + "w", "6900")
    right = _node(table_row, "tc")
    rightpr = _cell_fill(right, fill)
    rightpr.find(W + "tcW").set(W + "w", "3730")
    title.getparent().remove(title)
    left.append(title)
    for old_run in title.iter(W + "r"):
        rpr = old_run.find(W + "rPr")
        if rpr is None:
            rpr = etree.Element(W + "rPr")
            old_run.insert(0, rpr)
        if rpr.find(W + "b") is None:
            _node(rpr, "b")
        sz = rpr.find(W + "sz")
        if sz is None:
            sz = _node(rpr, "sz")
        sz.set(W + "val", "26")
    for name in ("subject", "year", "topic"):
        _styled_paragraph(left, *rows[name], font_size=18 if name != "topic" else 16)
    for name in ("class", "date", "day", "time", "students"):
        _styled_paragraph(right, *rows[name], font_size=15)
    body.insert(body.index(first_table), banner)


def premium_header_bytes(document, fill):
    """Preserve exactly the original w:t nodes, leaving unsupported layouts alone."""
    if not isinstance(document, bytes) or not document.startswith(b"PK\x03\x04"):
        return document
    with ZipFile(BytesIO(document)) as source:
        if DOCUMENT not in source.namelist() or source.testzip():
            return document
        original_xml = source.read(DOCUMENT)
        root = etree.fromstring(original_xml)
        body = root.find(W + "body")
        if body is None:
            return document
        tables = body.findall(W + "tbl")
        if len(tables) != 3:
            return document
        first = tables[0]
        details = first.findall(W + "tr")
        if len(details) < 10:
            return document
        if any(len(row.findall(W + "tc")) != 2 for row in details):
            return document
        if any(len(row.findall(W + "tc")) != 3 for row in tables[1].findall(W + "tr")):
            return document
        rows = {}
        for expected, table_row in zip(FIELDS, details):
            label_cell, value_cell = table_row.findall(W + "tc")
            key = ALIASES.get(" ".join(_text(label_cell).strip().casefold().split()))
            if key != expected:
                return document
            rows[key] = (label_cell, value_cell)
        title = next((p for p in body.findall(W + "p")
                      if body.index(p) < body.index(first)
                      and " ".join(_text(p).strip().casefold().split()) in TITLES), None)
        if title is None:
            return document
        before = Counter(item.text for item in root.iter(W + "t"))
        _make_banner(body, first, title, rows, fill)
        for row in details[:len(FIELDS)]:
            first.remove(row)
        after = Counter(item.text for item in root.iter(W + "t"))
        if before != after:
            raise ValueError("RPH header unexpectedly changed displayed source text")
        new_xml = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
        output = BytesIO()
        with ZipFile(output, "w") as target:
            for info in source.infolist():
                target.writestr(info, new_xml if info.filename == DOCUMENT else source.read(info.filename))
        return output.getvalue()
