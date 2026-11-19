"""Extract weekly Lesson/PdP numbers from published RPT PDFs.

Run from the repository root with PyMuPDF installed. The Web uses the
generated JSON, so requests require no PDF parsing or additional dependencies.
"""
from argparse import ArgumentParser
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
APPROVED_SCIENCE = {5: 116, 6: 89}
SCIENCE_WEEK = re.compile(
    r"^M(\d{2})\nA (\d{2}/\d{2})–(\d{2}/\d{2})\n"
    r"B (\d{2}/\d{2})–(\d{2}/\d{2})$", re.MULTILINE
)
SCIENCE_PDP = re.compile(r"^PdP (\d{3})$", re.MULTILINE)
SCIENCE_MINUTES = re.compile(r"^(30|60) minit$", re.MULTILINE)


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
                if (drawing["type"] not in ("f", "fs") or abs(rect.width - 105) > 0.1
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
                clip = fitz.Rect(510 if rtl else 140, rect.y0,
                                 rect.x0 if rtl else 300, rect.y1)
                if "School closed" in text or "Cuti sekolah" in text:
                    if LESSON.search(page.get_text(clip=clip)):
                        raise ValueError(f"{path}: Lesson assigned during school closure in week {n}")
                    continue
                if dates_by_week.setdefault(n, dates) != dates:
                    raise ValueError(f"{path}: conflicting dates for week {n}")
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
        expected = list(range(1, len(numbers) + 1))
        if subject == "SCIENCE" and path.name == "tahun_6.pdf" and len(numbers) == 89:
            # Unit 1 was added to the RPH catalogue after the 84 existing PdP.
            expected = expected[84:] + expected[:84]
        if numbers != expected:
            raise ValueError(f"{path}: non-contiguous sequence for {component}")
    if dates_by_week.keys() != lessons_by_week.keys():
        raise ValueError(f"{path}: week without a numbered lesson")
    return dates_by_week, lessons_by_week


def approved_science_weeks(path, year):
    """Read the schedule printed in an approved SK Science PDF."""
    with fitz.open(path) as pdf:
        text = "".join(page.get_text() for page in list(pdf)[1:])
    rows = list(SCIENCE_WEEK.finditer(text))
    weeks = {}
    for index, row in enumerate(rows):
        end = rows[index + 1].start() if index + 1 < len(rows) else len(text)
        body = text[row.end():end]
        numbers = list(map(int, SCIENCE_PDP.findall(body)))
        minutes = list(map(int, SCIENCE_MINUTES.findall(body)))
        if len(numbers) > 1 or len(numbers) != len(minutes):
            raise ValueError(f"{path}: invalid PdP or duration in week {row[1]}")
        if not numbers:
            continue
        dates = [datetime.strptime(f"{value}/2027", "%d/%m/%Y").date().isoformat()
                 for value in row.groups()[1:]]
        week = weeks.setdefault(str(int(row[1])), [*dates, {"": []}, []])
        if week[:4] != dates:
            raise ValueError(f"{path}: conflicting dates in week {row[1]}")
        week[4][""].extend(numbers)
        week[5].extend(minutes)
    expected = list(range(1, APPROVED_SCIENCE[year] + 1))
    if year == 6:
        expected = expected[84:] + expected[:84]
    if ([n for row in weeks.values() for n in row[4][""]] != expected
            or len(SCIENCE_PDP.findall(text)) != len(expected)
            or sum(m for row in weeks.values() for m in row[5]) != 64 * 60
            or max(map(int, weeks)) != 38
            or weeks.keys() & {"6", "18", "19"}):
        raise ValueError(f"{path}: published Science schedule is incomplete or inconsistent")
    return weeks


def update_approved_science(catalog):
    for year in APPROVED_SCIENCE:
        path = ROOT.parent / "sains" / f"CikguLaju_RPT_Sains_SK_Tahun{year}_2027.pdf"
        catalog[f"SCIENCE:{year}"] = approved_science_weeks(path, year)


def manifest_catalog():
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
    return catalog


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--approved-science", action="store_true",
                        help="refresh only the approved SK Science Year 5 and 6 entries")
    args = parser.parse_args()
    catalog = json.loads(OUTPUT.read_text(encoding="utf-8")) if args.approved_science else manifest_catalog()
    update_approved_science(catalog)
    OUTPUT.write_text("{\n" + ",\n".join(
        json.dumps(key) + ":" + json.dumps(weeks, separators=(",", ":"))
        for key, weeks in sorted(catalog.items())
    ) + "\n}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
