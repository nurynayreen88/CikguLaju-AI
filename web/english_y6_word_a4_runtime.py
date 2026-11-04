"""Year 6 English Word-only A4 compact layout, installed after existing RPH generator.

No curriculum DB access, Telegram network call, quota handling or PDF changes.
The current live Word generator first writes the whole RPH; the adapter then
compacts its layout, atomically replacing the file only if saving succeeded.
"""
from pathlib import Path
import os
import re
import tempfile

from docx import Document
from docx.shared import Cm, Pt
from docx.oxml.ns import qn


def _is_year6_english_rph(state):
    if not isinstance(state, dict):
        return False
    if str(state.get("task") or "").strip().casefold() != "rph":
        return False
    subject = re.sub(r"[^a-z]", "", str(state.get("subject") or "").casefold())
    if subject not in ("english", "bahasainggeris", "bi"):
        return False
    year = str(state.get("year") or state.get("year_label") or "").strip().casefold()
    return year in ("6", "tahun 6", "year 6", "primary year 6", "y6", "tahun 6 (sk)")


def compact_word_file(path, *, point_size=8.0):
    """Apply tested text-preserving A4 spacing; never cut or replace lesson text.

    Returns True only after atomic replacement, False on any invalid input.
    The original file is unchanged if the new document cannot be saved.
    """
    try:
        source = Path(path)
    except (TypeError, ValueError):
        return False
    if not source.is_file() or source.suffix.casefold() != ".docx":
        return False
    if type(point_size) not in (int, float) or not 7.2 <= point_size <= 8.5:
        return False

    temporary = None
    try:
        doc = Document(str(source))
        for section in doc.sections:
            section.top_margin = Cm(0.52)
            section.bottom_margin = Cm(0.52)
            section.left_margin = Cm(0.95)
            section.right_margin = Cm(0.95)
            section.footer_distance = Cm(0.25)
        normal = doc.styles["Normal"]
        normal.font.size = Pt(point_size)
        normal.paragraph_format.line_spacing = 0.95
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    props = cell._tc.get_or_add_tcPr()
                    margins = props.find(qn("w:tcMar"))
                    if margins is not None:
                        for side in ("top", "bottom", "left", "right"):
                            node = margins.find(qn("w:" + side))
                            if node is not None:
                                node.set(qn("w:w"), "7" if side in ("top", "bottom") else "42")
                    for paragraph in cell.paragraphs:
                        paragraph.paragraph_format.space_before = Pt(0)
                        paragraph.paragraph_format.space_after = Pt(0)
                        paragraph.paragraph_format.line_spacing = 0.95
                        for run in paragraph.runs:
                            run.font.size = Pt(point_size)
        with tempfile.NamedTemporaryFile(
            prefix="cikgulaju_y6_word_a4_", suffix=".docx",
            dir=str(source.parent), delete=False
        ) as file:
            temporary = Path(file.name)
        doc.save(str(temporary))
        os.replace(str(temporary), str(source))
        return True
    except (OSError, ValueError, TypeError, KeyError, Exception) as exc:
        # The original document is preserved and can still be delivered.
        print("English Y6 Word A4 layout fallback:", repr(exc), flush=True)
        return False
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _lesson16_choice(state):
    """Only Year6 SOW teacher-choice Lesson 16 needs the 7.5pt A4 variant."""
    if not _is_year6_english_rph(state):
        return False
    value = state.get("lesson_no") or state.get("textbook_lesson_no") or state.get("lesson")
    if isinstance(value, bool):
        return False
    value = str(value or "").strip()
    return value.isascii() and value.isdecimal() and int(value) == 16


def install(runtime):
    """Wrap only create_word_file for English Year 6 RPH, no other paths."""
    if getattr(runtime, "CIKGULAJU_ENGLISH_Y6_WORD_A4_ACTIVE", False):
        return True
    previous = getattr(runtime, "create_word_file", None)
    if not callable(previous):
        return False

    def year6_word(state, *args, **kwargs):
        original = previous(state, *args, **kwargs)
        if _is_year6_english_rph(state):
            # All other 159 Lessons retain their original tested 8pt style.
            # Choice Lesson 16 is the sole 8pt layout overflow in the latest
            # AST-locked Word/PDF A4 audit; 7.5pt applies ONLY here.
            compact_word_file(original, point_size=7.5 if _lesson16_choice(state) else 8.0)
        return original

    runtime.create_word_file = year6_word
    runtime.CIKGULAJU_ENGLISH_Y6_WORD_A4_ACTIVE = True
    return True
