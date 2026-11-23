"""Render-only Jawi numerals for verified active Pendidikan Islam RPH.

Replace European 0-9 with Arabic-Indic ٠-٩ on displayed lesson strings.
This is deliberately not a database migration, SK/SP code rewrite, route ID
rewrite, or change to lesson selections. Only active PI RPH Word/PDF output
uses this adapter. Existing Jawi digits and text are left intact.
"""
from __future__ import annotations

from copy import copy
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import os
import re

from lxml import etree

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOCUMENT = "word/document.xml"
DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
# A URL/email is a reference, not a printed lesson number. Keep its identity.
LINK = re.compile(r"https?://[^\s<>]+|www\.[^\s<>]+|[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I)
SPECIAL = ("ppki", "dlp", "sjkc", "sjkt", "kp2027")


def is_active_pi_rph(state):
    if not isinstance(state, dict):
        return False
    if (str(state.get("task") or "").strip().casefold() != "rph"
            or str(state.get("subject") or "").strip().casefold() != "pendidikan islam"):
        return False
    for key in ("curriculum", "curriculum_version", "stream",
                "programme", "program", "school_type"):
        if any(marker in str(state.get(key) or "").casefold() for marker in SPECIAL):
            return False
    return True


def jawi_display_digits(text):
    """Convert only printed decimal glyphs; preserve URL/email substrings."""
    if not isinstance(text, str) or not any("0" <= x <= "9" for x in text):
        return text
    pieces = []
    previous = 0
    for found in LINK.finditer(text):
        pieces.append(text[previous:found.start()].translate(DIGITS))
        pieces.append(found.group(0))
        previous = found.end()
    pieces.append(text[previous:].translate(DIGITS))
    return "".join(pieces)


def display_pi_rows(state, rows):
    """Copy formatted rows, never edit the returned source dict in place."""
    if not is_active_pi_rph(state) or not isinstance(rows, dict):
        return rows
    rendered = {
        name: jawi_display_digits(value) if isinstance(value, str) else value
        for name, value in rows.items()
    }
    return rendered if rendered != rows else rows


def _text(parent):
    return "".join(n.text or "" for n in parent.iter(W + "t"))


def jawi_word_display_digits(original):
    """Update only w:t glyphs in a confirmed 4-table active Jawi Word file.

    All OOXML relationships, images, styles, hyperlinks, source fields and
    package members are preserved. Unsupported/uncertain layouts fail closed.
    """
    if not isinstance(original, bytes) or not original.startswith(b"PK\x03\x04"):
        return original
    try:
        with ZipFile(BytesIO(original)) as src:
            names = src.namelist()
            if DOCUMENT not in names or src.testzip() is not None:
                return original
            root = etree.fromstring(src.read(DOCUMENT))
            body = root.find(W + "body")
            if body is None:
                return original
            tables = body.findall(W + "tbl")
            if len(tables) != 4:
                return original
            title = next((
                p for p in body.findall(W + "p")
                if body.index(p) < body.index(tables[0])
                and _text(p).strip() == "رنچڠن ڤڠاجرن هارين"
            ), None)
            if title is None:
                return original
            if any(t.find(W + "tblPr/" + W + "bidiVisual") is None for t in tables):
                return original
            first = tables[0].findall(W + "tr")
            if len(first) != 1:
                return original
            cols = first[0].findall(W + "tc")
            if (len(cols) != 2 or "ڤنديديقن اسلام" not in _text(cols[0])
                    or "کلس" not in _text(cols[1])):
                return original
            if any(len(row.findall(W + "tc")) != n
                   for table, n in zip(tables[1:], (2, 3, 2))
                   for row in table.findall(W + "tr")):
                return original
            replacements = 0
            for node in root.iter(W + "t"):
                # Preserve clickable hyperlink destinations and text verbatim.
                if any(ancestor.tag == W + "hyperlink" for ancestor in node.iterancestors()):
                    continue
                original_text = node.text or ""
                revised_text = jawi_display_digits(original_text)
                if revised_text != original_text:
                    node.text = revised_text
                    replacements += 1
            if replacements == 0:
                return original
            updated_xml = etree.tostring(
                root, encoding="UTF-8", xml_declaration=True, standalone=True
            )
            result = BytesIO()
            with ZipFile(result, "w") as out:
                for item in src.infolist():
                    out.writestr(copy(item), updated_xml if item.filename == DOCUMENT
                                 else src.read(item.filename))
            output = result.getvalue()
            with ZipFile(BytesIO(output)) as checked:
                if (checked.namelist() != names
                        or checked.testzip() is not None
                        or any(checked.read(n) != src.read(n)
                               for n in names if n != DOCUMENT)):
                    return original
                # Idempotence and source text content are checked at the w:t
                # boundary: only the approved digit mapping may differ.
                modified = etree.fromstring(checked.read(DOCUMENT))
                old_nodes = list(etree.fromstring(src.read(DOCUMENT)).iter(W + "t"))
                new_nodes = list(modified.iter(W + "t"))
                if (len(old_nodes) != len(new_nodes)
                        or any(new.text != (
                            old.text if any(a.tag == W+"hyperlink" for a in old.iterancestors())
                            else jawi_display_digits(old.text)
                        ) for old, new in zip(old_nodes, new_nodes))):
                    return original
            return output
    except (OSError, ValueError, TypeError, BadZipFile, etree.XMLSyntaxError):
        return original


def install(runtime):
    """Install after final PI rows and Word decorators, for both outputs."""
    if getattr(runtime, "_CIKGULAJU_PI_JAWI_NUMERALS_20261124", False):
        return False
    previous_rows = getattr(runtime, "_rph_rows", None)
    previous_word = getattr(runtime, "create_word_file", None)
    if not callable(previous_rows) or not callable(previous_word):
        return False

    def pi_jawi_rows(state, source_text):
        return display_pi_rows(state, previous_rows(state, source_text))

    def pi_jawi_word(state, source_text, chat_id):
        path = previous_word(state, source_text, chat_id)
        if is_active_pi_rph(state) and isinstance(path, (str, os.PathLike)):
            target = Path(path)
            if target.suffix.lower() == ".docx" and target.is_file():
                try:
                    original = target.read_bytes()
                    changed = jawi_word_display_digits(original)
                    if changed != original:
                        tmp = target.with_name(target.name + ".jawi-digits.tmp")
                        try:
                            tmp.write_bytes(changed)
                            os.replace(tmp, target)
                        finally:
                            tmp.unlink(missing_ok=True)
                except OSError as exc:
                    print("PI Jawi numeral display skipped:",
                          type(exc).__name__, flush=True)
        return path

    runtime._rph_rows = pi_jawi_rows
    runtime.create_word_file = pi_jawi_word
    runtime._CIKGULAJU_PI_JAWI_NUMERALS_20261124 = True
    return True
