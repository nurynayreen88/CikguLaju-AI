"""Check Mathematics DLP Year 3 plans against the published RPT and export Word/PDF."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import re

from docx import Document

from dlp_year2_rph import _pdf, _word


SOURCE = Path(__file__).resolve().parent
RPT = SOURCE.parents[2] / "rpt_2027/dlp/CikguLaju_RPT_DLP_2027_Mathematics_Year_3.docx"
RPT_SHA256 = "a822f20d6c3276dec7f6dbb261ea9bb7e0d5da103117b6134f11026d484bfa00"
LS_CODE = re.compile(r"\d+\.\d+\.\d+")
PHASES = ("Set induction", "Main activity", "Practice and assessment", "Closure")
PHASE_MINUTES = {60: (5, 30, 20, 5), 90: (10, 45, 25, 10)}
TABLE_HEADER = ("Phase", "Teacher", "Pupils")


def read_drafts():
    for number in range(1, 10):
        path = SOURCE / f"mathematics_unit_{number:02d}.md"
        introduction, *drafts = path.read_text(encoding="utf-8").split("\n## ")
        unit = introduction.strip().split(" · ")[-1]
        for draft in drafts:
            heading, *lines = draft.splitlines()
            identifier, title = heading.split(" · ", 1)
            details = {}
            activities = []
            for line in lines:
                if line.startswith("**"):
                    name, value = line[2:].split("** · ", 1)
                    details[name] = value
                elif line.startswith("| ") and line not in (
                    "| Phase | Teacher | Pupils |", "| --- | --- | --- |",
                ):
                    activities.append(tuple(line[2:-2].split(" | ")))
            yield identifier, title, unit, details, activities


def normalized_reference(text):
    text = text.replace("Textbook Part ", "TB ").replace("Activity Book ", "AB ").replace("–", "-")
    return re.sub(r"\bpp?\.", "p.", text)


def verify_drafts():
    if sha256(RPT.read_bytes()).hexdigest() != RPT_SHA256:
        raise ValueError("The RPT changed. Review the draft before exporting.")

    result = []
    lesson = review = 0
    previous_unit = None
    taught = defaultdict(set)
    durations = Counter()
    for row, draft in zip(Document(RPT).tables[-1].rows[1:], read_drafts(), strict=True):
        identifier, title, unit, details, activities = draft
        dates, caption, standards, objective, book = (cell.text for cell in row.cells)
        label_and_title, rpt_unit = caption.splitlines()
        *references, duration = book.splitlines()
        minutes = int(duration.split()[0])
        if label_and_title.startswith("Review  "):
            review += 1
            label = f"Review {review:02d}"
            heading = "Review: " + label_and_title.removeprefix("Review  ")
            expected_id = f"DLP-MAT-Y3-R{review:02d}"
            review_codes = set(LS_CODE.findall(details["Standards"]))
            if rpt_unit != "Consolidation" or unit != previous_unit or not review_codes or review_codes - taught[unit]:
                raise ValueError(f"Review uses an unverified unit or learning standard: {identifier}")
        else:
            lesson += 1
            label = f"Lesson {lesson:02d}"
            if not label_and_title.startswith(label + "  ") or unit != rpt_unit:
                raise ValueError(f"RPT lesson or unit does not match: {identifier}")
            heading = label_and_title.removeprefix(label + "  ")
            expected_id = f"DLP-MAT-Y3-U{int(unit.split()[1]):02d}-{lesson:02d}"
            draft_standards = re.sub(r" \([iv]+\)(?:, \([iv]+\))*", "", details["Standards"])
            if draft_standards != " · ".join(standards.splitlines()):
                raise ValueError(f"RPT standards do not match: {identifier}")
            taught[unit].update(LS_CODE.findall(standards))
            previous_unit = unit

        if (identifier != expected_id or title != heading or details["Learning objective"] != objective
                or normalized_reference(details["References"]) != normalized_reference(" · ".join(references))):
            raise ValueError(f"Draft details do not match the RPT: {identifier}")
        phases = [f"{phase} · {time} min" for phase, time in zip(PHASES, PHASE_MINUTES[minutes], strict=True)]
        if [phase for phase, _, _ in activities] != phases or any(
            not teacher.strip() or not pupils.strip() for _, teacher, pupils in activities
        ):
            raise ValueError(f"Missing activity or incorrect time allocation: {identifier}")
        if not details["Materials"].strip() or not details["Reflection"].strip():
            raise ValueError(f"Missing materials or reflection: {identifier}")
        result.append((identifier, title, rpt_unit, label, " · ".join(dates.splitlines()), duration, details, activities))
        durations[minutes] += 1

    if (lesson, review) != (73, 9) or durations != {60: 54, 90: 28}:
        raise ValueError("Expected 73 Lesson, nine Review and 96 hours.")
    if len(set().union(*taught.values())) != 102:
        raise ValueError("Expected coverage of 102 learning standards.")
    return result


def render_plan(stream, draft, renderer):
    _, title, unit, label, dates, duration, details, activities = draft
    heading = ("Daily Lesson Plan", "Mathematics (DLP) · Year 3 SK", title)
    fields = [
        ("Unit", unit),
        ("Lesson / PdP", f"{label} · {duration}"),
        ("RPT 2027 dates", dates),
        ("Class / date / time", "Class: ______ · Date: ______ · Time: ______ · Pupils: ______"),
        ("Standards", details["Standards"]),
        ("Book references", details["References"]),
        ("Learning objective", details["Learning objective"]),
        ("Materials", details["Materials"]),
    ]
    renderer(stream, heading, fields, [TABLE_HEADER, *activities], [("Reflection", details["Reflection"])])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Directory for the verified Word and PDF files.")
    args = parser.parse_args()
    plans = verify_drafts()
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        for plan in plans:
            for suffix, renderer in (("docx", _word), ("pdf", _pdf)):
                with (args.output / f"{plan[0]}.{suffix}").open("wb") as stream:
                    render_plan(stream, plan, renderer)
    print(f"Verified {len(plans)} RPH, 102 learning standards and 96 hours.")


if __name__ == "__main__":
    main()
