"""Resolve and render the published Year 2 SK DLP lesson plans."""

from datetime import date
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
    math_options = {"mathematics": True, "teacher": teacher} if subject == "MATH_DLP" else {}
    if fmt == "word":
        _word(output, heading, details, activities, reflection, **math_options)
    elif fmt == "pdf":
        _pdf(output, heading, details, activities, reflection, **math_options)
    else:
        raise ValueError("Unsupported DLP format")
    return output.getvalue()


def _math_layout(heading, details, activities, teacher):
    """Map the authored Mathematics lesson to the original three-table RPH."""
    english = heading[0] == "Daily Lesson Plan"
    title = heading[0].upper()
    teacher = teacher or {}
    day = ""
    display_date = teacher.get("date") or ""
    try:
        year, month, number = (display_date.split("-") if "-" in display_date
                               else reversed(display_date.split("/")))
        lesson_date = date(int(year), int(month), int(number))
        display_date = lesson_date.strftime("%d/%m/%Y")
        days = (("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
                if english else ("Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad"))
        day = days[lesson_date.weekday()]
    except ValueError:
        pass
    labels = (("Date", "Day", "Time", "Class", "Number of pupils", "Topic") if english
              else ("Tarikh", "Hari", "Masa", "Kelas", "Bilangan Murid", "Tajuk"))
    time = re.sub(r"\s*[-–—]\s*", " - ", teacher.get("time") or "")
    values = (display_date, day, time, teacher.get("class"),
              teacher.get("students"), heading[2])
    year_label = re.search(r"\b(?:Year|Tahun) [1-6](?: SK)?\b", heading[1])[0]
    fields = [("Subject" if english else "Mata Pelajaran",
               "Mathematics (DLP)" if english else "Matematik"),
              ("Year" if english else "Tahun/Tingkatan", year_label)]
    fields.extend((key, value or "____________________") for key, value in zip(labels, values))
    for label, value in details:
        if label in {"Maklumat kelas", "Class / date / time"}:
            continue
        if label == "SK / SP" and " · SP " in value:
            sk, _, sp = value.partition(" · SP ")
            fields.extend([("Standard Kandungan", sk), ("Standard Pembelajaran", "SP " + sp)])
        else:
            fields.append((label, value))

    def actions(teacher_action, pupil_action):
        teacher_label, pupil_label = ("Teacher", "Pupils") if english else ("Guru", "Murid")
        return f"{teacher_label}: {teacher_action}\n{pupil_label}: {pupil_action}"

    def phase_title(phase):
        name, sep, duration = phase.replace("\n", " · ").rpartition(" · ")
        return f"{name.replace(' · ', ' – ')} ({duration})" if sep else phase

    header = (("Phase / Time", "Teaching and Learning Activities", "Notes") if english
              else ("Fasa / Masa", "Aktiviti Pengajaran & Pembelajaran", "Catatan"))
    main_heading = "Main Activities" if english else "Aktiviti Utama"
    induction, *main, closure = activities[1:]
    blocks = []
    for phase, teacher_action, pupil_action in main:
        blocks.extend(((phase_title(phase), True), (actions(teacher_action, pupil_action), False)))
    phases = [header, (phase_title(induction[0]), actions(*induction[1:]), ""),
              (main_heading, tuple(blocks), ""),
              (phase_title(closure[0]), actions(*closure[1:]), "")]
    return (title, *heading[1:]), fields, phases


def _cell_lines(value, bold):
    if isinstance(value, str):
        return [(line, bold) for line in value.split("\n")]
    return [(line, heading) for block, heading in value for line in block.split("\n")]


def _word(output, heading, details, activities, reflection, *, compact=False,
          mathematics=False, teacher=None):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Mm, Pt, RGBColor

    if mathematics:
        heading, details, activities = _math_layout(heading, details, activities, teacher)
    doc = Document()
    doc.core_properties.title = f"{heading[0]} · {heading[2]}"
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.left_margin = section.right_margin = Mm(14)
    section.top_margin = section.bottom_margin = Mm(15)
    if mathematics:
        section.left_margin = section.right_margin = Mm(11)
        section.top_margin = section.bottom_margin = Mm(9)
        section.footer_distance = Mm(4)

    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(9 if compact else 10)
    normal.paragraph_format.space_after = Pt(3)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.line_spacing = 1.08
    if mathematics:
        normal.font.name, normal.font.size = "Arial", Pt(8.5 if compact else 9)
        normal.paragraph_format.space_after = Pt(0)
        normal.paragraph_format.line_spacing = 1.0
    title = doc.styles["Title"]
    title.font.name, title.font.size = "Calibri", Pt(20)
    title.font.bold, title.font.color.rgb = True, RGBColor(0, 0, 0)
    title.paragraph_format.space_after = Pt(3)
    properties = title.element.get_or_add_pPr()
    border = properties.find(qn("w:pBdr"))
    if border is not None:
        properties.remove(border)
    title_paragraph = doc.add_paragraph(heading[0], "Title")
    if mathematics:
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.font.name, title.font.size = "Arial", Pt(12)
        title_paragraph.paragraph_format.space_after = Pt(5)
    else:
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
                bold = j == 0 or (header and i == 0)
                if bold and not mathematics:
                    shading = OxmlElement("w:shd")
                    shading.set(qn("w:fill"), "E8F0F2")
                    cell._tc.get_or_add_tcPr().append(shading)
                paragraph = cell.paragraphs[0]
                padding = 1 if mathematics else (2 if compact else 3)
                paragraph.paragraph_format.space_before = Pt(padding)
                paragraph.paragraph_format.space_after = Pt(padding)
                if mathematics:
                    if header and i == 0:
                        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for index, (line, strong) in enumerate(_cell_lines(value, bold)):
                        if index:
                            paragraph.add_run().add_break()
                        paragraph.add_run(line).bold = strong
                else:
                    paragraph.add_run(value).bold = bold

    def gap():
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = Pt(8)

    fields_width = (48, 124) if mathematics else (36, 146)
    steps_width = (32, 112, 28) if mathematics else (36, 73, 73)
    table(details, fields_width)
    gap()
    table(activities, steps_width, header=True)
    gap()
    table(reflection, fields_width)
    if mathematics:
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer.add_run("CikguLaju AI  •  ").font.size = Pt(7.5)
        page = OxmlElement("w:fldSimple")
        page.set(qn("w:instr"), "PAGE")
        footer._p.append(page)
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


def _pdf(output, heading, details, activities, reflection, *, compact=False,
         mathematics=False, teacher=None):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import BaseDocTemplate, Frame, KeepInFrame, PageTemplate, Paragraph, Spacer, Table

    if mathematics:
        heading, details, activities = _math_layout(heading, details, activities, teacher)
    fallback_regular, fallback_bold = _pdf_fonts()
    regular, bold = ("Helvetica", "Helvetica-Bold") if mathematics else (fallback_regular, fallback_bold)
    font_size = 8.25 if mathematics else 9
    leading = (9.35 if compact else 9.9) if mathematics else (11 if compact else 12)
    body = ParagraphStyle("DLP body", fontName=regular, fontSize=font_size, leading=leading)
    label = ParagraphStyle("DLP label", parent=body, fontName=bold)
    title = ParagraphStyle("DLP title", parent=label, fontSize=19, leading=23, spaceAfter=3)
    topic = ParagraphStyle("DLP topic", parent=label, fontSize=12, leading=16, spaceBefore=2)
    if mathematics:
        title.fontSize, title.leading, title.alignment = 12, 15, TA_CENTER
    def paragraph(value, style):
        lines = _cell_lines(value, False)
        formatted = []
        for line, strong in lines:
            font = bold if strong else style.fontName
            if mathematics and fallback_regular != "Helvetica" and not line.isascii():
                try:
                    line.encode("cp1252")
                except UnicodeEncodeError:
                    font = fallback_bold if strong or style.fontName == bold else fallback_regular
            elif regular == "Helvetica":
                line = line.replace("ℓ", "L").replace("−", "–")
            line = escape(line)
            formatted.append(f'<font name="{font}">{line}</font>' if font != style.fontName else line)
        return Paragraph("<br/>".join(formatted), style)

    def table(rows, widths, header=False):
        cells = [[paragraph(value, label if j == 0 or (header and i == 0) else body)
                  for j, value in enumerate(row)] for i, row in enumerate(rows)]
        result = Table(cells, colWidths=[width * mm for width in widths], repeatRows=int(header))
        padding = 2.5 if mathematics else (3 if compact else 4)
        commands = [
            ("GRID", (0, 0), (-1, -1), 0.5 if mathematics else 0.45,
             colors.black if mathematics else colors.HexColor("#859298")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), padding),
            ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
        ]
        if not mathematics:
            commands.append(("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F0F2")))
            if header:
                commands.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F0F2")))
        result.setStyle(commands)
        return result

    def footer(canvas, document):
        canvas.setFont("Helvetica", 7.5)
        canvas.drawCentredString(A4[0] / 2, 5 * mm, f"CikguLaju AI  •  {document.page}")

    doc = BaseDocTemplate(output, pagesize=A4, title=f"{heading[0]} · {heading[2]}")
    frame = Frame(14 * mm, 11 * mm if mathematics else 15 * mm,
                  182 * mm, 274 * mm if mathematics else 267 * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    if mathematics:
        doc.addPageTemplates(PageTemplate("RPH A4", frames=[frame], onPage=footer))
    else:
        doc.addPageTemplates(PageTemplate("DLP A4", frames=[frame]))
    opening = [paragraph(heading[0], title)]
    if not mathematics:
        opening.extend([paragraph(heading[1], body), paragraph(heading[2], topic)])
    fields_width = (48, 124) if mathematics else (36, 146)
    steps_width = (32, 112, 28) if mathematics else (36, 73, 73)
    story = [
        *opening,
        Spacer(1, 8),
        table(details, fields_width),
        Spacer(1, 8),
        table(activities, steps_width, header=True),
        Spacer(1, 8),
        table(reflection, fields_width),
    ]
    if mathematics:
        story = [KeepInFrame(182 * mm, 274 * mm, story, mode="shrink")]
    doc.build(story)
