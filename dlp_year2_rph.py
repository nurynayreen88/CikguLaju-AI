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


def _word(output, heading, details, activities, reflection, *, formal=False):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.shared import Mm, Pt
    from web.rph_document_style import style_word_table, word_gap, word_typography

    doc = Document()
    doc.core_properties.title = f"{heading[0]} · {heading[2]}"
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.left_margin = section.right_margin = Mm(14)
    section.top_margin = section.bottom_margin = Mm(14)
    word_typography(doc, 10.5)
    if formal:
        section.top_margin = section.bottom_margin = Mm(12)
        doc.styles["Normal"].paragraph_format.line_spacing = Pt(11.5)

    if formal:
        title = doc.add_paragraph(heading[0].upper(), "Title")
        title.paragraph_format.space_after = Pt(3)
        context = doc.add_paragraph(heading[1])
        topic = doc.add_paragraph()
        run = topic.add_run(heading[2])
        run.bold = True
        run.font.size = Pt(14)
        topic.paragraph_format.space_before = Pt(4)
        for paragraph in (title, context, topic):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        label = doc.add_paragraph()
        label.add_run(heading[0]).bold = True
        label.paragraph_format.space_after = Pt(3)
        context = doc.add_paragraph(heading[1])
        context.paragraph_format.space_after = Pt(4)
        title = doc.add_paragraph(heading[2], "Title")
        title.alignment = WD_ALIGN_PARAGRAPH.LEFT

    def section_label(text):
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_before = Pt(6)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.keep_with_next = True
        paragraph.add_run(text).bold = True

    def table(rows, widths, *, header=False, padding=55):
        element = doc.add_table(rows=0, cols=len(widths))
        for row in rows:
            line = element.add_row()
            line._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            for cell, value in zip(line.cells, row, strict=True):
                cell.paragraphs[0].add_run(value)
        style_word_table(element, widths, header=header, padding=padding)
        return element

    widths = (39, 143) if formal else (34, 148)
    if formal:
        section_label("MAKLUMAT PENGAJARAN")
    table(details, widths, padding=38 if formal else 55)
    if formal:
        section_label("LANGKAH PENGAJARAN DAN PEMBELAJARAN")
    else:
        word_gap(doc)
    table(activities, (32, 75, 75) if formal else (30, 76, 76), header=True,
          padding=46 if formal else 60)
    if formal:
        section_label("PENTAKSIRAN DAN REFLEKSI")
    else:
        word_gap(doc)
    tail = table(reflection, widths, padding=46 if formal else 55)
    for i, (name, _) in enumerate(reflection):
        if name.casefold() in ("refleksi", "reflection"):
            tail.rows[i].cells[0].merge(tail.rows[i].cells[1])
    doc.save(output)


def _pdf(output, heading, details, activities, reflection, *, formal=False):
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.colors import black
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Frame, PageTemplate, BaseDocTemplate, Paragraph, Spacer, Table
    from web.rph_document_style import pdf_box_style, pdf_fonts

    regular, bold, serif = pdf_fonts()
    body = ParagraphStyle("RPH body", fontName=regular, fontSize=10.5, leading=12.3, textColor=black)
    label = ParagraphStyle("RPH label", parent=body, fontName=bold)
    title = ParagraphStyle("RPH topic", parent=body, fontName=serif, fontSize=20, leading=22, spaceAfter=7)
    context = ParagraphStyle("RPH context", parent=body, spaceAfter=4)
    caption = ParagraphStyle("RPH caption", parent=label, fontSize=10, spaceAfter=3)
    section_label = ParagraphStyle("RPH section", parent=label, spaceBefore=6, spaceAfter=2,
                                   keepWithNext=True)

    def paragraph(value, style):
        return Paragraph(escape(value).replace("\n", "<br/>"), style)

    def table(rows, widths, *, header=False, padding=2.75, span_reflection=False):
        cells = []
        commands = pdf_box_style(padding)
        for index, row in enumerate(rows):
            if span_reflection and row[0].casefold() in ("refleksi", "reflection"):
                cells.append([[paragraph(row[0], label), paragraph(row[1], body)], ""])
                commands.append(("SPAN", (0, index), (1, index)))
            else:
                cells.append([paragraph(value, label if col == 0 or (header and index == 0) else body)
                              for col, value in enumerate(row)])
        return Table(cells, colWidths=[width * mm for width in widths], repeatRows=int(header), style=commands)

    doc = BaseDocTemplate(output, pagesize=A4, title=f"{heading[0]} · {heading[2]}")
    margin = 12 if formal else 14
    frame = Frame(14 * mm, margin * mm, 182 * mm, (297 - 2 * margin) * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate("RPH A4", frames=[frame]))
    widths = (39, 143) if formal else (34, 148)
    if formal:
        title.alignment, title.spaceAfter = TA_CENTER, 3
        context.alignment = TA_CENTER
        topic = ParagraphStyle("RPH formal topic", parent=label, fontSize=14, leading=16, alignment=TA_CENTER)
        story = [paragraph(heading[0].upper(), title), paragraph(heading[1], context),
                 paragraph(heading[2], topic), paragraph("MAKLUMAT PENGAJARAN", section_label)]
    else:
        story = [paragraph(heading[0], caption), paragraph(heading[1], context), paragraph(heading[2], title)]
    story.extend([
        table(details, widths, padding=2 if formal else 2.75),
        paragraph("LANGKAH PENGAJARAN DAN PEMBELAJARAN", section_label) if formal else Spacer(1, 6),
        table(activities, (32, 75, 75) if formal else (30, 76, 76), header=True, padding=2.5 if formal else 3),
        paragraph("PENTAKSIRAN DAN REFLEKSI", section_label) if formal else Spacer(1, 6),
        table(reflection, widths, span_reflection=True, padding=2.5 if formal else 2.75),
    ])
    doc.build(story)
