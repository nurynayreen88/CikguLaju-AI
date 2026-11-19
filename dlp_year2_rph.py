"""Resolve and render the published Year 2 SK DLP lesson plans."""

from functools import lru_cache
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from xml.sax.saxutils import escape

SUBJECTS = {"SCIENCE_DLP": "Science", "MATH_DLP": "Mathematics"}


@lru_cache(maxsize=1)
def catalog():
    path = Path(__file__).resolve().parent / "data" / "dlp_year2_review.json"
    with path.open(encoding="utf-8") as source:
        return json.load(source)


@lru_cache(maxsize=2)
def rpt_lessons(subject):
    subject_name = SUBJECTS[subject].lower()
    path = Path(__file__).resolve().parent / "rpt_2027" / "dlp" / f"{subject_name}_year2_rph_rpt_2027.json"
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def science_rpt_lessons():
    return rpt_lessons("SCIENCE_DLP")


@lru_cache(maxsize=1)
def year3_science_catalog():
    path = Path(__file__).resolve().parent / "staging" / "dlp" / "year3" / "science_2027.json"
    with path.open(encoding="utf-8") as source:
        data = json.load(source)
    rpt = path.parents[3] / "rpt_2027" / "dlp" / "CikguLaju_RPT_DLP_2027_Science_Year_3.docx"
    if sha256(rpt.read_bytes()).hexdigest() != data["rpt_sha256"]:
        raise ValueError("The Science Year 3 RPT has changed.")
    plans = data["plans"]
    units = {}
    for plan in plans:
        title = plan["unit"]
        unit_number = re.match(r"Unit (\d+) ", title)
        unit_id = unit_number[1].zfill(2) if unit_number else "review"
        unit = units.setdefault(unit_id, {"id": unit_id, "title": title, "lessons": []})
        unit["lessons"].append({
            "id": plan["id"],
            "title": plan["title"],
            "year": 3,
            "unit_title": title,
            "numbered_label": plan["label"],
            "minutes": plan["minutes"],
            "rpt_dates": plan["rpt_dates"],
            "standards": " · ".join(plan["standards"]),
            "references": " · ".join(line.replace("TB ", "Textbook ").replace("AB ", "Activity Book ")
                                     for line in plan["references"]),
            "objective": plan["objective"],
            "materials": plan["materials"],
            "phases": [[f"{phase['phase']} · {phase['minutes']} min", phase["teacher"], phase["pupils"]]
                       for phase in plan["phases"]],
            "reflection": f"___ / ___ pupils met the objective. {plan['follow_up']}",
        })
    return [*(units[key] for key in sorted(units) if key != "review"), units["review"]]


def subject_units(year, subject):
    if type(year) is not int or subject not in SUBJECTS:
        return ()
    if year == 2:
        return catalog()[subject]
    if year == 3 and subject == "SCIENCE_DLP":
        return year3_science_catalog()
    return ()


def resolve(year, subject, unit_id, lesson_id):
    for unit in subject_units(year, subject):
        if unit["id"] == unit_id:
            for lesson in unit["lessons"]:
                if lesson["id"] == lesson_id:
                    return unit, lesson
    return None


def filename(lesson_id, fmt):
    return f"CIKGULAJU_RPH_{lesson_id}." + ("docx" if fmt == "word" else "pdf")


def render(subject, unit, lesson, fmt, teacher):
    year = lesson.get("year", 2)
    phases = lesson["phases"]
    if "numbered_label" in lesson:
        minutes = lesson["minutes"]
        lesson_label = f"{lesson['numbered_label']} · {minutes} min"
    else:
        scheduled = rpt_lessons(subject)[lesson["id"]]
        minutes = scheduled["minutes"]
        lesson_label = f"Lesson {scheduled['number']:02d} · {minutes} min"
    if (year == 2 and subject == "SCIENCE_DLP" and minutes == 30
            and not lesson_label.startswith("Review ")):
        phases = [
            (f"{phase.split(' · ', 1)[0]} · {duration} min", teacher_action, pupils_action)
            for (phase, teacher_action, pupils_action), duration in zip(
                phases, (3, 15, 9, 3), strict=True
            )
        ]
    heading = (
        "Daily Lesson Plan",
        f"{SUBJECTS[subject]} (DLP) · Year {year} SK",
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
        ("Lesson / PdP", lesson_label),
        ("Class / date / time", "   ·   ".join(
            f"{label}: {value or '________'}" for label, value in class_details)),
        ("Standards", lesson["standards"]),
        ("Teaching source" if lesson_label.startswith("Review ") and year == 2 else "Book references",
         lesson["references"]),
        ("Learning objective", lesson["objective"]),
        ("Materials", lesson["materials"]),
    ]
    if "rpt_dates" in lesson:
        details.insert(2, ("RPT 2027 dates", " · ".join(lesson["rpt_dates"])))
    activities = [("Phase", "Teacher", "Pupils"), *phases]
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
    from web.rph_document_style import INK, TEAL, style_word_table

    doc = Document()
    doc.core_properties.title = f"{heading[0]} · {heading[2]}"
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.left_margin = section.right_margin = Mm(14)
    section.top_margin = section.bottom_margin = Mm(15)

    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(9.75)
    normal.paragraph_format.space_after = Pt(3)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.line_spacing = 1.08
    title = doc.styles["Title"]
    title.font.name, title.font.size = "Calibri", Pt(18)
    title.font.bold, title.font.color.rgb = True, RGBColor(0, 0, 0)
    title.paragraph_format.space_after = Pt(3)
    properties = title.element.get_or_add_pPr()
    border = properties.find(qn("w:pBdr"))
    if border is not None:
        properties.remove(border)
    doc.add_paragraph(heading[0], "Title")
    subtitle = doc.add_paragraph()
    subtitle.add_run(heading[1]).font.color.rgb = RGBColor.from_string(TEAL)
    topic = doc.add_paragraph()
    topic_text = topic.add_run(heading[2])
    topic_text.bold = True
    topic_text.font.color.rgb = RGBColor.from_string(INK)
    topic_text.font.size = Pt(12)
    topic.paragraph_format.space_after = Pt(8)

    def table(rows, widths, header=False):
        element = doc.add_table(rows=0, cols=len(widths))
        element.style = "Table Grid"
        element.autofit = False
        element.alignment = WD_TABLE_ALIGNMENT.CENTER
        for row in rows:
            line = element.add_row()
            line._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            for cell, value in zip(line.cells, row, strict=True):
                paragraph = cell.paragraphs[0]
                paragraph.paragraph_format.space_before = Pt(2.3)
                paragraph.paragraph_format.space_after = Pt(2.3)
                paragraph.add_run(value)
        style_word_table(element, widths, header=header)

    def gap():
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = Pt(8)

    table(details, (36, 146))
    gap()
    table(activities, (34, 74, 74), header=True)
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
    from web.rph_document_style import GRID, INK, MIST, NAVY, STRIPE, TEAL

    regular, bold = _pdf_fonts()
    body = ParagraphStyle("DLP body", fontName=regular, fontSize=9, leading=11.6, textColor=colors.HexColor("#" + INK))
    label = ParagraphStyle("DLP label", parent=body, fontName=bold)
    title = ParagraphStyle("DLP title", parent=label, fontSize=18, leading=23, spaceAfter=3, textColor=colors.black)
    subtitle = ParagraphStyle("DLP subtitle", parent=body, textColor=colors.HexColor("#" + TEAL))
    header_label = ParagraphStyle("DLP header", parent=label, textColor=colors.white)
    topic = ParagraphStyle("DLP topic", parent=label, fontSize=12, leading=16, spaceBefore=2)

    def paragraph(value, style):
        if regular == "Helvetica":
            value = value.replace("ℓ", "L").replace("−", "–")
        return Paragraph(escape(value).replace("\n", "<br/>"), style)

    def table(rows, widths, header=False):
        cells = [[paragraph(value, header_label if header and i == 0 else label if j == 0 else body)
                  for j, value in enumerate(row)] for i, row in enumerate(rows)]
        result = Table(cells, colWidths=[width * mm for width in widths], repeatRows=int(header))
        commands = [
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#" + GRID)),
            ("ROWBACKGROUNDS", (1, 0), (-1, -1), [colors.white, colors.HexColor("#" + STRIPE)]),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#" + MIST)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        if header:
            commands.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#" + NAVY)))
        else:
            commands.append(("LINEABOVE", (0, 0), (-1, 0), 1.5, colors.HexColor("#" + TEAL)))
        result.setStyle(commands)
        return result

    doc = BaseDocTemplate(output, pagesize=A4, title=f"{heading[0]} · {heading[2]}")
    frame = Frame(14 * mm, 15 * mm, 182 * mm, 267 * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate("DLP A4", frames=[frame]))
    doc.build([
        paragraph(heading[0], title),
        paragraph(heading[1], subtitle),
        paragraph(heading[2], topic),
        Spacer(1, 8),
        table(details, (36, 146)),
        Spacer(1, 8),
        table(activities, (34, 74, 74), header=True),
        Spacer(1, 8),
        table(reflection, (36, 146)),
    ])
