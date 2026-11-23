"""CikguLaju shared RPH presentation entrance (non-destructive transition).

One stable generator API for source-specific adapters. The source remains the
authority for SK/SP, content, activity/teacher instructions and reflection.

The format contract belongs here, not in each subject. The underlying Word
and PDF builders remain compatible while existing subject families are
migrated independently; do not guess Jawi/Arabic or source schema.
"""
from __future__ import annotations

from io import BytesIO
from typing import Literal

# Owner-approved BM SK KP2027 Tahun 1 visual contract.
# All families use the SAME neutral small teacher panel; different pastel
# palettes and native grid widths remain unchanged until their route is audited.
TEACHER_PANEL_FILL = "F5F7FA"
MASTER_NAME = "BM_SK_KP2027_T1"
HEADER_PANELS = {"ltr": ("identity", "teacher"), "rtl": ("teacher", "identity")}

# Only verified structured RPH adapters are enabled. Other families must be
# audited one by one, not silently converted into DLP/PPKI structures.
STRUCTURED_SOURCES = frozenset(("dlp", "ppki"))


def render_structured_rph(*, source: Literal["dlp", "ppki"],
                          fmt: Literal["word", "docx", "pdf"],
                          heading, details, activities, footer,
                          compact=False, mathematics=False,
                          teacher=None, label_fill=None) -> bytes:
    """Build source-approved four-box RPH Word/PDF via ONE common entry point.

    The source adapter sends the exact existing four payloads; no extra rows,
    default objectives, reflection text or imagined curriculum metadata are
    added here. The existing tested builder owns typography and RTL protection.
    """
    if source not in STRUCTURED_SOURCES:
        raise ValueError("RPH source is not yet verified for unified rendering")
    if fmt not in ("word", "docx", "pdf"):
        raise ValueError("Unsupported RPH format")
    if not isinstance(heading, (list, tuple)) or len(heading) != 3:
        raise ValueError("RPH heading must already come from its source")
    if not all(isinstance(rows, (list, tuple)) for rows in
               (details, activities, footer)):
        raise ValueError("Missing source-backed RPH rows")
    if source == "ppki" and mathematics:
        raise ValueError("PPKI cannot use the DLP Mathematics adapter")
    # Delayed import keeps the existing DLP public API and all its source
    # parsers unchanged; no circular import when dlp_year2_rph calls us.
    from dlp_year2_rph import _word, _pdf

    buffer = BytesIO()
    builder = _pdf if fmt == "pdf" else _word
    builder(buffer, heading, details, activities, footer,
            compact=compact, mathematics=mathematics, teacher=teacher,
            label_fill=label_fill)
    data = buffer.getvalue()
    if not data.startswith(b"%PDF-" if fmt == "pdf" else b"PK\x03\x04"):
        raise ValueError("Generated RPH file has an invalid signature")
    return data
