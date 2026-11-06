"""Fail-closed BA evidence formatter for Mathematics staging ONLY.

Not imported by app.py, Telegram, or Web. It does not alter RPH text or DB.
"""
from __future__ import annotations
import re

_PAGE_RE = re.compile(r"^[1-9][0-9]{0,2}(?:-[1-9][0-9]{0,2})?$")
_ACTIVITY_RE = re.compile(r"^Aktiviti [1-9][0-9]{0,2}(?:-[1-9][0-9]{0,2})?$", re.I)


def verified_ba_reference(record: dict[str, str]) -> str | None:
    """Return a BA citation ONLY on evidence-complete manual approval.

    'Legacy v27' candidates and the unreviewed v41 ledger must return None.
    The caller must separately review the one-page A4 layout before insertion.
    """
    if record.get("approval") != "APPROVED":
        return None
    if any(record.get(k) != "YES" for k in (
        "bt_sp_semantic_check", "visual_page_check", "source_edition_check"
    )):
        return None
    for key in ("year", "v41_lesson_id", "ba_exact_page", "ba_activity_ref",
                "ba_source_key", "reviewer", "evidence_note"):
        if not str(record.get(key, "")).strip():
            return None
    try:
        year = int(record["year"])
    except (ValueError, TypeError):
        return None
    if year not in (2, 3, 4, 5, 6):
        return None
    lesson = record["v41_lesson_id"]
    if not re.fullmatch(rf"T{year}-L[0-9]{{3}}", lesson):
        return None
    pages = record["ba_exact_page"]
    if not _PAGE_RE.fullmatch(pages):
        return None
    a, *rest = map(int, pages.split("-"))
    if rest and rest[0] < a:
        return None
    activity = record["ba_activity_ref"]
    if not _ACTIVITY_RE.fullmatch(activity):
        return None
    return f"Buku Aktiviti Matematik Tahun {year}, hlm. {pages}, {activity}."


__all__ = ["verified_ba_reference"]
