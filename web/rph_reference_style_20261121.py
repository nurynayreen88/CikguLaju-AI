"""Pastel RPH presentation for native 3-table Word downloads only.

Sains, DLP and PPKI are the approved visual references and are never changed.
This updates OOXML formatting in-place: it cannot change curriculum text,
teacher metadata, table structure, fonts, page dimensions or lesson content.
"""
from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOC = "word/document.xml"
PALETTES = {
    "bahasa melayu": "EAF1FB",
    "bm": "EAF1FB",
    "english": "E9F3F9",
    "bahasa inggeris": "E9F3F9",
    "matematik": "F0EBFA",
    "mathematics": "F0EBFA",
    "pendidikan islam": "F3F1DF",
    "sejarah": "F8EEDF",
    "pendidikan muzik": "EAF5EA",
    "muzik": "EAF5EA",
    "pendidikan jasmani dan pendidikan kesihatan": "E7F4EE",
    "pendidikan jasmani": "E7F4EE",
    "pjpk": "E7F4EE",
    "pendidikan moral": "F8EAF2",
    "moral": "F8EAF2",
    "pendidikan seni visual": "FCEFE8",
    "psv": "FCEFE8",
    "reka bentuk dan teknologi": "EDF0F7",
    "rbt": "EDF0F7",
}
REFERENCE = ("sains", "science", "ppki", "dlp")
TITLE_MARKERS = (
    "rancangan pengajaran harian",
    "daily lesson plan",
    "lesson plan",
    "خطة التدريس",
    "رنجنجن ڤڠاجرن",
)


def color_for_state(state):
    if not isinstance(state, dict) or str(state.get("task") or "").strip().casefold() != "rph":
        return None
    # Protect the three owner-approved references, including DLP Maths/Science.
    for key in ("subject", "curriculum_version", "curriculum", "stream", "programme", "program", "school_type"):
        value = str(state.get(key) or "").strip().casefold()
        if any(ref in value for ref in REFERENCE):
            return None
    subject = " ".join(str(state.get("subject") or "").strip().casefold().split())
    return PALETTES.get(subject)


def _node(parent, name, *, first=False):
    tag = W + name
    child = parent.find(tag)
    if child is None:
        child = etree.Element(tag)
        if first:
            parent.insert(0, child)
        else:
            parent.append(child)
    return child


def _shade_cell(cell, fill):
    props = _node(cell, "tcPr", first=True)
    shading = _node(props, "shd")
    shading.set(W + "val", "clear")
    shading.set(W + "fill", fill)
    borders = _node(props, "tcBorders")
    for edge in ("top", "bottom", "left", "right"):
        line = _node(borders, edge)
        line.set(W + "val", "single")
        line.set(W + "sz", "4")
        line.set(W + "color", "444444")


def _boxed_title(body, first_table, fill):
    for paragraph in body.findall(W + "p"):
        if paragraph.getparent() is not body:
            continue
        if body.index(paragraph) >= body.index(first_table):
            break
        visible = "".join(n.text or "" for n in paragraph.iter(W + "t")).strip().casefold()
        if not any(key in visible for key in TITLE_MARKERS):
            continue
        ppr = _node(paragraph, "pPr", first=True)
        shading = _node(ppr, "shd")
        shading.set(W + "val", "clear")
        shading.set(W + "fill", fill)
        borders = _node(ppr, "pBdr")
        for edge in ("top", "bottom", "left", "right"):
            line = _node(borders, edge)
            line.set(W + "val", "single")
            line.set(W + "sz", "6")
            line.set(W + "space", "5")
            line.set(W + "color", "444444")
        return True
    return False


def style_three_table_word_bytes(document, fill):
    """Return styled bytes; fail closed to original on unexpected table layout.

    In particular, no new table is inserted: native Web's 3-table contract,
    Sejarah compacting and all existing metadata indices remain valid.
    """
    if not isinstance(document, bytes) or not document.startswith(b"PK\x03\x04"):
        return document
    with ZipFile(BytesIO(document)) as source:
        if DOC not in source.namelist() or source.testzip():
            return document
        original_xml = source.read(DOC)
        root = etree.fromstring(original_xml)
        body = root.find(W + "body")
        if body is None:
            return document
        tables = body.findall(W + "tbl")
        if len(tables) != 3 or any(len(t.findall(W + "tr")) < 1 for t in tables):
            return document
        if any(len(row.findall(W + "tc")) != width
               for table, width in zip(tables, (2, 3, 2))
               for row in table.findall(W + "tr")):
            return document
        original_text = tuple(node.text for node in root.iter(W + "t"))
        _boxed_title(body, tables[0], fill)
        for index, table in enumerate(tables):
            for ri, row in enumerate(table.findall(W + "tr")):
                cells = row.findall(W + "tc")
                for ci, cell in enumerate(cells):
                    if ci == 0 or (index == 1 and ri == 0):
                        _shade_cell(cell, fill)
        if tuple(node.text for node in root.iter(W + "t")) != original_text:
            raise ValueError("RPH typography unexpectedly changed document text")
        updated_xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        if updated_xml == original_xml:
            return document
        output = BytesIO()
        with ZipFile(output, "w") as target:
            for info in source.infolist():
                target.writestr(info, updated_xml if info.filename == DOC else source.read(info.filename))
    return output.getvalue()


def style_word_path(path, fill):
    target = Path(path)
    if target.suffix.lower() != ".docx" or not target.is_file():
        return False
    original = target.read_bytes()
    updated = style_three_table_word_bytes(original, fill)
    if updated == original:
        return False
    temporary = target.with_name(target.name + ".style.tmp")
    try:
        temporary.write_bytes(updated)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return True


def install(runtime):
    """Install after existing subject-specific adapters, without touching PDF."""
    if getattr(runtime, "_CIKGULAJU_REFERENCE_WORD_STYLE_20261121", False):
        return True
    previous = getattr(runtime, "create_word_file", None)
    if not callable(previous):
        return False

    def premium_word(state, source_text, chat_id):
        path = previous(state, source_text, chat_id)
        fill = color_for_state(state)
        if fill is not None and isinstance(path, (str, os.PathLike)):
            try:
                style_word_path(path, fill)
            except (OSError, ValueError, etree.XMLSyntaxError) as exc:
                # Fail open to the unchanged original document, never block a
                # teacher's download because of a decorative formatting pass.
                print("RPH pastel presentation skipped:", type(exc).__name__, flush=True)
        return path

    runtime.create_word_file = premium_word
    runtime._CIKGULAJU_REFERENCE_WORD_STYLE_20261121 = True
    return True
