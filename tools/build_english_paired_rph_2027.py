"""Build one-page RPH review sheets for the English SK October pair schedule."""

import argparse
import json
from functools import lru_cache
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

if __package__:
    from .build_english_rpt_2027_review import ROOT, SOURCE, schedule, source_rows
else:
    from build_english_rpt_2027_review import ROOT, SOURCE, schedule, source_rows


TASKS = SOURCE / "october_paired_rph_tasks.txt"
SOW_INDEX = ROOT / "audits" / "english_primary_2_6_official_sow_index_20261103.json"
SOW_LEDGER = ROOT / "audits" / "english_2_6_independent_sow_pdf_code_ledger_20261104.json"
TEAL = "086B66"
INK = "142C44"


def read_tasks():
    tasks = {}
    for line in TASKS.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            year = int(line[1:-1])
            continue
        n, task, evidence = line.split(" | ")
        key = (year, int(n))
        if key in tasks or not (task and evidence):
            raise ValueError(f"Duplicate or empty adaptation for {key}")
        tasks[key] = task, evidence
    return tasks


def paired_lessons():
    tasks = read_tasks()
    index = json.loads(SOW_INDEX.read_text())["lessons"]
    ledger = json.loads(SOW_LEDGER.read_text())["rows"]
    used = set()
    for year in range(2, 7):
        rpt_rows = source_rows(year)
        for week, group_a, group_b, sessions in schedule(year):
            for slot, session in enumerate(sessions, 1):
                if len(session) != 2:
                    continue
                lessons = []
                for n in session:
                    key = f"{year}/{n}"
                    row = index[key]
                    audited = ledger[key]
                    standards = [row["main_ls"], row["complementary_ls"]]
                    if row["teacher_selected"] or standards != [
                        *audited["sow_pdf_observed_main_ls"],
                        *audited["sow_pdf_observed_complementary_ls"],
                    ]:
                        raise ValueError(f"Expected two verified fixed standards for {key}")
                    used.add((year, n))
                    task, evidence = tasks[year, n]
                    if not (ROOT / f"rph_standalone/english/year{year}/lesson_{n:03d}.md").is_file():
                        raise ValueError(f"Missing source RPH for {key}")
                    materials = " ".join(rpt_rows[n][2])
                    if materials == "non-textbook / SOW task":
                        materials = "Teacher-prepared materials listed in the original RPH"
                    if key == "4/103":
                        materials = "SB p.73, Activity 5 · TB p.111 · CD2 Track 26"
                    lessons.append((n, row, task, evidence, materials))
                if lessons[0][1]["topic"] != lessons[1][1]["topic"]:
                    raise ValueError(f"Paired lessons cross topics for Year {year}, week {week}")
                yield year, week, group_a, group_b, slot, lessons
    if used != tasks.keys():
        raise ValueError("Adaptation file contains Lessons outside the October pairs")


def stylise(document):
    section = document.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(17)
    section.bottom_margin = Mm(15)
    section.left_margin = section.right_margin = Mm(18)
    style = document.styles["Normal"]
    style.font.name = "DejaVu Sans"
    style.font.size = Pt(10)
    style.font.color.rgb = RGBColor.from_string(INK)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.18
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run("CikguLaju  /  English SK 2027").font.size = Pt(8)


def labelled(paragraph, label, detail):
    paragraph.add_run(label + "  ").bold = True
    paragraph.add_run(detail)


def band(document, left, right):
    table = document.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for column, cell, width, title in zip(
        table.columns, table.rows[0].cells, (116, 58), (left, right), strict=True
    ):
        column.width = cell.width = Mm(width)
        shade = OxmlElement("w:shd")
        shade.set(qn("w:fill"), TEAL)
        cell._tc.get_or_add_tcPr().append(shade)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(title)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)


def make_sheet(year, week, group_a, group_b, slot, lessons, teacher=None):
    document = Document()
    stylise(document)
    a, b = (lesson[0] for lesson in lessons)
    topic = lessons[0][1]["topic"]
    document.core_properties.title = f"English SK Year {year} Lesson {a:03d} + {b:03d}"
    document.core_properties.author = "CikguLaju"
    p = document.add_paragraph()
    run = p.add_run(f"RPH ENGLISH SK 2027  /  YEAR {year}  /  SEMAKAN")
    run.bold = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor.from_string(TEAL)
    p = document.add_paragraph()
    run = p.add_run(topic)
    run.bold = True
    run.font.size = Pt(26)
    p.paragraph_format.space_after = Pt(3)
    labelled(document.add_paragraph(), "SOW references", f"Lesson {a:03d} + {b:03d}")
    document.add_paragraph(f"Week {week:02d} · Session {slot} · 60 minutes   |   Group A {group_a} · Group B {group_b}")
    teacher = teacher or {}
    document.add_paragraph("   ".join(
        f"{label} {teacher.get(key) or blank}"
        for label, key, blank in (
            ("Class", "class", "__________"), ("Date", "date", "__________"),
            ("Time", "time", "__________"), ("Attendance", "students", "____ / ____"),
        )
    ))

    band(document, "Curriculum and materials", "SOW")
    for number, row, _, _, _ in lessons:
        main, complementary = row["main_ls"], row["complementary_ls"]
        p = document.add_paragraph()
        labelled(
            p, f"SK/SP · {number:03d}",
            f"Main {main.rsplit('.', 1)[0]} / {main}  ·  Complementary {complementary.rsplit('.', 1)[0]} / {complementary}",
        )
    first_materials, second_materials = (lesson[4] for lesson in lessons)
    if first_materials == second_materials:
        labelled(document.add_paragraph(), "Materials", first_materials)
    else:
        labelled(document.add_paragraph(), "Materials",
                 f"{a:03d} – {first_materials}\n{b:03d} – {second_materials}")

    band(document, "Teaching and learning", "60 minutes")
    labelled(document.add_paragraph(), "Set induction (5 min)", f"Show a prompt from the {topic.rstrip('.!?')} materials. Elicit relevant words and model one response.")
    p = document.add_paragraph("Main activities (43 min)")
    p.runs[0].bold = True
    for number, (_, _, task, _, _) in enumerate(lessons, 1):
        labelled(document.add_paragraph(), f"Activity {number}", task)
    p = document.add_paragraph("PBD (8 min)")
    p.runs[0].bold = True
    p.add_run("  Collect evidence across both activities and confirm one response from each pupil during the session.")
    for number, (_, _, _, evidence, _) in enumerate(lessons, 1):
        labelled(document.add_paragraph(), f"Activity {number}", evidence)
    labelled(document.add_paragraph(), "Closure (4 min)", "Invite pupils to share a response from the activities and recap one useful example from the session.")
    labelled(document.add_paragraph(), "Reflection", "Activity 1 ____ / ____ met the target.   Activity 2 ____ / ____ met the target.")
    document.add_paragraph("Follow-up _________________________________________________________________")
    if teacher.get("reflection"):
        labelled(document.add_paragraph(), "Teacher notes", teacher["reflection"])
    return document


@lru_cache(maxsize=1)
def paired_plan_index():
    return {
        (plan[0], lesson[0]): plan
        for plan in paired_lessons()
        for lesson in plan[-1]
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    out = parser.parse_args().output
    for year, week, group_a, group_b, slot, lessons in paired_lessons():
        folder = out / f"Year_{year}"
        folder.mkdir(parents=True, exist_ok=True)
        a, b = (lesson[0] for lesson in lessons)
        make_sheet(year, week, group_a, group_b, slot, lessons).save(
            folder / f"RPH_English_SK_2027_Y{year}_L{a:03d}-{b:03d}.docx"
        )


if __name__ == "__main__":
    main()
