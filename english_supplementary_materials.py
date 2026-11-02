"""Read-only registry for approved supplementary English lesson worksheets.

This module does not modify the lesson plan, database, or generation quotas.
A worksheet is offered only for the exact matching subject/year/lesson.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "supplementary_materials" / "english"

YEAR4 = {
    4: "Country and Nationality Writing Sheet",
    79: "The King of Kites — Story Response Sheet",
    89: "Famous Building Writing Planner",
    90: "Invitation Card Template",
}


def available(st):
    """Return existing, lesson-specific materials; never invent missing files."""
    if not isinstance(st, dict):
        return []
    if str(st.get("subject", "")).strip().casefold() not in ("english", "bahasa inggeris"):
        return []
    if str(st.get("year", "")).strip().casefold() not in ("4", "year 4", "tahun 4"):
        return []
    try:
        lesson = int(st.get("lesson_no") or st.get("textbook_lesson_no") or st.get("lesson"))
    except (ValueError, TypeError):
        return []
    title = YEAR4.get(lesson)
    if not title:
        return []
    path = ROOT / "year4" / ("lesson_%03d_worksheet.md" % lesson)
    if not path.is_file():
        return []
    return [{"lesson": lesson, "title": title, "path": str(path), "format": "markdown", "status": "supplementary"}]
