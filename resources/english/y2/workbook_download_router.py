"""Verified English Year 2 Workbook PDF-part lookup.

Returns an existing repository PDF part for a verified lesson. The caller must
still send the file to Telegram; this module does not imply a delivery succeeded.
No guess is made for unverified or non-textbook lessons.
"""
from pathlib import Path

from .workbook_verified_map import Y2_WB_VERIFIED_LESSON_MAP

PDF_PARTS = (
    (1, 40, "books/english/y12_workbook_001_040.pdf"),
    (41, 80, "books/english/y12_workbook_041_080.pdf"),
    (81, 120, "books/english/y12_workbook_081_120.pdf"),
    (121, 129, "books/english/y12_workbook_121_129.pdf"),
)


def resolve_lesson(lesson, root=None):
    """Return PDF part and pages for a verified lesson, else None.

    Page numbers in the verified Year 2 mapping are used as source-PDF
    coordinates only where the verified map says so. A PDF part is returned,
    not an extracted page or proof that the page is the printed page.
    """
    if isinstance(lesson, bool):
        return None
    try:
        lesson_no = int(lesson)
    except (ValueError, TypeError):
        return None
    pages = Y2_WB_VERIFIED_LESSON_MAP.get(lesson_no)
    if not pages:
        return None
    first, last = pages
    matches = [
        (start, end, path)
        for start, end, path in PDF_PARTS
        if start <= first <= last <= end
    ]
    if len(matches) != 1:
        return None
    start, _, relative_path = matches[0]
    base = Path(root) if root is not None else Path(__file__).resolve().parents[3]
    full_path = base / relative_path
    if not full_path.is_file():
        return None
    return {
        "path": str(full_path),
        "relative_path": relative_path,
        "source_page_start": first,
        "source_page_end": last,
        "part_page_start": first - start + 1,
        "part_page_end": last - start + 1,
    }
