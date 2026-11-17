"""Check and export the Year 4 Mathematics DLP teacher-review drafts."""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import re

from docx import Document

from dlp_year2_rph import _pdf, _word


SOURCE = Path(__file__).resolve().parent
RPT = SOURCE.parents[2] / "rpt_2027/dlp/CikguLaju_RPT_DLP_2027_Mathematics_Year_4.docx"
RPT_SHA256 = "7e0f3c4fd73cb45b34ade909e51256dbc5af129992c0204c2a19f9be7ce3c59b"
LS_CODE = re.compile(r"\d+\.\d+\.\d+")
PHASES = ("Set induction", "Main activity", "Practice and assessment", "Closure")
PHASE_MINUTES = {60: (5, 30, 20, 5), 90: (10, 45, 25, 10)}
TABLE_HEADER = ("Phase", "Teacher", "Pupils")


def read_drafts():
    for number in range(1, 9):
        unit_file = SOURCE / f"mathematics_unit_{number:02d}.md"
        introduction, *drafts = unit_file.read_text(encoding="utf-8").split("\n## ")
        unit = introduction.strip().splitlines()[-1]
        for draft in drafts:
            heading, *lines = (line for line in draft.splitlines() if line)
            details = {}
            activities = []
            for line in lines:
                if line.startswith("**"):
                    label, value = line.split("** · ", 1)
                    details[label[2:]] = value
                elif line.startswith("| ") and line not in ("| Phase | Teacher | Pupils |", "| --- | --- | --- |"):
                    phase, teacher, pupils = line[2:-2].split(" | ")
                    activities.append((phase, teacher, pupils))
            yield unit, heading, details, activities


def verify_drafts():
    if sha256(RPT.read_bytes()).hexdigest() != RPT_SHA256:
        raise ValueError("The RPT changed. Reconcile and review the drafts before exporting.")

    lesson = review = 0
    standards_taught = defaultdict(set)
    checked = []
    durations = Counter()
    for row, draft in zip(Document(RPT).tables[-1].rows[1:], read_drafts(), strict=True):
        draft_unit, heading, details, activities = draft
        dates, caption, standards, objective, book = (cell.text for cell in row.cells)
        title, unit = caption.splitlines()
        *references, duration = book.splitlines()
        minutes = int(duration.split()[0])
        if title == "Review":
            review += 1
            identifier = f"DLP-MAT-Y4-R{review:02d}"
            label = f"Review {review:02d}"
            title = f"{unit.split(' ', 2)[2]} Review"
            review_standards = details["Standards"].removeprefix("Review LS ").split(", ")
            if not set(review_standards) <= standards_taught[unit]:
                raise ValueError(f"Review uses a standard that has not been taught in the unit: {identifier}")
            standards = "Review LS " + ", ".join(review_standards)
        else:
            lesson += 1
            identifier = f"DLP-MAT-Y4-L{lesson:02d}"
            label = f"Lesson {lesson:02d}"
            if not title.startswith(label + "  "):
                raise ValueError(f"The RPT lesson is out of sequence: {identifier}")
            title = title.removeprefix(label + "  ")
            standards_taught[unit].update(LS_CODE.findall(standards))
            standards = " · ".join(standards.splitlines())

        expected = {
            "RPT 2027 dates": " · ".join(dates.splitlines()),
            "Duration": duration,
            "Standards": standards,
            "References": " · ".join(references).replace("TB ", "Textbook "),
            "Learning objective": objective,
        }
        if draft_unit != unit or heading != f"{identifier} · {label} · {title}" or any(
            details.get(key) != value for key, value in expected.items()
        ):
            raise ValueError(f"Draft details do not match the RPT: {identifier}")
        phases = [f"{phase} · {time} min" for phase, time in zip(PHASES, PHASE_MINUTES[minutes], strict=True)]
        if [phase for phase, _, _ in activities] != phases or any(
            not teacher.strip() or not pupils.strip() for _, teacher, pupils in activities
        ):
            raise ValueError(f"Missing activity or incorrect time allocation: {identifier}")
        if not details.get("Materials", "").strip() or not details.get("Reflection", "").strip():
            raise ValueError(f"Missing materials or reflection: {identifier}")
        checked.append((identifier, title, unit, label, details, activities))
        durations[minutes] += 1

    if (lesson, review) != (69, 8) or durations != {60: 39, 90: 38}:
        raise ValueError("Year 4 Mathematics must cover 69 Lesson, eight Review and 96 hours.")
    if len(set().union(*standards_taught.values())) != 85:
        raise ValueError("Year 4 Mathematics must cover 85 learning standards.")
    return checked


def export(drafts, output):
    output.mkdir(parents=True, exist_ok=True)
    for identifier, title, unit, label, details, activities in drafts:
        heading = ("Daily Lesson Plan", "Mathematics (DLP) · Year 4 SK", title)
        fields = [
            ("Unit", unit),
            ("Lesson / PdP", f"{label} · {details['Duration']}"),
            ("RPT 2027 dates", details["RPT 2027 dates"]),
            ("Class / date / time", "Class: ______ · Date: ______ · Time: ______ · Pupils: ______"),
            ("Standards", details["Standards"]),
            ("Book references", details["References"]),
            ("Learning objective", details["Learning objective"]),
            ("Materials", details["Materials"]),
        ]
        reflection = [("Reflection", details["Reflection"])]
        for suffix, render in (("docx", _word), ("pdf", _pdf)):
            with (output / f"{identifier}.{suffix}").open("wb") as stream:
                render(stream, heading, fields, [TABLE_HEADER, *activities], reflection)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Export verified Word and PDF files to this directory.")
    args = parser.parse_args()
    drafts = verify_drafts()
    if args.output:
        export(drafts, args.output)
    print(f"Verified {len(drafts)} RPH, 85 learning standards and 96 hours.")


if __name__ == "__main__":
    main()
