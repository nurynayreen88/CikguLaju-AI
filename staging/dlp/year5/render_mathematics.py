"""Validate and export the Mathematics DLP Year 5 SK 2027 teacher review set."""

import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

from docx import Document

from dlp_year2_rph import _pdf, _word


ROOT = Path(__file__).resolve().parents[3]
DATA = Path(__file__).with_name("mathematics_2027.json")
RPT_NAME = "CikguLaju_RPT_DLP_2027_Mathematics_Year_5"
RPT = ROOT / "rpt_2027" / "dlp" / f"{RPT_NAME}.docx"
PHASES = ("Set induction", "Main activity", "Practice and assessment", "Closure")
DURATIONS = {60: (5, 30, 20, 5), 90: (10, 45, 30, 5)}
LS_CODE = re.compile(r"\d+\.\d+\.\d+")
ACTIVITY_FIELDS = {
    "materials", "induction", "model", "guided_practice", "assessment", "evidence", "closure",
}


def official_rows(rpt):
    rows = rpt.tables[-1].rows
    if [cell.text for cell in rows[0].cells] != [
        "Date range\nA / B", "Lesson / Unit", "CS / LS", "Learning evidence (PBD)", "Book reference / Time",
    ]:
        raise ValueError("Unexpected Year 5 RPT table header")
    return rows[1:]


def load_plans():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    if sha256(RPT.read_bytes()).hexdigest() != data["rpt_sha256"]:
        raise ValueError("Year 5 RPT changed. Check the new source before exporting.")
    rpt = Document(RPT)
    plans = []
    standards_taught = defaultdict(set)
    lesson_count = review_count = 0
    for row in official_rows(rpt):
        dates, caption, source_standards, objective, book_and_time = (cell.text for cell in row.cells)
        label, unit = caption.splitlines()
        book, time = book_and_time.splitlines()
        minutes = int(time.removesuffix(" min"))
        phase_minutes = DURATIONS[minutes]
        if label == "Review":
            review_count += 1
            plan_id = f"R{review_count:02d}"
            title = f"{unit.split(' ', 2)[2]} Review"
            codes = data["review_standards"][plan_id]
            if not codes or not set(codes) <= standards_taught[unit]:
                raise ValueError(f"Review uses a standard outside its taught unit: {plan_id}")
            standards = "Review of LS " + ", ".join(codes)
            label = f"Review {review_count:02d}"
        else:
            lesson_count += 1
            label, title = label.split("  ", 1)
            if label != f"Lesson {lesson_count:02d}":
                raise ValueError(f"Invalid lesson sequence: {label}")
            plan_id = f"L{lesson_count:02d}"
            standards = " · ".join(source_standards.splitlines())
            codes = LS_CODE.findall(standards)
            if not codes or not all(code.split(".")[0] == unit.split()[1] for code in codes):
                raise ValueError(f"Invalid standards for {plan_id}")
            standards_taught[unit].update(codes)

        activity = data["activities"][plan_id]
        if set(activity) != ACTIVITY_FIELDS or not all(value.strip() for value in activity.values()):
            raise ValueError(f"Incomplete activity or assessment for {plan_id}")
        reference = data["reference_corrections"].get(plan_id, book)
        if not re.fullmatch(r"TB pp?\. \d+(?:-\d+)?(?:, \d+(?:-\d+)?)*", reference):
            raise ValueError(f"Invalid printed-page reference for {plan_id}: {reference}")
        if reference != book:
            # Change the text run in the review copy and retain the source formatting.
            matching_runs = [run for run in row.cells[-1].paragraphs[0].runs if run.text == book]
            if len(matching_runs) != 1:
                raise ValueError(f"Could not locate the textbook reference run for {plan_id}")
            matching_runs[0].text = reference

        phases = [
            (activity["induction"], "Predict or describe what you notice and give a reason."),
            (activity["model"], activity["guided_practice"]),
            ("Give the independent task and check each response against the PBD evidence.", activity["assessment"]),
            (activity["closure"], "Give a brief explanation using the method from the lesson."),
        ]
        plans.append({
            "id": plan_id,
            "unit": unit,
            "title": title,
            "label": f"{label} · {minutes} min",
            "minutes": minutes,
            "dates": " · ".join(" ".join(line.split()) for line in dates.splitlines()),
            "standards": standards,
            "reference": reference.replace("TB ", "Textbook ", 1),
            "objective": objective,
            "materials": activity["materials"],
            "phases": [(f"{phase} · {duration} min", teacher, pupils)
                       for phase, duration, (teacher, pupils) in zip(PHASES, phase_minutes, phases, strict=True)],
            "evidence": activity["evidence"],
        })

    plan_ids = {plan["id"] for plan in plans}
    all_codes = set().union(*standards_taught.values())
    if (lesson_count, review_count, len(standards_taught), len(all_codes)) != (61, 8, 8, 72):
        raise ValueError("Expected 61 lessons, 8 reviews, 8 units and 72 learning standards")
    review_ids = {plan_id for plan_id in plan_ids if plan_id.startswith("R")}
    if (plan_ids != data["activities"].keys() or review_ids != data["review_standards"].keys()
            or not data["reference_corrections"].keys() <= plan_ids):
        raise ValueError("Activity keys and reference corrections must match the RPT")
    if sum(plan["minutes"] for plan in plans) != 5760:
        raise ValueError("Year 5 Mathematics must have 96 hours")
    return rpt, plans


def render_plan(stream, plan, renderer, *, teacher=None):
    teacher = teacher or {}
    heading = ("Daily Lesson Plan", "Mathematics (DLP) · Year 5 SK", plan["title"])
    details = [
        ("Unit", plan["unit"]),
        ("Lesson / PdP", plan["label"]),
        ("RPT date ranges", plan["dates"]),
        ("Standards", plan["standards"]),
        ("Book reference", plan["reference"]),
        ("Learning objective", plan["objective"]),
        ("Materials", plan["materials"]),
    ]
    activities = [("Phase", "Teacher", "Pupils"), *plan["phases"]]
    reflection = [
        ("PBD evidence", plan["evidence"]),
        ("Reflection", teacher.get("reflection") or "___ of ___ pupils met the objective. Follow-up: ____________________."),
    ]
    renderer(stream, heading, details, activities, reflection, mathematics=True, teacher=teacher)


def export(output, rpt, plans):
    output.mkdir(parents=True, exist_ok=True)
    rpt.save(output / f"{RPT_NAME}_Teacher_Review.docx")
    for plan in plans:
        stem = f"CikguLaju_RPH_Mathematics_DLP_Y5_{plan['id']}"
        for extension, render in (("docx", _word), ("pdf", _pdf)):
            with (output / f"{stem}.{extension}").open("wb") as stream:
                render_plan(stream, plan, render)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rpt, plans = load_plans()
    if args.output:
        export(args.output, rpt, plans)
    print(f"Validated {len(plans)} Mathematics DLP Year 5 SK plans against RPT 2027.")


if __name__ == "__main__":
    main()
