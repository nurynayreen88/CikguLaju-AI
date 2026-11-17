"""Online book references for English Lessons with no local PDF excerpt."""
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YEAR3_WORKBOOK_VIEW = "https://online.anyflip.com/rmzft/wwgq/mobile/index.html"
YEAR6_PUPIL_BOOK_VIEW = "https://online.anyflip.com/hykyg/rrpd/mobile/index.html"
# Printed pp.2–3 are leaves 3–4 in this copy. The local PDF skips them.
YEAR3_WELCOME_WORKBOOK_PAGES = {1: (2,), 2: (2,), 3: (3,), 6: (3,), 7: (3,)}


@lru_cache(maxsize=1)
def year6_sow_book_pages():
    path = ROOT / "rph_standalone/english/year6/sow_task_overlay_2027.json"
    overlay = json.loads(path.read_text(encoding="utf-8"))
    if overlay["version"] != "y6-sow-20261103":
        return {}
    result = {}
    for lesson, row in overlay["lessons"].items():
        source = row["sow_pupil_book_pages"].strip().rstrip(",")
        if not source:
            continue
        pages = set()
        for part in re.split(r"\s*[,&]\s*", source):
            span = re.fullmatch(r"(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?", part)
            if not span:
                raise ValueError("Unexpected Year 6 SOW book page reference")
            first, last = int(span[1]), int(span[2] or span[1])
            if not 4 <= first <= last <= 131:
                raise ValueError("Year 6 SOW reference outside the Pupil's Book")
            pages.update(range(first, last + 1))
        if len(pages) <= 4:
            result[int(lesson)] = sorted(pages)
    return result


def english_book_view_link(year, lessons, pdf_types):
    """Return an original-book viewer link only when its PDF is unavailable."""
    if year == 3 and "workbook" not in pdf_types:
        kind, label = "workbook", "Activity Book"
        page_map, url, offset = YEAR3_WELCOME_WORKBOOK_PAGES, YEAR3_WORKBOOK_VIEW, 1
    elif year == 6 and "textbook" not in pdf_types:
        kind, label = "textbook", "Pupil’s Book"
        page_map, url, offset = year6_sow_book_pages(), YEAR6_PUPIL_BOOK_VIEW, 0
    else:
        return None
    covered = [number for number in lessons if number in page_map]
    pages = sorted({page for number in covered for page in page_map[number]})
    if not pages:
        return None
    numbers = " + ".join(f"{number:03d}" for number in covered)
    page_label = ", ".join(map(str, pages))
    return {"type": kind, "title": f"{label} • Lesson {numbers} • m/s {page_label}",
            "url": f"{url}?pageIndex={pages[0] + offset}", "action": "Buka Buku Asal"}
