"""Resolve and render the published Year 2 SK DLP lesson plans."""

from functools import lru_cache
from io import BytesIO
import json
from pathlib import Path
from xml.sax.saxutils import escape

SUBJECTS = {"SCIENCE_DLP": "Science", "MATH_DLP": "Mathematics"}


@lru_cache(maxsize=1)
def catalog():
    path = Path(__file__).resolve().parent / "data" / "dlp_year2_review.json"
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def resolve(year, subject, unit_id, lesson_id):
    if type(year) is not int or year != 2 or subject not in SUBJECTS:
        return None
    for unit in catalog()[subject]:
        if unit["id"] == unit_id:
            for lesson in unit["lessons"]:
                if lesson["id"] == lesson_id:
                    return unit, lesson
    return None


def filename(lesson_id, fmt):
    return f"CIKGULAJU_RPH_{lesson_id}." + ("docx" if fmt == "word" else "pdf")


def render(subject, unit, lesson, fmt, teacher):
    heading = (
        "Daily Lesson Plan",
        f"{SUBJECTS[subject]} (DLP) · Year 2 SK",
        lesson["title"],
    )
    class_details = (
        ("Class", teacher["class"]),
        ("Date", teacher["date"]),
        ("Time", teacher["time"]),
        ("Pupils", teacher["students"]),
    )
    details = [
        ("Unit", unit["title"]),
        ("Lesson / PdP", lesson["id"]),
        ("Class / date / time", "   ·   ".join(
            f"{label}: {value or '________'}" for label, value in class_details)),
        ("Standards", lesson["standards"]),
        ("Book references", lesson["references"]),
        ("Learning objective", lesson["objective"]),
        ("Materials", lesson["materials"]),
    ]
    activities = [("Phase", "Teacher", "Pupils"), *lesson["phases"]]
    reflection = [("Reflection", teacher.get("reflection") or lesson["reflection"])]
    output = BytesIO()
    if fmt == "word":
        _word(output, heading, details, activities, reflection)
    elif fmt == "pdf":
        _pdf(output, heading, details, activities, reflection)
    else:
        raise ValueError("Unsupported DLP format")
    return output.getvalue()


def _word(output, heading, details, activities, reflection):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Mm, Pt, RGBColor

    doc = Document()
    doc.core_properties.title = f"{heading[0]} · {heading[2]}"
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.left_margin = section.right_margin = Mm(14)
    section.top_margin = section.bottom_margin = Mm(15)

    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(10)
    normal.paragraph_format.space_after = Pt(3)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.line_spacing = 1.08
    title = doc.styles["Title"]
    title.font.name, title.font.size = "Calibri", Pt(20)
    title.font.bold, title.font.color.rgb = True, RGBColor(0, 0, 0)
    title.paragraph_format.space_after = Pt(3)
    properties = title.element.get_or_add_pPr()
    border = properties.find(qn("w:pBdr"))
    if border is not None:
        properties.remove(border)
    doc.add_paragraph(heading[0], "Title")
    doc.add_paragraph(heading[1])
    topic = doc.add_paragraph()
    topic.add_run(heading[2]).bold = True
    topic.paragraph_format.space_after = Pt(8)

    def table(rows, widths, header=False):
        element = doc.add_table(rows=0, cols=len(widths))
        element.style = "Table Grid"
        element.autofit = False
        element.alignment = WD_TABLE_ALIGNMENT.CENTER
        for column, width in zip(element.columns, widths):
            column.width = Mm(width)
        for i, row in enumerate(rows):
            line = element.add_row()
            line._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            for j, (cell, value, width) in enumerate(zip(line.cells, row, widths)):
                cell.width = Mm(width)
                if j == 0 or (header and i == 0):
                    shading = OxmlElement("w:shd")
                    shading.set(qn("w:fill"), "E8F0F2")
                    cell._tc.get_or_add_tcPr().append(shading)
                paragraph = cell.paragraphs[0]
                paragraph.paragraph_format.space_before = Pt(3)
                paragraph.paragraph_format.space_after = Pt(3)
                paragraph.add_run(value).bold = j == 0 or (header and i == 0)

    def gap():
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = Pt(8)

    table(details, (36, 146))
    gap()
    table(activities, (36, 73, 73), header=True)
    gap()
    table(reflection, (36, 146))
    doc.save(output)


@lru_cache(maxsize=1)
def _pdf_fonts():
    from reportlab import rl_config
    from reportlab.pdfbase.pdfmetrics import registerFont
    from reportlab.pdfbase.ttfonts import TTFont

    paths = (
        Path("/usr/share/fonts/truetype/dejavu"),
        *(Path(directory) for directory in rl_config.TTFSearchPath),
    )
    for directory in paths:
        if (directory / "DejaVuSans.ttf").is_file() and (directory / "DejaVuSans-Bold.ttf").is_file():
            registerFont(TTFont("DLP-Regular", str(directory / "DejaVuSans.ttf")))
            registerFont(TTFont("DLP-Bold", str(directory / "DejaVuSans-Bold.ttf")))
            return "DLP-Regular", "DLP-Bold"
    return "Helvetica", "Helvetica-Bold"


def _pdf(output, heading, details, activities, reflection):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Frame, PageTemplate, BaseDocTemplate, Paragraph, Spacer, Table

    regular, bold = _pdf_fonts()
    body = ParagraphStyle("DLP body", fontName=regular, fontSize=9, leading=12)
    label = ParagraphStyle("DLP label", parent=body, fontName=bold)
    title = ParagraphStyle("DLP title", parent=label, fontSize=19, leading=23, spaceAfter=3)
    topic = ParagraphStyle("DLP topic", parent=label, fontSize=12, leading=16, spaceBefore=2)

    def paragraph(value, style):
        if regular == "Helvetica":
            value = value.replace("ℓ", "L").replace("−", "–")
        return Paragraph(escape(value).replace("\n", "<br/>"), style)

    def table(rows, widths, header=False):
        cells = [[paragraph(value, label if j == 0 or (header and i == 0) else body)
                  for j, value in enumerate(row)] for i, row in enumerate(rows)]
        result = Table(cells, colWidths=[width * mm for width in widths], repeatRows=int(header))
        commands = [
            ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#859298")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F0F2")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        if header:
            commands.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F0F2")))
        result.setStyle(commands)
        return result

    doc = BaseDocTemplate(output, pagesize=A4, title=f"{heading[0]} · {heading[2]}")
    frame = Frame(14 * mm, 15 * mm, 182 * mm, 267 * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate("DLP A4", frames=[frame]))
    doc.build([
        paragraph(heading[0], title),
        paragraph(heading[1], body),
        paragraph(heading[2], topic),
        Spacer(1, 8),
        table(details, (36, 146)),
        Spacer(1, 8),
        table(activities, (36, 73, 73), header=True),
        Spacer(1, 8),
        table(reflection, (36, 146)),
    ])
