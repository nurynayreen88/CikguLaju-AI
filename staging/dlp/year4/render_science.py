"""Verify and render the Year 4 Science DLP lessons against RPT 2027."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import re

from docx import Document

from dlp_year2_rph import _pdf, _word, science_class_fields


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).with_name("science_2027.json")
STANDARD_DESCRIPTIONS = Path(__file__).with_name("science_standard_descriptions.json")
PHASES = ("Set induction", "Main activity", "Practice and assessment", "Closure")
DURATIONS = {30: (3, 15, 9, 3), 60: (5, 30, 20, 5)}
LS_CODE = re.compile(r"\d+\.\d+\.\d+")


def load_plans():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    descriptions = json.loads(STANDARD_DESCRIPTIONS.read_text(encoding="utf-8"))
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
            codes = plan["review_lss"]
            if not codes or not set(codes) <= standards_taught[unit]:
                raise ValueError(f"Review uses an untaught standard: {plan_id}")
        else:
            lesson_number += 1
            label, title = title.split("  ", 1)
            plan_id = f"DLP-SCI-Y4-L{lesson_number:02d}"
            if label != f"Lesson {lesson_number:02d}":
                raise ValueError(f"Lesson out of sequence: {plan_id}")
            content_standard, learning_standards = standards.splitlines()
            prefix = content_standard.removeprefix("CS ") + "."
            codes = LS_CODE.findall(learning_standards)
            if not codes or not all(code.startswith(prefix) for code in codes):
                raise ValueError(f"Learning standards must belong to the stated CS: {plan_id}")
            standards_taught[unit].update(codes)
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

        content_codes = tuple(dict.fromkeys(code.rsplit(".", 1)[0] for code in codes))
        plan["content_standards"] = " · ".join(
            f"{code} {descriptions['cs'][code]}" for code in content_codes
        )
        plan["learning_standards"] = " · ".join(
            f"{code} {descriptions['ls'][code]}" for code in codes
        )

    learning_codes = set().union(*standards_taught.values())
    if (lesson_number, review_number) != (59, 10) or len(learning_codes) != 92:
        raise ValueError("Year 4 Science coverage changed")
    if (set(descriptions["ls"]) != learning_codes
            or set(descriptions["cs"]) != {code.rsplit(".", 1)[0] for code in learning_codes}
            or any(not text.strip() for group in descriptions.values() for text in group.values())):
        raise ValueError("Incomplete Science Year 4 DLP standard descriptions")
    if Counter(plan["minutes"] for plan in plans) != {60: 59, 30: 10}:
        raise ValueError("Year 4 Science must cover 3,840 minutes")
    return plans


@lru_cache(maxsize=1)
def _download_units():
    units = {}
    for plan in load_plans():
        unit_id = f"{int(plan['unit'].split()[1]):02d}"
        unit = units.setdefault(unit_id, {"id": unit_id, "title": plan["unit"], "lessons": {}})
        unit["lessons"][plan["id"]] = plan
    return units


def _book_references(plan):
    return " · ".join(plan["references"]).replace("TB ", "Textbook ")


def _catalogue_minutes(plan):
    from staging.dlp.science_y45_session_delivery import extend
    return extend(plan,4)["minutes"]

def download_catalogue():
    return [
        {"id": unit["id"], "title": unit["title"], "lessons": [
            {"id": plan["id"], "title": plan["title"], "label": plan["label"],
             "book_reference": _book_references(plan), "minutes": _catalogue_minutes(plan)}
            for plan in unit["lessons"].values()
        ]}
        for unit in _download_units().values()
    ]


def resolve_download(unit_id, lesson_id):
    unit = _download_units().get(unit_id)
    if unit is None or lesson_id not in unit["lessons"]:
        return None
    return unit, unit["lessons"][lesson_id]


def render_download(plan, fmt, teacher):
    from staging.dlp.science_y45_session_delivery import for_teacher
    plan=for_teacher(plan,4,teacher)
    output = BytesIO()
    render_plan(output, plan, {"word": _word, "pdf": _pdf}[fmt], teacher=teacher)
    return output.getvalue()


def render_plan(stream, plan, renderer, *, teacher=None):
    teacher = teacher or {}
    heading = ("Daily Lesson Plan", "Science (DLP) · Year 4 SK", plan["title"])
    details = [
        ("Unit", plan["unit"]),
        ("Lesson / PdP", f"{plan['label']} · {plan['minutes']} min"),
        ("RPT 2027 dates", " · ".join(plan["rpt_dates"])),
        *science_class_fields(teacher, english=True),
        ("Content Standards", plan["content_standards"]),
        ("Learning Standards", plan["learning_standards"]),
        ("Book references", _book_references(plan)),
        ("Learning objective", plan["objective"]),
        ("Materials", plan["materials"]),
    ]
    activities = [("Phase", "Teacher", "Pupils")]
    activities.extend(
        (f"{phase['phase']} · {phase['minutes']} min", phase["teacher"], phase["pupils"])
        for phase in plan["phases"]
    )
    reflection = [("Reflection", teacher.get("reflection") or
                   f"___ / ___ pupils met the objective. {plan['follow_up']}")]
    renderer(stream, heading, details, activities, reflection)


def export(plans, output):
    output.mkdir(parents=True, exist_ok=True)
    for plan in plans:
        for suffix, renderer in (("docx", _word), ("pdf", _pdf)):
            with (output / f"{plan['id']}.{suffix}").open("wb") as stream:
                render_plan(stream, plan, renderer)


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
