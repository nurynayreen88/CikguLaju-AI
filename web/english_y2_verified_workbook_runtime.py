"""Opt-in bridge from verified Year 2 Workbook mapping to existing Telegram material UI.

Installs only on the WSGI runtime. Other subjects, years, and material types
retain the original handlers. No database mutation or Telegram side effects.
"""
from pathlib import Path

from resources.english.y2.workbook_download_router import resolve_lesson


def install(runtime):
    available = getattr(runtime, "_available_materials_v2528", None)
    pages = getattr(runtime, "_en_book_pages_v25232", None)
    year_number = getattr(runtime, "_english_primary_year_number_v2517", None)
    if not all(callable(f) for f in (available, pages, year_number)):
        return False

    def verified(ss):
        if not isinstance(ss, dict):
            return None
        if year_number(ss.get("year")) != 2:
            return None
        if str(ss.get("subject") or "").strip().casefold() not in ("english", "bahasa inggeris"):
            return None
        lesson = ss.get("lesson_no") or ss.get("textbook_lesson_no") or ss.get("lesson")
        return resolve_lesson(lesson)

    def available_with_verified_workbook(ss):
        items = list(available(ss) or [])
        if verified(ss) is not None and "activity" not in items:
            items.append("activity")
        return items

    def pages_with_verified_workbook(ss, key):
        if key == "activity":
            item = verified(ss)
            if item is not None:
                return list(range(item["source_page_start"], item["source_page_end"] + 1))
        return pages(ss, key)

    runtime._available_materials_v2528 = available_with_verified_workbook
    runtime._en_book_pages_v25232 = pages_with_verified_workbook
    return True
