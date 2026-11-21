"""Restore complex-script bold in approved Pendidikan Islam v2 Word/PDF.

The 696 vetted source DOCX already have bold activity titles, but their
complex-script runs lack w:bCs. LibreOffice consequently embeds Amiri-Regular
instead of Amiri-Bold in the archived PDFs. This adapter adds only those
run-formatting properties. It cannot edit or reword lesson source text.
"""
from __future__ import annotations

from io import BytesIO
import re

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

MAIN_LABEL = "اکتيۏيتي اوتام"
ACTIVITY_TITLE = re.compile(r"^اکتيۏيتي [1-4]$")


def with_jawi_bold(word: bytes) -> tuple[bytes, int]:
    """Set complex-script bold on preexisting, bold Jawi activity headings."""
    if not isinstance(word, bytes) or not word.startswith(b"PK\x03\x04"):
        raise ValueError("Not a Word RPH")
    doc = Document(BytesIO(word))
    if len(doc.tables) != 3 or len(doc.tables[2].columns) != 2:
        raise ValueError("Unreviewed Pendidikan Islam template")
    main = doc.tables[2]
    if len(main.rows) != 6 or main.cell(1, 0).text.strip() != MAIN_LABEL:
        raise ValueError("Unreviewed Jawi activity grid")
    original = [tuple(p.text for p in cell.paragraphs)
                for table in doc.tables for row in table.rows for cell in row.cells]
    modified = 0
    for para in main.cell(1, 1).paragraphs:
        if not ACTIVITY_TITLE.fullmatch(para.text.strip()):
            continue
        if not para.runs or any(not run.bold for run in para.runs if run.text.strip()):
            raise ValueError("Source heading is not preapproved bold")
        for run in para.runs:
            if not run.text.strip():
                continue
            props = run._r.get_or_add_rPr()
            for name in ("bCs", "rtl"):
                node = props.find(qn("w:" + name))
                if node is None:
                    node = OxmlElement("w:" + name)
                    props.append(node)
                node.set(qn("w:val"), "1")
            fonts = props.find(qn("w:rFonts"))
            if fonts is None:
                fonts = OxmlElement("w:rFonts")
                props.insert(0, fonts)
            fonts.set(qn("w:cs"), "Amiri")
        modified += 1
    if not 1 <= modified <= 4:
        raise ValueError("No validated Jawi activity headings")
    after = [tuple(p.text for p in cell.paragraphs)
             for table in doc.tables for row in table.rows for cell in row.cells]
    if original != after:
        raise ValueError("Activity styling changed lesson text")
    out = BytesIO()
    doc.save(out)
    return out.getvalue(), modified


def pdf_is_reliable(candidate: bytes, original: bytes) -> bool:
    """Reject conversions missing Amiri-Bold or modifying document geometry."""
    try:
        import fitz
        with fitz.open(stream=candidate, filetype="pdf") as revised, \
             fitz.open(stream=original, filetype="pdf") as old:
            if len(revised) != len(old) or not revised or revised.is_encrypted:
                return False
            if any(abs(revised[i].rect.width - old[i].rect.width) > 1 or
                   abs(revised[i].rect.height - old[i].rect.height) > 1
                   for i in range(len(old))):
                return False
            return any("Amiri-Bold" in font[3]
                       for page in revised for font in page.get_fonts())
    except Exception:
        return False
