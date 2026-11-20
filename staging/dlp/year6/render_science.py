"""Validate and export the Science DLP Year 6 SK 2027 teacher review set."""

import argparse
from collections import defaultdict
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re

from docx import Document

from dlp_year2_rph import _pdf, _word, science_class_fields


ROOT = Path(__file__).resolve().parents[3]
DATA = Path(__file__).with_name("science_2027.json")
STANDARD_DESCRIPTIONS = Path(__file__).with_name("science_standard_descriptions.json")
RPT_NAME = "CikguLaju_RPT_DLP_2027_Science_Year_6"
RPT = ROOT / "rpt_2027" / "dlp" / f"{RPT_NAME}.docx"
DURATIONS = {
    30: (3, 13, 11, 3),
    60: (5, 32, 18, 5),
    90: (8, 28, 28, 20, 6),
    120: (10, 35, 40, 28, 7),
}
ACTIVITY_FIELDS = {
    "materials", "induction", "teach", "practice", "assessment", "evidence", "closure",
}
TABLE_HEADER = [
    "Date range\nA / B", "Lesson / Unit", "CS / LS", "Learning evidence (PBD)", "Book reference / Time",
]


def schedule_rows(rpt):
    rows = rpt.tables[-1].rows
    if [cell.text for cell in rows[0].cells] != TABLE_HEADER:
        raise ValueError("Unexpected Science Year 6 RPT table header")
    return rows[1:]


def replace_cell_line(cell, previous, replacement):
    matching = [run for p in cell.paragraphs for run in p.runs if run.text == previous]
    if len(matching) != 1:
        raise ValueError(f"Could not locate RPT text to replace: {previous}")
    matching[0].text = replacement


def apply_corrections(row, objective, reference, correction):
    if "objective" in correction:
        replace_cell_line(row.cells[3], objective, correction["objective"])
    if "reference" in correction:
        replace_cell_line(row.cells[4], reference, correction["reference"])


def load_plans():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    descriptions = json.loads(STANDARD_DESCRIPTIONS.read_text(encoding="utf-8"))
    if sha256(RPT.read_bytes()).hexdigest() != data["rpt_sha256"]:
        raise ValueError("Science Year 6 RPT changed. Verify the source before exporting.")
    rpt = Document(RPT)
    plans = []
    taught = defaultdict(set)
    lesson_count = review_count = 0
    for row in schedule_rows(rpt):
        dates, caption, standards, objective, book_and_time = (cell.text for cell in row.cells)
        heading, unit = caption.splitlines()
        reference, duration = book_and_time.splitlines()
        minutes = int(duration.removesuffix(" min"))
        if heading == "Review":
            review_count += 1
            plan_id = f"R{review_count:02d}"
            label = f"Review {review_count:02d}"
            title = f"{unit.split(' ', 2)[2]} Review"
            codes = data["review_standards"][plan_id]
            if not codes or not set(codes) <= taught[unit]:
                raise ValueError(f"Review must use previously taught unit standards: {plan_id}")
            standards = "Review of LS " + ", ".join(codes)
        else:
            lesson_count += 1
            plan_id = f"L{lesson_count:02d}"
            label, title = heading.split("  ", 1)
            if label != f"Lesson {lesson_count:02d}":
                raise ValueError(f"Unexpected lesson sequence: {label}")
            content_standard, learning_standards = standards.splitlines()
            prefix = content_standard.removeprefix("CS ") + "."
            codes = re.findall(r"\d+\.\d+\.\d+", learning_standards)
            if not codes or not all(code.startswith(prefix) for code in codes):
                raise ValueError(f"Learning standards must belong to the stated CS: {plan_id}")
            taught[unit].update(codes)
            standards = f"{content_standard} · {learning_standards}"

        correction = data["schedule_corrections"].get(plan_id, {})
        if "title" in correction:
            title = correction["title"]
            replace_cell_line(row.cells[1], heading, f"{label}  {title}")
        apply_corrections(row, objective, reference, correction)
        reference = correction.get("reference", reference)
        if not re.fullmatch(r"TB pp?\. \d+(?:-\d+)?(?:, ?\d+(?:-\d+)?)*", reference):
            raise ValueError(f"Invalid printed-page reference: {plan_id}")
        activity = data["activities"][plan_id]
        if set(activity) != ACTIVITY_FIELDS or not all(value.strip() for value in activity.values()):
            raise ValueError(f"Invalid activity: {plan_id}")
        steps = [
            ("Set induction", activity["induction"], "Respond to the opening prompt using the material shown."),
            ("Main activity", activity["teach"], activity["practice"]),
            ("Practice and assessment", "Set the individual task and check the PBD evidence.", activity["assessment"]),
            ("Closure", activity["closure"], "Answer using one observation or example from the session."),
        ]
        if minutes in (90, 120):
            teacher_extension, pupil_extension = data["extended_practice"][plan_id]
            if not teacher_extension.strip() or not pupil_extension.strip():
                raise ValueError(f"Incomplete guided application: {plan_id}")
            steps.insert(2, ("Guided application", teacher_extension, pupil_extension))
        phases = [
            (f"{name} · {time} min", teacher, pupils)
            for (name, teacher, pupils), time in zip(steps, DURATIONS[minutes], strict=True)
        ]
        content_codes = tuple(dict.fromkeys(code.rsplit(".", 1)[0] for code in codes))
        plans.append({
            "id": plan_id,
            "title": title,
            "unit": unit,
            "label": f"{label} · {duration}",
            "dates": dates.replace("\n", " · "),
            "standards": standards,
            "content_standards": " · ".join(
                f"{code} {descriptions['cs'][code]}" for code in content_codes
            ),
            "learning_standards": " · ".join(
                f"{code} {descriptions['ls'][code]}" for code in codes
            ),
            "reference": reference.replace("TB ", "Textbook ", 1),
            "objective": correction.get("objective", objective),
            "materials": activity["materials"],
            "phases": phases,
            "evidence": activity["evidence"],
            "minutes": minutes,
        })

    ids = {plan["id"] for plan in plans}
    review_ids = {plan["id"] for plan in plans if plan["id"].startswith("R")}
    if ids != data["activities"].keys() or review_ids != data["review_standards"].keys():
        raise ValueError("Activity or review IDs differ from the RPT")
    longer_sessions = {plan["id"] for plan in plans if plan["minutes"] in (90, 120)}
    if longer_sessions != data["extended_practice"].keys():
        raise ValueError("Every extended practice must correspond to a longer RPT session")
    if not data["schedule_corrections"].keys() <= ids:
        raise ValueError("An RPT correction has no matching session")
    learning_codes = set().union(*taught.values())
    if (lesson_count, review_count, len(taught), len(learning_codes)) != (52, 9, 13, 96):
        raise ValueError("Expected 52 lessons, 9 reviews, 13 units and 96 learning standards")
    if (set(descriptions["ls"]) != learning_codes
            or set(descriptions["cs"]) != {code.rsplit(".", 1)[0] for code in learning_codes}
            or any(not text.strip() for group in descriptions.values() for text in group.values())):
        raise ValueError("Incomplete Science Year 6 DLP standard descriptions")
    if sum(plan["minutes"] for plan in plans) != 3840:
        raise ValueError("Year 6 Science must have 64 hours")
    return rpt, plans


@lru_cache(maxsize=1)
def _download_units():
    _, plans = load_plans()
    units = {}
    for plan in plans:
        key = f"{int(plan['unit'].split()[1]):02d}"
        unit = units.setdefault(key, {"id": key, "title": plan["unit"], "lessons": {}})
        unit["lessons"][f"DLP-SCI-Y6-{plan['id']}"] = plan
    return units


def download_catalogue():
    return [
        {"id": unit["id"], "title": unit["title"], "lessons": [
            {"id": key, "title": plan["title"], "label": plan["label"],
             "book_reference": plan["reference"], "minutes": plan["minutes"]}
            for key, plan in unit["lessons"].items()
        ]}
        for unit in _download_units().values()
    ]


def resolve_download(unit_id, lesson_id):
    unit = _download_units().get(unit_id)
    if unit is None or lesson_id not in unit["lessons"]:
        return None
    return unit, {**unit["lessons"][lesson_id], "id": lesson_id}


def render_download(plan, fmt, teacher):
    output = BytesIO()
    render_plan(output, plan, {"word": _word, "pdf": _pdf}[fmt], teacher=teacher)
    return output.getvalue()


def render_plan(stream, plan, renderer, *, teacher=None):
    teacher = teacher or {}
    heading = ("Daily Lesson Plan", "Science (DLP) · Year 6 SK", plan["title"])
    details = [
        ("Unit", plan["unit"]),
        ("Lesson / PdP", plan["label"]),
        ("RPT date ranges", plan["dates"]),
        *science_class_fields(teacher, english=True),
        ("Content Standards", plan["content_standards"]),
        ("Learning Standards", plan["learning_standards"]),
        ("Book reference", plan["reference"]),
        ("Learning objective", plan["objective"]),
        ("Materials", plan["materials"]),
    ]
    activities = [("Phase", "Teacher", "Pupils"), *plan["phases"]]
    reflection = [
        ("PBD evidence", plan["evidence"]),
        ("Reflection", teacher.get("reflection") or
         "___ of ___ pupils met the objective. Follow-up: ____________________."),
    ]
    renderer(stream, heading, details, activities, reflection)


def export(output, rpt, plans):
    output.mkdir(parents=True, exist_ok=True)
    rpt.save(output / f"{RPT_NAME}_Teacher_Review.docx")
    for plan in plans:
        stem = f"CikguLaju_RPH_Science_DLP_Y6_{plan['id']}"
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
    print(f"Validated {len(plans)} Science DLP Year 6 SK plans against RPT 2027.")


if __name__ == "__main__":
    main()
