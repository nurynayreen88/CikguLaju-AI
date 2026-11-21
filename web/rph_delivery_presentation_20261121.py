"""Source-preserving final Web delivery of owner-approved RPH presentation.

Only ordinary LTR subjects use the original reviewed, fail-closed OOXML/PDF
adapters. Jawi, Arabic, Sains, DLP and PPKI retain their native or archived
subject-specific RTL/template formats. This module never edits the curriculum,
account data, permissions, or generation quota.
"""
from __future__ import annotations

from collections import Counter
from io import BytesIO
from zipfile import ZipFile

ORDINARY = {
    "BM": "Bahasa Melayu",
    "ENGLISH": "English",
    "MATH": "Matematik",
    "MATH_DPK3": "Matematik",
    "MORAL": "Pendidikan Moral",
    "PJPK": "PJPK",
    "PSV": "Pendidikan Seni Visual",
    "SEJARAH": "Sejarah",
    "RBT": "Reka Bentuk dan Teknologi",
    "MUZIK": "Pendidikan Muzik",
}
DOC = "word/document.xml"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _word_tokens(blob):
    from lxml import etree
    with ZipFile(BytesIO(blob)) as package:
        if package.testzip() is not None:
            raise ValueError("Invalid Word package")
        document = etree.fromstring(package.read(DOC))
        return Counter(node.text or "" for node in document.iter(W + "t"))


def presentation_for_web(selected, fmt, document):
    """Style delivered bytes only; keep the real document on any mismatch.

    No source lesson text is removed, reconstructed, reworded or relabeled.
    A layout absent from the reviewed three-table contract is left untouched.
    """
    if not isinstance(selected, dict) or not isinstance(document, BytesIO):
        return document
    subject = selected.get("subject")
    if subject not in ORDINARY or fmt not in ("word", "pdf"):
        return document
    original = document.getvalue()
    if not original or len(original) > 15 * 1024 * 1024:
        return document
    try:
        from web.rph_reference_style_20261121 import (
            color_for_state, style_three_table_word_bytes,
        )
        state = {"task": "rph", "subject": ORDINARY[subject]}
        fill = color_for_state(state)
        if not fill:
            return document
        if fmt == "word":
            from web.rph_premium_header_20261121 import premium_header_bytes
            from web.rph_equal_width_20261121 import equal_width_four_table_bytes
            updated = style_three_table_word_bytes(original, fill)
            updated = premium_header_bytes(updated, fill)
            updated = equal_width_four_table_bytes(updated)
            if updated != original and _word_tokens(original) != _word_tokens(updated):
                raise ValueError("Academic text changed by style adapter")
        else:
            from web.rph_reference_pdf_style_20261121 import style_pdf_bytes
            updated = style_pdf_bytes(original, fill)
        if not updated or updated == original or len(updated) > 15 * 1024 * 1024:
            return document
        return BytesIO(updated)
    except Exception:
        # The approved source document must never be lost for a visual change.
        return document
