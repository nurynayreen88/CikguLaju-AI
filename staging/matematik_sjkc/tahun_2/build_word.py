"""Build the A4 source pack from the published RPT mapping and lesson activities."""

import csv
import json
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
RPT = HERE.parents[2] / "rpt_2027/sjkc/matematik/year_2_2027.json"
STEM = "RPH_2027_Matematik_SJKC_Tahun_2"
FONT = "Noto Sans CJK SC"
NAVY = "163D57"


def styles(doc):
    for name, size, bold, color in (
        ("Normal", 9.5, False, "172634"),
        ("Lesson title", 19, True, NAVY),
        ("Lesson number", 10, True, NAVY),
        ("Lesson label", 9, True, NAVY),
    ):
        style = (doc.styles["Normal"] if name == "Normal"
                 else doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH))
        style.base_style = None if name == "Normal" else doc.styles["Normal"]
        style.font.name = FONT
        style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.line_spacing = 1.08


def table_row(table, label, values):
    left, right = table.add_row().cells
    left.width, right.width = table.columns[0].width, table.columns[1].width
    for cell in (left, right):
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), "EDF4F7")
    left._tc.get_or_add_tcPr().append(shading)
    p = left.paragraphs[0]
    p.style = "Lesson label"
    p.add_run(label)
    for index, (role, value) in enumerate(values):
        p = right.paragraphs[0] if index == 0 else right.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        if role:
            p.add_run(role + " ").bold = True
        p.add_run(value)


def build():
    lessons = json.loads(RPT.read_text(encoding="utf-8"))["lessons"]
    with (HERE / "aktiviti.tsv").open(encoding="utf-8", newline="") as stream:
        activities = list(csv.DictReader(stream, delimiter="\t"))
    assert [row["pdp"] for row in lessons] == [int(row["pdp"]) for row in activities] == list(range(1, 97))
    doc = Document()
    doc.core_properties.title = "RPH 2027 Matematik SJKC Tahun 2"
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin, section.bottom_margin = Cm(1.55), Cm(1.5)
    section.left_margin = section.right_margin = Cm(1.65)
    section.footer_distance = Cm(0.8)
    styles(doc)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run("CikguLaju AI  ·  数学二年级  ·  Matematik SJKC Tahun 2").font.size = Pt(8)

    for lesson, activity in zip(lessons, activities, strict=True):
        if lesson["pdp"] > 1:
            doc.add_page_break()
        p = doc.add_paragraph(f"PdP {lesson['pdp']:03}  ·  数学二年级  ·  RPH 2027", "Lesson number")
        p.paragraph_format.space_after = Pt(4)
        p = doc.add_paragraph(lesson["topic"], "Lesson title")
        p.paragraph_format.space_after = Pt(6)
        p = doc.add_paragraph(f"Unit {lesson['unit_number']}  ·  {lesson['unit']}")
        p.runs[0].bold = True
        p.paragraph_format.space_after = Pt(7)
        p = doc.add_paragraph("日期 Tarikh ________  |  时间 Masa ________  |  班级 Kelas ________  |  学生人数 Bilangan murid ____  |  60 分钟")
        p.paragraph_format.space_after = Pt(22)
        table = doc.add_table(rows=0, cols=2)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        table.columns[0].width, table.columns[1].width = Cm(3.55), Cm(14.15)
        references = f"课本 J{lesson['textbook_volume']} {lesson['textbook_pages']}   ·   活动本 {lesson['activity_book']}"
        codes = f"SK {'、'.join(lesson['sk'])}    SP {'、'.join(lesson['sp'])}"
        table_row(table, "课程标准及参考", (("", codes), ("", references)))
        table_row(table, "学习目标", (("", lesson["focus"]),))
        table_row(table, "导入\n6 分钟", (("", activity["induction"]),))
        table_row(table, "主要教学活动\n35 分钟", (
            ("活动 1 教师", activity["teacher"]), ("活动 2 学生", activity["pupils"]),
        ))
        table_row(table, "巩固与课堂评估\n14 分钟", (("活动 3 PBD", activity["assessment"]),))
        table_row(table, "总结\n5 分钟", (("", activity["closure"]),))
        table_row(table, "教具", (("", activity["materials"]),))
        p = doc.add_paragraph("教学反思  Refleksi", "Lesson label")
        p.paragraph_format.space_before = Pt(11)
    doc.save(HERE / f"{STEM}.docx")


if __name__ == "__main__":
    build()
