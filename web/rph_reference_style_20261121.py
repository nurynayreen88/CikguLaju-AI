"""Pastel RPH presentation for native 3-table Word downloads only.

DLP and PPKI retain their independent approved renderers. Native KSSR Sains
uses the same source-preserving header alignment as other SK subjects.
This updates OOXML formatting in-place: it cannot change curriculum text,
teacher metadata, table structure, fonts, page dimensions or lesson content.
"""
from __future__ import annotations

from io import BytesIO
from collections import Counter
from copy import deepcopy
import re
import os
from pathlib import Path
from zipfile import BadZipFile, ZipFile

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
    "sains": "E7F3EA",
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
REFERENCE = ("science", "ppki", "dlp")
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
    # Protect DLP/PPKI and English-language Science; native SK Sains
    # receives a pastel/two-panel header only when its actual 3-table
    # source contract passes all existing source-text guards.
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
    borders = _node(props, "tcBorders")
    for edge in ("top", "bottom", "left", "right"):
        line = _node(borders, edge)
        line.set(W + "val", "single")
        line.set(W + "sz", "4")
        line.set(W + "color", "444444")
    shading = _node(props, "shd")
    shading.set(W + "val", "clear")
    shading.set(W + "fill", fill)


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
        borders = _node(ppr, "pBdr")
        for edge in ("top", "bottom", "left", "right"):
            line = _node(borders, edge)
            line.set(W + "val", "single")
            line.set(W + "sz", "6")
            line.set(W + "space", "5")
            line.set(W + "color", "444444")
        shading = _node(ppr, "shd")
        shading.set(W + "val", "clear")
        shading.set(W + "fill", fill)
        return True
    return False


_ACTIVITY_TITLE = re.compile(
    r"^(?:Aktiviti|Activity)\s+[1-9]\d?"
    r"(?:\s*[.:)–—-]\s*\S.{0,109})?$",
    re.IGNORECASE,
)


def _is_standalone_activity_title(value):
    if not _ACTIVITY_TITLE.fullmatch(value):
        return False
    remainder = re.sub(
        r"^(?:Aktiviti|Activity)\s+[1-9]\d?\s*[.:)–—-]\s*",
        "", value, flags=re.IGNORECASE,
    )
    # Full teacher/pupil instructions are NEVER treated as bold titles.
    if remainder != value and (
        re.match(r"^(?:Guru|Murid|Teacher|Pupils|Students)\b",
                 remainder, re.IGNORECASE)
        or remainder.endswith((".", "!", "?"))
    ):
        return False
    return True


def _bold_separate_activity_titles(table):
    """Bold only existing numbered title LINES in the native main-activity cell.

    Preserves every original OOXML w:t text node, line break and source run
    font. Nothing is inserted into curricula or other table cells. A title
    embedded inside an instruction paragraph is not guessed or rewritten.
    """
    changed = False
    for row in table.findall(W + "tr"):
        cells = row.findall(W + "tc")
        if len(cells) != 3:
            continue
        phase = " ".join(
            "".join(node.text or "" for node in cells[0].iter(W + "t"))
            .casefold().split()
        )
        if phase not in ("aktiviti utama", "main activities"):
            continue
        for para in cells[1].findall(W + "p"):
            # Complex fields/hyperlinks are deliberately untouched.
            if any(child.tag not in (W + "pPr", W + "r") for child in para):
                continue
            runs = para.findall(W + "r")
            if not runs or any(
                item.tag not in (W + "rPr", W + "t", W + "br")
                for run in runs for item in run
            ):
                continue
            lines = [[]]
            for run in runs:
                props = run.find(W + "rPr")
                for item in run:
                    if item.tag == W + "rPr":
                        continue
                    lines[-1].append((props, item))
                    if item.tag == W + "br":
                        lines.append([])
            titles = [
                i for i, line in enumerate(lines)
                if i < len(lines) - 1
                and _is_standalone_activity_title(
                    "".join(item.text or "" for _, item in line
                            if item.tag == W + "t").strip()
                )
            ]
            if not titles:
                continue
            original_text = tuple(t.text for t in para.iter(W + "t"))
            original_breaks = len(tuple(para.iter(W + "br")))
            # Rebuild only these simple runs, keeping the exact original w:t
            # nodes and all w:br nodes in order, with copied original rPr.
            for run in runs:
                para.remove(run)
            for i, line in enumerate(lines):
                for props, item in line:
                    run = etree.Element(W + "r")
                    if props is not None:
                        run.append(deepcopy(props))
                    if i in titles and item.tag == W + "t":
                        bold = _node(_node(run, "rPr", first=True), "b")
                        bold.set(W + "val", "1")
                    run.append(item)
                    para.append(run)
            assert tuple(t.text for t in para.iter(W + "t")) == original_text
            assert len(tuple(para.iter(W + "br"))) == original_breaks
            changed = True
    return changed


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
        _bold_separate_activity_titles(tables[1])
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



def _preserves_source_content(original, styled):
    """Fail closed unless every source text token and untouched DOCX part survives.

    The approved premium header deliberately relocates text into a new banner,
    so compare the *multiset* of exact OOXML tokens, not their position. This
    is a final safety gate after all presentation-only transforms, including
    future optional ones. No source Word file or DB record is rewritten.
    """
    if not (isinstance(original, bytes) and isinstance(styled, bytes)):
        return False
    if not (original.startswith(b"PK\x03\x04") and styled.startswith(b"PK\x03\x04")):
        return False
    try:
        with ZipFile(BytesIO(original)) as before, ZipFile(BytesIO(styled)) as after:
            names = before.namelist()
            if (DOC not in names or names != after.namelist()
                    or before.testzip() is not None or after.testzip() is not None):
                return False
            if any(before.read(name) != after.read(name)
                   for name in names if name != DOC):
                return False
            a = etree.fromstring(before.read(DOC))
            b = etree.fromstring(after.read(DOC))
    except (OSError, ValueError, BadZipFile, etree.XMLSyntaxError):
        return False
    protected = {
        W + "t", W + "instrText", W + "delText", W + "delInstrText",
        "{http://schemas.openxmlformats.org/drawingml/2006/main}t",
    }
    def tokens(root):
        return Counter((node.tag, node.text or "")
                       for node in root.iter() if node.tag in protected)
    return tokens(a) == tokens(b)



def style_word_path(path, fill, *, premium_header=False, rtl_jawi=False):
    target = Path(path)
    if target.suffix.lower() != ".docx" or not target.is_file():
        return False
    original = target.read_bytes()
    updated = style_three_table_word_bytes(original, fill)
    if premium_header:
        from web.rph_premium_header_20261121 import premium_header_bytes
        updated = premium_header_bytes(updated, fill, rtl_jawi=rtl_jawi)
        from web.rph_equal_width_20261121 import equal_width_four_table_bytes
        updated = equal_width_four_table_bytes(updated, rtl_jawi=rtl_jawi)
        if rtl_jawi:
            # Only active source-backed PI native Word, never PI 696 archives:
            # four verified RTL tables, standalone source title and fixed Jawi
            # identity must be present before any paragraph justification.
            from web.rph_active_pi_rtl_alignment_20261123 import align_active_pi_rtl_value_bytes
            updated = align_active_pi_rtl_value_bytes(updated)
    if updated == original:
        return False
    if not _preserves_source_content(original, updated):
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
                subject = str(state.get("subject") or "").strip().casefold()
                # PI Word may upgrade only if the exact native Jawi labels
                # and four-part grid match. Any mismatch preserves the
                # original source; Arabic has a separate approved renderer.
                style_word_path(path, fill,
                                premium_header=subject != "bahasa arab",
                                rtl_jawi=subject == "pendidikan islam")
            except (OSError, ValueError, etree.XMLSyntaxError) as exc:
                # Fail open to the unchanged original document, never block a
                # teacher's download because of a decorative formatting pass.
                print("RPH pastel presentation skipped:", type(exc).__name__, flush=True)
        return path

    runtime.create_word_file = premium_word
    runtime._CIKGULAJU_REFERENCE_WORD_STYLE_20261121 = True
    return True
