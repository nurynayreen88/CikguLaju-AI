"""Verify and export the Year 4 Science DLP review pack outside production."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import re

from docx import Document

from dlp_year2_rph import _pdf, _word


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).with_name("science_2027.json")
PHASES = ("Set induction", "Main activity", "Practice and assessment", "Closure")
DURATIONS = {30: (3, 15, 9, 3), 60: (5, 30, 20, 5)}
LS_CODE = re.compile(r"\d+\.\d+\.\d+")


def load_plans():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    rpt = ROOT / "rpt_2027" / "dlp" / data["rpt_file"]
    if (data["year"], data["planning_year"], data["subject"]) != (4, 2027, "SCIENCE_DLP"):
        raise ValueError("Unexpected year or subject")
    if hashlib.sha256(rpt.read_bytes()).hexdigest() != data["rpt_sha256"]:
        raise ValueError("Published RPT changed. Compare the plans with the new RPT before exporting.")

    rows = Document(rpt).tables[-1].rows[1:]
    lesson_number = review_number = 0
    standards_taught = defaultdict(set)
    plans = data["plans"]
    for row, plan in zip(rows, plans, strict=True):
        dates, caption, standards, objective, book = (cell.text for cell in row.cells)
        title, unit = caption.splitlines()
        if title == "Review":
            review_number += 1
            label = f"Review {review_number:02d}"
            plan_id = f"DLP-SCI-Y4-R{review_number:02d}"
            title = f"{unit.split(' ', 2)[2]} Review"
            review_codes = set(plan["review_lss"])
            if not review_codes or not review_codes <= standards_taught[unit]:
                raise ValueError(f"Review uses an untaught standard: {plan_id}")
        else:
            lesson_number += 1
            label, title = title.split("  ", 1)
            plan_id = f"DLP-SCI-Y4-L{lesson_number:02d}"
            if label != f"Lesson {lesson_number:02d}":
                raise ValueError(f"Lesson out of sequence: {plan_id}")
            standards_taught[unit].update(LS_CODE.findall(standards))
            if "review_lss" in plan:
                raise ValueError(f"Review standards appear in a numbered lesson: {plan_id}")

        expected = (plan_id, label, title, unit, dates.splitlines(), standards.splitlines(), objective, book.splitlines())
        observed = (plan["id"], plan["label"], plan["title"], plan["unit"], plan["rpt_dates"],
                    plan["standards"], plan["objective"], [*plan["references"], f"{plan['minutes']} min"])
        if observed != expected:
            raise ValueError(f"Plan does not match the RPT row: {plan_id}")
        if tuple(phase["phase"] for phase in plan["phases"]) != PHASES or tuple(
            phase["minutes"] for phase in plan["phases"]
        ) != DURATIONS[plan["minutes"]]:
            raise ValueError(f"Incorrect phases or time allocation: {plan_id}")
        if not plan["materials"] or not plan["follow_up"] or any(
            not phase["teacher"] or not phase["pupils"] for phase in plan["phases"]
        ):
            raise ValueError(f"Incomplete teaching details: {plan_id}")

    if (lesson_number, review_number) != (59, 10) or len(set().union(*standards_taught.values())) != 92:
        raise ValueError("Year 4 Science coverage changed")
    if Counter(plan["minutes"] for plan in plans) != {60: 59, 30: 10}:
        raise ValueError("Year 4 Science must cover 3,840 minutes")
    return plans


def export(plans, output):
    output.mkdir(parents=True, exist_ok=True)
    for plan in plans:
        heading = ("Daily Lesson Plan", "Science (DLP) · Year 4 SK", plan["title"])
        if "review_lss" in plan:
            standards = "Review LS " + ", ".join(plan["review_lss"])
        else:
            standards = " · ".join(plan["standards"])
        details = [
            ("Unit", plan["unit"]),
            ("Lesson / PdP", f"{plan['label']} · {plan['minutes']} min"),
            ("RPT 2027 dates", " · ".join(plan["rpt_dates"])),
            ("Class / date / time", "Class: ______ · Date: ______ · Time: ______ · Pupils: ______"),
            ("Standards", standards),
            ("Book references", " · ".join(plan["references"]).replace("TB ", "Textbook ")),
            ("Learning objective", plan["objective"]),
            ("Materials", plan["materials"]),
        ]
        activities = [("Phase", "Teacher", "Pupils")]
        activities.extend(
            (f"{phase['phase']} · {phase['minutes']} min", phase["teacher"], phase["pupils"])
            for phase in plan["phases"]
        )
        reflection = [("Reflection", f"___ / ___ pupils met the objective. {plan['follow_up']}")]
        for suffix, render in (("docx", _word), ("pdf", _pdf)):
            with (output / f"{plan['id']}.{suffix}").open("wb") as stream:
                render(stream, heading, details, activities, reflection)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Export verified Word and PDF files to this directory.")
    args = parser.parse_args()
    plans = load_plans()
    if args.output:
        export(plans, args.output)
    print(f"Verified {len(plans)} RPH, 92 LS and {sum(plan['minutes'] for plan in plans)} minutes.")


if __name__ == "__main__":
    main()
