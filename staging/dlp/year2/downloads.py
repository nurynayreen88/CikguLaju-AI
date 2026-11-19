"""Serve Year 2 DLP Lessons and Review sessions in the published RPT order."""

from functools import cached_property
from hashlib import sha256
import json
from pathlib import Path
import re

from docx import Document

from dlp_year2_rph import SUBJECTS, catalog, render, rpt_lessons

SOURCE = Path(__file__).resolve().parent
RPT_ROOT = SOURCE.parents[2] / "rpt_2027/dlp"
RPT_CHECKSUMS = {
    "SCIENCE_DLP": "62f222a1d7393d3bbd492fc890835a172355164d2277efcfcf906b26ece22ca9",
    "MATH_DLP": "155f187c3e8d7c62e5a24d3bb6b60f7de530727c0c97b40771e8bbbd65956515",
}
PHASE_MINUTES = {30: (3, 15, 9, 3), 60: (5, 30, 20, 5)}
PHASES = ("Set induction", "Main activity", "Practice and assessment", "Closure")
LS_CODE = re.compile(r"\d+\.\d+\.\d+")


class Downloads:
    def __init__(self, subject, prefix, lesson_count, review_count, hours):
        self.subject = subject
        self.prefix = prefix
        self.lesson_count = lesson_count
        self.review_count = review_count
        self.hours = hours

    @cached_property
    def units(self):
        subject_name = SUBJECTS[self.subject]
        rpt = RPT_ROOT / f"CikguLaju_RPT_DLP_2027_{subject_name}_Year_2.docx"
        if sha256(rpt.read_bytes()).hexdigest() != RPT_CHECKSUMS[self.subject]:
            raise ValueError(f"Review the changed Year 2 {subject_name} RPT before releasing the materials.")
        tasks = iter(json.loads((SOURCE / "reviews_2027.json").read_text(encoding="utf-8"))[self.subject])
        original = catalog()[self.subject]
        scheduled = rpt_lessons(self.subject)
        lessons = iter(lesson for unit in original for lesson in unit["lessons"])
        units = {unit["title"]: {**unit, "lessons": []} for unit in original}
        taught = set()
        lesson_count = review_count = total_minutes = 0
        for row in Document(rpt).tables[2].rows[1:]:
            dates, caption, standards, objective, details = (cell.text for cell in row.cells)
            heading, unit_title = caption.splitlines()
            label, title = heading.split("  ", 1)
            *sources, duration = details.splitlines()
            minutes = int(duration.split()[0])
            codes = set(LS_CODE.findall(standards))
            if label.startswith("Review "):
                review_count += 1
                if (not codes or codes - taught or label != f"Review {review_count:02d}"
                        or sources != ["Teacher-prepared task"]):
                    raise ValueError(f"Review standards or sources do not match {subject_name} {label}.")
                task = next(tasks)
                phases = [
                    [f"{name} · {length} min", teacher, pupils]
                    for name, length, (teacher, pupils) in
                    zip(PHASES, PHASE_MINUTES[minutes], task["activities"], strict=True)
                ]
                lesson = {
                    "id": f"DLP-{self.prefix}-Y2-R{review_count:02d}", "title": title,
                    "numbered_label": label, "minutes": minutes, "rpt_dates": dates.splitlines(),
                    "standards": standards, "references": sources[0], "objective": objective,
                    "materials": task["materials"], "phases": phases,
                    "reflection": f"___ / ___ pupils met the objective. {task['follow_up']}",
                }
            else:
                lesson_count += 1
                original_lesson = next(lessons)
                reference = " · ".join(sources).replace("TB ", "Textbook ").replace("AB ", "Activity Book ")
                if (label != f"Lesson {lesson_count:02d}" or title != original_lesson["title"]
                        or scheduled[original_lesson["id"]] != {"number": lesson_count, "minutes": minutes}
                        or not original_lesson["id"].startswith(f"DLP-{self.prefix}-Y2-U{units[unit_title]['id']}-")
                        or LS_CODE.findall(standards) != LS_CODE.findall(original_lesson["standards"])
                        or objective != original_lesson["objective"] or reference != original_lesson["references"]):
                    raise ValueError(f"Lesson order does not match {subject_name} {label}.")
                lesson = {**original_lesson, "rpt_dates": dates.splitlines(), "numbered_label": label,
                          "minutes": minutes}
                taught.update(codes)
            units[unit_title]["lessons"].append({**lesson, "unit_title": unit_title})
            total_minutes += minutes
        if (next(lessons, None) is not None or next(tasks, None) is not None
                or (lesson_count, review_count, total_minutes) != (self.lesson_count, self.review_count, self.hours * 60)):
            raise ValueError(f"Unexpected lesson or review total for {subject_name} Year 2.")
        return tuple(units.values())

    def download_catalogue(self):
        return [
            {"id": unit["id"], "title": unit["title"], "lessons": [
                {"id": lesson["id"], "title": lesson["title"], "label": lesson["numbered_label"],
                 "minutes": lesson["minutes"],
                 "book_reference": "" if lesson["numbered_label"].startswith("Review ") else lesson["references"]}
                for lesson in unit["lessons"]
            ]}
            for unit in self.units
        ]

    def resolve_download(self, unit_id, lesson_id):
        for unit in self.units:
            if unit["id"] == unit_id:
                return next(((unit, lesson) for lesson in unit["lessons"] if lesson["id"] == lesson_id), None)
        return None

    def render_download(self, lesson, fmt, teacher):
        return render(self.subject, {"title": lesson["unit_title"]}, lesson, fmt, teacher)


SCIENCE = Downloads("SCIENCE_DLP", "SCI", 63, 4, 48)
MATHEMATICS = Downloads("MATH_DLP", "MAT", 78, 18, 96)
BY_SUBJECT = {"SCIENCE_DLP": SCIENCE, "MATH_DLP": MATHEMATICS}
