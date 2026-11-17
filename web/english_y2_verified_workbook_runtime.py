"""Opt-in bridge from verified Year 2–4 Workbook mapping to existing Telegram material UI.

Installs only on the WSGI runtime. Other subjects, years, and material types
retain the original handlers. No database mutation or Telegram side effects.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PARTS = {
    3: ((1, 80, 'y3_workbook_001_080.pdf'), (81, 96, 'y3_workbook_081_096.pdf')),
    4: ((2, 60, 'y4_workbook_002_060.pdf'), (61, 110, 'y4_workbook_061_110.pdf')),
}


def _local_pages_exist(year, start, end):
    return all(any(a <= p <= b and (_REPO_ROOT / 'books' / 'english' / name).is_file()
                   for a, b, name in _PARTS[year]) for p in range(start, end + 1))

from resources.english.y2.workbook_download_router import resolve_lesson
from resources.english.y3.workbook_verified_map import Y3_WB_VERIFIED_LESSON_MAP, Y3_WB_WELCOME_PART
from resources.english.y4.workbook_verified_map import EN4_WB_VERIFIED
from web.telegram_english_workbook_api_20261106 import _extract, _material


def install(runtime):
    available = getattr(runtime, "_available_materials_v2528", None)
    pages = getattr(runtime, "_en_book_pages_v25232", None)
    year_number = getattr(runtime, "_english_primary_year_number_v2517", None)
    if not all(callable(f) for f in (available, pages, year_number)):
        return False

    def selection(ss):
        if not isinstance(ss, dict):
            return None
        year = year_number(ss.get("year"))
        if year not in (2, 3, 4):
            return None
        if str(ss.get("subject") or "").strip().casefold() not in ("english", "bahasa inggeris"):
            return None
        lesson = ss.get("lesson_no") or ss.get("textbook_lesson_no") or ss.get("lesson")
        try:
            return year, int(lesson)
        except (TypeError, ValueError):
            return None

    def welcome_lesson(ss):
        selected = selection(ss)
        if selected and selected[0] == 3:
            lesson = selected[1]
            if Y3_WB_VERIFIED_LESSON_MAP.get(lesson, {}).get("part") == Y3_WB_WELCOME_PART:
                return lesson
        return None

    def verified(ss):
        selected = selection(ss)
        if not selected:
            return None
        year, number = selected
        if year == 2:
            return resolve_lesson(number)
        row = (Y3_WB_VERIFIED_LESSON_MAP if year == 3 else EN4_WB_VERIFIED).get(number)
        if not isinstance(row, dict) or row.get("part") or not isinstance(row.get("pdf"), int):
            return None
        p = row["pdf"]
        return {"source_page_start": p, "source_page_end": p} if _local_pages_exist(year, p, p) else None

    def available_with_verified_workbook(ss):
        items = list(available(ss) or [])
        lesson = welcome_lesson(ss)
        if lesson is not None and _material(3, lesson, root=_REPO_ROOT) is None:
            return [item for item in items if item != "activity"]
        if (lesson is not None or verified(ss) is not None) and "activity" not in items:
            items.append("activity")
        return items

    def pages_with_verified_workbook(ss, key):
        if key == "activity":
            item = verified(ss)
            if item is not None:
                return list(range(item["source_page_start"], item["source_page_end"] + 1))
        return pages(ss, key)

    def workbook_sender(send_before):
        def send(cid, ss, key, *args, **kwargs):
            lesson = welcome_lesson(ss) if key == "activity" else None
            if lesson is None:
                return send_before(cid, ss, key, *args, **kwargs)
            material = _material(3, lesson, root=_REPO_ROOT)
            if material is None:
                return False
            try:
                with TemporaryDirectory(prefix="cikgulaju-workbook-") as folder:
                    path = Path(folder) / f"English_Y3_Lesson_{lesson:03d}_Workbook.pdf"
                    path.write_bytes(_extract(material))
                    sent = runtime._send_document_before_v25277(cid, str(path), material["label"])
            except (OSError, ValueError):
                return False
            return runtime._telegram_delivery_ok_v25279(sent)
        return send

    runtime._available_materials_v2528 = available_with_verified_workbook
    runtime._en_book_pages_v25232 = pages_with_verified_workbook
    for name in ("_send_reference_material_v2528", "_send_reference_material"):
        send_before = getattr(runtime, name, None)
        if callable(send_before):
            setattr(runtime, name, workbook_sender(send_before))
    return True
