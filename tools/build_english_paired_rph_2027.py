"""Build one-page RPH review sheets for the English SK October pair schedule."""

import argparse
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

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
                        materials = "TB p.111, Activity 5 (CD2 Track 26 in the source RPH)"
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


def build_sheet(out, year, week, group_a, group_b, slot, lessons):
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
    run = p.add_run(f"Lesson {a:03d} + {b:03d}")
    run.bold = True
    run.font.size = Pt(26)
    p.paragraph_format.space_after = Pt(3)
    document.add_paragraph(topic).runs[0].bold = True
    document.add_paragraph(f"Week {week:02d} · Session {slot} · 60 minutes   |   Group A {group_a} · Group B {group_b}")
    document.add_paragraph("Class ____________   Date ____________   Time ____________   Attendance ____ / ____")
    for half, (number, row, task, evidence, materials) in enumerate(lessons):
        start = 30 * half
        band(document, f"Lesson {number:03d} · {row['focus']}", f"{start}–{start + 30} min")
        main, complementary = row["main_ls"], row["complementary_ls"]
        p = document.add_paragraph()
        p.paragraph_format.space_before = Pt(7)
        labelled(p, "SK/SP", f"Main {main.rsplit('.',1)[0]} / {main}  ·  Complementary {complementary.rsplit('.',1)[0]} / {complementary}")
        labelled(document.add_paragraph(), "Materials / reference", materials)
        labelled(document.add_paragraph(), "Set induction (4 min)", "Model a brief example from the task and check understanding of the instruction.")
        labelled(document.add_paragraph(), "Main activity (19 min)", task)
        labelled(document.add_paragraph(), "PBD (5 min)", "Check during the task and confirm at the end. " + evidence)
        close = "Keep the relevant picture, text or notes for the next Lesson."
        if half == 1:
            close = "Invite a pupil to share one answer and identify a point for follow-up."
        labelled(document.add_paragraph(), "Closure (2 min)", close)
    p = document.add_paragraph()
    labelled(p, "Reflection", f"{a:03d} ____ / ____ met the target.   {b:03d} ____ / ____ met the target.")
    document.add_paragraph("Follow-up _________________________________________________________________")
    document.save(out / f"RPH_English_SK_2027_Y{year}_L{a:03d}-{b:03d}.docx")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    out = parser.parse_args().output
    for year, week, group_a, group_b, slot, lessons in paired_lessons():
        folder = out / f"Year_{year}"
        folder.mkdir(parents=True, exist_ok=True)
        build_sheet(folder, year, week, group_a, group_b, slot, lessons)


if __name__ == "__main__":
    main()
