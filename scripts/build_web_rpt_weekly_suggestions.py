"""Extract weekly Lesson/PdP numbers from published RPT PDFs.

Run from the repository root with PyMuPDF installed. The Web uses the
generated JSON, so requests require no PDF parsing or additional dependencies.
"""
from collections import defaultdict
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re

import fitz


ROOT = Path("rpt_2027/web_2027_pdfs")
OUTPUT = Path("web/rpt_weekly_suggestions_2027.json")
SUBJECTS = {
    "bahasa_arab": "ARAB",
    "bahasa_melayu": "BM",
    "english": "ENGLISH",
    "matematik": "MATH",
    "muzik": "MUZIK",
    "pendidikan_islam": "PI",
    "pendidikan_moral": "MORAL",
    "pjpk": "PJPK",
    "psv": "PSV",
    "rbt": "RBT",
    "sains": "SCIENCE",
    "sejarah": "SEJARAH",
}
RTL_SUBJECTS = {"ARAB", "PI"}
WEEK = re.compile(r"\bM(\d{2})\b")
DATE = re.compile(r"\d{2}/\d{2}/2027")
LESSON = re.compile(r"(?:(PJ|PK) )?(?:Lesson|PdP) (\d{3})")


def read_weeks(path, subject):
    rtl = subject in RTL_SUBJECTS
    dates_by_week = {}
    lessons_by_week = defaultdict(lambda: defaultdict(list))
    seen = set()
    with fitz.open(path) as pdf:
        for page in list(pdf)[1:]:
            for drawing in page.get_drawings():
                rect = drawing["rect"]
                edge = rect.x1 if rtl else rect.x0
                if (drawing["type"] != "f" or abs(rect.width - 105) > 0.1
                        or abs(edge - (page.rect.width - 23 if rtl else 35)) > 0.1):
                    continue
                text = page.get_text(clip=rect)
                week = WEEK.search(text)
                printed_dates = DATE.findall(text)
                if not week or len(printed_dates) != 4:
                    raise ValueError(f"{path}, page {page.number + 1}: invalid week cell")
                n = int(week[1])
                dates = tuple(datetime.strptime(d, "%d/%m/%Y").date().isoformat()
                              for d in printed_dates)
                if dates_by_week.setdefault(n, dates) != dates:
                    raise ValueError(f"{path}: conflicting dates for week {n}")
                clip = fitz.Rect(510 if rtl else 140, rect.y0,
                                 rect.x0 if rtl else 300, rect.y1)
                for block in page.get_text("dict", clip=clip)["blocks"]:
                    for line in block.get("lines", ()):
                        for span in line["spans"]:
                            match = LESSON.fullmatch(span["text"].strip())
                            if match is None or abs(span["size"] - 8.1) > 0.05:
                                continue
                            component, number = match[1] or "", int(match[2])
                            identity = (component, number)
                            if identity in seen or (subject == "PJPK") != bool(component):
                                raise ValueError(f"{path}: invalid or repeated PdP {identity}")
                            seen.add(identity)
                            lessons_by_week[n][component].append(number)
    for component in {component for component, _ in seen}:
        numbers = [number for n in sorted(lessons_by_week)
                   for number in lessons_by_week[n].get(component, ())]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError(f"{path}: non-contiguous sequence for {component}")
    if dates_by_week.keys() != lessons_by_week.keys():
        raise ValueError(f"{path}: week without a numbered lesson")
    return dates_by_week, lessons_by_week


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    catalog = {}
    for key, entry in manifest["files"].items():
        subject, year = key.split(":")
        code = SUBJECTS[subject]
        path = ROOT / entry["path"]
        if sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"{path} differs from the Web RPT manifest")
        dates, lessons = read_weeks(path, code)
        if not lessons:
            raise ValueError(f"{path}: no weekly lessons found")
        catalog[f"{code}:{year}"] = {
            str(week): [*dates[week], lessons[week]]
            for week in sorted(lessons)
        }
    OUTPUT.write_text("{\n" + ",\n".join(
        json.dumps(key) + ":" + json.dumps(weeks, separators=(",", ":"))
        for key, weeks in sorted(catalog.items())
    ) + "\n}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
