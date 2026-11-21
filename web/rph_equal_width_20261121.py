"""Align the outer edges of all native premium Word RPH tables.

Presentation only. This adapter runs after the approved source-preserving
four-table premium header transform. It leaves each w:t text token identical
and returns the original document for layouts outside the audited contract.
"""
from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile
from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
XML = "word/document.xml"
RATIOS = ((3730, 6900), (530, 1345), (265, 1265, 345), (530, 1345))
MAX_WIDTH = 10630  # Established 18.75 cm RPH content width in twips.


def _find_or_add(parent, label, first=False):
    tag = W + label
    node = parent.find(tag)
    if node is None:
        node = etree.Element(tag)
        if first:
            parent.insert(0, node)
        else:
            parent.append(node)
    return node


def _printable_width(root):
    body = root.find(W + "body")
    section = body.find(W + "sectPr") if body is not None else None
    if section is None:
        return None
    size, margin = section.find(W + "pgSz"), section.find(W + "pgMar")
    if size is None or margin is None:
        return None
    try:
        available = (int(size.get(W + "w")) - int(margin.get(W + "left"))
                     - int(margin.get(W + "right")))
    except (ValueError, TypeError):
        return None
    return min(available, MAX_WIDTH) if 4500 <= available <= 13000 else None


def _set_table_geometry(table, target, ratios, *, rtl_jawi=False):
    weights = sum(ratios)
    widths = [round(target * part / weights) for part in ratios]
    widths[-1] = target - sum(widths[:-1])
    pr = _find_or_add(table, "tblPr", first=True)
    table_width = _find_or_add(pr, "tblW")
    table_width.set(W + "w", str(target))
    table_width.set(W + "type", "dxa")
    indent = _find_or_add(pr, "tblInd")
    indent.set(W + "w", "0")
    indent.set(W + "type", "dxa")
    align = _find_or_add(pr, "jc")
    align.set(W + "val", "right" if rtl_jawi else "left")
    if rtl_jawi:
        bidi = _find_or_add(pr, "bidiVisual")
        bidi.set(W + "val", "1")
    layout = _find_or_add(pr, "tblLayout")
    layout.set(W + "type", "fixed")

    grid = _find_or_add(table, "tblGrid")
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        element = etree.SubElement(grid, W + "gridCol")
        element.set(W + "w", str(width))

    for row in table.findall(W + "tr"):
        for index, cell in enumerate(row.findall(W + "tc")):
            props = _find_or_add(cell, "tcPr", first=True)
            cell_width = _find_or_add(props, "tcW")
            cell_width.set(W + "w", str(widths[index]))
            cell_width.set(W + "type", "dxa")


def equal_width_four_table_bytes(document, *, rtl_jawi=False):
    """Return aligned DOCX with identical displayed text and ZIP non-document parts.

    A document using merged or unrecognised table layouts is left intact.
    """
    if not isinstance(document, bytes) or not document.startswith(b"PK\x03\x04"):
        return document
    with ZipFile(BytesIO(document)) as source:
        if XML not in source.namelist() or source.testzip():
            return document
        before_xml = source.read(XML)
        root = etree.fromstring(before_xml)
        body = root.find(W + "body")
        if body is None:
            return document
        tables = body.findall(W + "tbl")
        if len(tables) != 4:
            return document
        for idx, table in enumerate(tables):
            rows = table.findall(W + "tr")
            if not rows or any(len(row.findall(W + "tc")) != len(RATIOS[idx]) for row in rows):
                return document
            if table.find(W + "tblGrid") is None:
                return document
        # A valid premium banner has exactly one row. The other tables
        # contain the existing details, teaching phases and reflection.
        if len(tables[0].findall(W + "tr")) != 1:
            return document
        target = _printable_width(root)
        if target is None:
            return document

        text_before = tuple(node.text for node in root.iter(W + "t"))
        for table, ratios in zip(tables, RATIOS):
            _set_table_geometry(table, target, ratios, rtl_jawi=rtl_jawi)
        if tuple(node.text for node in root.iter(W + "t")) != text_before:
            raise ValueError("Word RPH equal-width pass changed lesson text")
        new_xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8",
                                 standalone=True)
        if new_xml == before_xml:
            return document
        output = BytesIO()
        with ZipFile(output, "w") as dest:
            for info in source.infolist():
                dest.writestr(info, new_xml if info.filename == XML
                              else source.read(info.filename))
    return output.getvalue()
