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
_DLP_SOURCES = Path(__file__).resolve().parent / "staging" / "dlp"
_LEARNING_STANDARD = re.compile(r"\b(\d+\.\d+\.\d+)(\([iv]+\)(?:, \([iv]+\))*)?")


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


@lru_cache(maxsize=3)
def _standard_descriptions(year, subject):
    source = _DLP_SOURCES / f"year{year}" / f"{SUBJECTS[subject].lower()}_standard_descriptions.json"
    return json.loads(source.read_text(encoding="utf-8"))


def _standard_rows(descriptions, ls_codes):
    cs_codes = dict.fromkeys(code.rsplit(".", 1)[0] for code in ls_codes)
    learning = descriptions["ls"] | descriptions.get("parts", {})
    return [
        ("Content Standards", "\n".join(f"{code} {descriptions['cs'][code]}" for code in cs_codes)),
        ("Learning Standards", "\n".join(f"{code} {learning[code]}" for code in ls_codes)),
    ]


def mathematics_standard_rows(year, standards):
    """Build the RPH fields from the same LS codes recorded in the RPT."""
    descriptions = _standard_descriptions(year, "MATH_DLP")
    codes = re.findall(r"\b(\d+\.\d+\.\d+)(?:[ \t]*(\([iv]+\)(?:,[ \t]*\([iv]+\))*))?",
                       standards)
    if not codes:
        raise ValueError("Mathematics DLP lesson lacks a Learning Standard")
    selected = dict.fromkeys(
        f"{code}{part}" for code, parts in codes for part in re.split(r",\s*", parts)
    )
    return _standard_rows(descriptions, selected)


@lru_cache(maxsize=1)
def year3_science_catalog():
    path = _DLP_SOURCES / "year3" / "science_2027.json"
    with path.open(encoding="utf-8") as source:
        data = json.load(source)
    rpt = path.parents[3] / "rpt_2027" / "dlp" / "CikguLaju_RPT_DLP_2027_Science_Year_3.docx"
    if sha256(rpt.read_bytes()).hexdigest() != data["rpt_sha256"]:
        raise ValueError("The Science Year 3 RPT has changed.")
    descriptions = _standard_descriptions(3, "SCIENCE_DLP")
    plans = data["plans"]
    units = {}
    for plan in plans:
        title = plan["unit"]
        unit_number = re.match(r"Unit (\d+) ", title)
        unit_id = unit_number[1].zfill(2) if unit_number else "review"
        if unit_id == "review":
            ls_codes = descriptions["review_ls"][plan["id"]]
        else:
            ls_codes = re.findall(r"\b\d+\.\d+\.\d+\b", plan["standards"][1])
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
            "standard_rows": _standard_rows(descriptions, ls_codes),
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


def science_class_fields(teacher, *, english, prefix=""):
    labels = (("Date", "Time", "Class", "Number of pupils") if english
              else ("Tarikh", "Masa", "Kelas", "Bilangan Murid"))
    keys = ("date", "time", "class", "students")
    return [(label, str(teacher.get(prefix + key) or "").strip())
            for key, label in zip(keys, labels)]


def render(subject, unit, lesson, fmt, teacher):
    year = lesson.get("year", 2)
    lesson_label = lesson.get("numbered_label")
    if not lesson_label:
        scheduled = rpt_lessons(subject)[lesson["id"]]
        lesson_label = f"Lesson {scheduled['number']:02d}"
    heading = (
        "Daily Lesson Plan",
        f"{SUBJECTS[subject]} (DLP) · Year {year} SK",
        lesson["title"],
    )
    mathematics = subject == "MATH_DLP"
    class_fields = [] if mathematics else science_class_fields(teacher, english=True)
    if year == 2:
        ls_codes = [f"{code}{part}" for code, parts in _LEARNING_STANDARD.findall(lesson["standards"])
                    for part in parts.split(", ")]
        standards = _standard_rows(_standard_descriptions(year, subject), ls_codes)
    else:
        standards = lesson.get("standard_rows", [("Standards", lesson["standards"])])
    details = [
        ("Unit", unit["title"]),
        ("Lesson / PdP", lesson_label),
        *class_fields,
        *standards,
        ("Teaching source" if lesson_label.startswith("Review ") and year == 2 else "Book references",
         lesson["references"]),
        ("Learning objective", lesson["objective"]),
        ("Materials", lesson["materials"]),
    ]
    if "rpt_dates" in lesson:
        details.insert(2, ("RPT 2027 dates", " · ".join(lesson["rpt_dates"])))
    activities = [("Phase", "Teacher", "Pupils"), *lesson["phases"]]
    reflection = [("Reflection", teacher.get("reflection") or lesson["reflection"])]
    # Shared CikguLaju RPH generator: curriculum extraction stays in DLP,
    # while Word and PDF pass through one source-safe rendering entrance.
    from web.rph_unified_engine import render_structured_rph
    math_options = {"mathematics": True, "teacher": teacher} if mathematics else {}
    return render_structured_rph(
        source="dlp", fmt=fmt, heading=heading, details=details,
        activities=activities, footer=reflection, **math_options,
    )


_DURATION_SUFFIX = re.compile(r"(?:[ \t]*·[ \t]*|\n)\d+[ \t]+min(?:it)?[ \t]*$")
_SESSION_LABELS = {
    "Lesson / PdP": "Lesson / PdP",
    "Lesson / tempoh": "Lesson",
    "PdP / Tempoh": "PdP",
    "Nombor dan tempoh": "Nombor PdP",
}
_RPT_DATE_FIELDS = {"Tarikh RPT", "Julat RPT", "RPT 2027 dates", "RPT date ranges"}
_MATHEMATICS_FILL = "DCEBFA"
_SCIENCE_FILL = "DFF1E3"
# Visual master: BM SK KP2027 Tahun 1, neutral small teacher-info panel.
from web.rph_unified_engine import TEACHER_PANEL_FILL as _TEACHER_PANEL_FILL
_FIELD_WIDTHS = (48, 134)
_ACTIVITY_WIDTHS = (32, 122, 28)


def _rph_display_rows(details, activities):
    """Keep class details and teaching content on the RPH handout."""
    fields = [
        (_SESSION_LABELS[label], _DURATION_SUFFIX.sub("", value)) if label in _SESSION_LABELS
        else (label, value)
        for label, value in details if label not in _RPT_DATE_FIELDS
    ]
    phases = [(_DURATION_SUFFIX.sub("", label), teacher, pupils)
              for label, teacher, pupils in activities]
    return fields, phases


def _math_details(heading, details, teacher):
    """Display Mathematics lesson and class details in the established fields."""
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
    time = re.sub(r"\s*[-–—]\s*", " - ", (teacher.get("time") or "").strip())
    values = (display_date, day, time, teacher.get("class"),
              teacher.get("students"), heading[2])
    year_label = re.search(r"\b(?:Year|Tahun) [1-6](?: SK)?\b", heading[1])[0]
    fields = [("Subject" if english else "Mata Pelajaran",
               "Mathematics (DLP)" if english else "Matematik"),
              ("Year" if english else "Tahun/Tingkatan", year_label)]
    fields.extend((key, str(value or "").strip()) for key, value in zip(labels, values))
    for label, value in details:
        if label in {"Maklumat kelas", "Class / date / time"}:
            continue
        if label == "SK / SP" and " · SP " in value:
            sk, _, sp = value.partition(" · SP ")
            fields.extend([("Standard Kandungan", sk), ("Standard Pembelajaran", "SP " + sp)])
        else:
            fields.append((label, value))
    return (title, *heading[1:]), fields


def _activity_table(activities, *, english):
    """Place both roles in the activity cell and leave room for notes."""
    teacher_label, pupil_label = ("Teacher", "Pupils") if english else ("Guru", "Murid")

    def actions(teacher_action, pupil_action):
        return f"{teacher_label}: {teacher_action}\n{pupil_label}: {pupil_action}"

    header = (("Phase", "Teaching and Learning Activities", "Notes") if english
              else ("Fasa", "Aktiviti Pengajaran & Pembelajaran", "Catatan"))
    main_heading = "Main Activities" if english else "Aktiviti Utama"
    induction, *main, closure = activities[1:]
    blocks = []
    for phase, teacher_action, pupil_action in main:
        activity_title = phase.replace("\n", " – ").replace(" · ", " – ")
        blocks.extend(((activity_title, True),
                       (actions(teacher_action, pupil_action), False)))
    return [header, (induction[0], actions(*induction[1:]), ""),
            (main_heading, tuple(blocks), ""),
            (closure[0], actions(*closure[1:]), "")]


def _cell_lines(value, bold):
    if isinstance(value, str):
        return [(line, bold) for line in value.split("\n")]
    return [(line, heading) for block, heading in value for line in block.split("\n")]


def _premium_header_payload(heading, details):
    """Move (never discard) teacher metadata into the approved small RIGHT panel.

    Source standards, activity steps, materials and reflections remain in their
    original order. The subject/year/topic already visible in the identity
    panel must not be repeated as separate curriculum rows.
    """
    english = heading[0].strip().casefold() == "daily lesson plan"
    aliases = {
        "class": "class", "kelas": "class",
        "date": "date", "tarikh": "date",
        "day": "day", "hari": "day",
        "time": "time", "masa": "time",
        "number of pupils": "students", "bilangan murid": "students",
        "bil. murid": "students",
    }
    redundant = {"subject", "mata pelajaran", "year", "tahun/tingkatan",
                 "topic", "tajuk"}
    values = {}
    remaining = []
    for label, value in details:
        clean = " ".join(label.casefold().split())
        if clean in aliases:
            values[aliases[clean]] = str(value or "")
        elif clean not in redundant:
            remaining.append((label, value))
    labels = (("Class", "Date", "Day", "Time", "Number of pupils") if english
              else ("Kelas", "Tarikh", "Hari", "Masa", "Bilangan Murid"))
    keys = ("class", "date", "day", "time", "students")
    # Do not invent a day for formats that did not have a day field.
    fields = [(label, values.get(key, "")) for label, key in zip(labels, keys)
              if key != "day" or "day" in values]
    return remaining, fields


def _separated_header_identity(heading):
    """Separate only source-authored subject / Year / topic in reviewed layouts.

    The exact original source phrases are kept; no new curriculum fields,
    values or teacher metadata are synthesized. Unsupported headings retain
    the established legacy layout.
    """
    if not isinstance(heading, (tuple, list)) or len(heading) != 3:
        return None
    subject, separator, year = str(heading[1]).rpartition(" · ")
    if not separator or not re.fullmatch(r"(?:Year|Tahun) [1-6](?: SK)?", year):
        return None
    english = str(heading[0]).strip().casefold() == "daily lesson plan"
    return (
        ("Subject" if english else "Mata Pelajaran", subject),
        ("Year" if english else "Tahun/Tingkatan", year),
        ("Topic" if english else "Tajuk", str(heading[2])),
    )


def _word(output, heading, details, activities, reflection, *, compact=False,
          mathematics=False, teacher=None, label_fill=None):
    from copy import deepcopy

    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Mm, Pt, RGBColor
    from web.rph_document_style import word_gap

    fill = label_fill or (_MATHEMATICS_FILL if mathematics else _SCIENCE_FILL)

    def shading(color=fill):
        element = OxmlElement("w:shd")
        element.set(qn("w:val"), "clear")
        element.set(qn("w:fill"), color)
        return element

    details, activities = _rph_display_rows(details, activities)
    from web.rph_supporting_fields_20261121 import supplement_details
    details = supplement_details(heading, details, activities, reflection)
    activities = _activity_table(activities, english=heading[0] == "Daily Lesson Plan")
    if mathematics:
        heading, details = _math_details(heading, details, teacher)
    details, teacher_fields = _premium_header_payload(heading, details)
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
    title.font.name, title.font.size = "Calibri", Pt(15)
    title.font.bold, title.font.color.rgb = True, RGBColor(0, 0, 0)
    title.paragraph_format.space_before = Pt(0)
    title.paragraph_format.line_spacing = 1.0
    properties = title.element.get_or_add_pPr()
    border = properties.find(qn("w:pBdr"))
    if border is not None:
        properties.remove(border)
    # The complete source title belongs at the centre ABOVE the top box.
    # No extra table or content is inserted for an unexpected heading.
    identity_fields = _separated_header_identity(heading)
    if identity_fields:
        title_p = doc.add_paragraph(str(heading[0]), style="Title")
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_p.paragraph_format.space_after = Pt(2)
    # One complete 182 mm A4 banner, exactly aligned to every table below.
    # Lesson identity remains at LEFT, the compact teacher panel at RIGHT.
    header = doc.add_table(rows=1, cols=2)
    header.style = "Table Grid"
    header.autofit = False
    header.alignment = WD_TABLE_ALIGNMENT.CENTER
    for column, width in zip(header.columns, (118, 64)):
        column.width = Mm(width)
    header_left, header_right = header.rows[0].cells
    for index, (cell, width) in enumerate(zip((header_left, header_right), (118, 64))):
        cell.width = Mm(width)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        # Recolor the existing small teacher cell only. Never insert, infer,
        # remove, or move teacher/curriculum fields to mimic the master.
        cell._tc.get_or_add_tcPr().append(
            shading(_TEACHER_PANEL_FILL if index == 1 else fill)
        )
    if identity_fields:
        for index, (label_text, value) in enumerate(identity_fields):
            paragraph = (header_left.paragraphs[0] if index == 0
                         else header_left.add_paragraph())
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(1)
            paragraph.paragraph_format.tab_stops.add_tab_stop(Mm(32))
            paragraph.add_run(label_text + ": ").bold = True
            paragraph.add_run("\t" + value)
    else:
        for index, text in enumerate(heading):
            paragraph = (header_left.paragraphs[0] if index == 0
                         else header_left.add_paragraph())
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            paragraph.paragraph_format.space_before = Pt(1)
            paragraph.paragraph_format.space_after = Pt(1)
            run = paragraph.add_run(str(text))
            run.bold = index in (0, 2)
            run.font.size = Pt(13 if index == 0 else 10)
    # All teacher labels and values start at the same X positions.
    for index, (label_text, value) in enumerate(teacher_fields):
        paragraph = (header_right.paragraphs[0] if index == 0
                     else header_right.add_paragraph())
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(1)
        if identity_fields:
            paragraph.paragraph_format.tab_stops.add_tab_stop(Mm(34))
        prefix = paragraph.add_run(label_text + ": ")
        prefix.bold = True
        paragraph.add_run(("\t" if identity_fields else "") + value)

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
                if bold:
                    cell._tc.get_or_add_tcPr().append(shading())
                paragraph = cell.paragraphs[0]
                padding = 1 if mathematics else (2 if compact else 3)
                paragraph.paragraph_format.space_before = Pt(padding)
                paragraph.paragraph_format.space_after = Pt(padding)
                if header and i == 0:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for index, (line, strong) in enumerate(_cell_lines(value, bold)):
                    if index:
                        paragraph.add_run().add_break()
                    paragraph.add_run(line).bold = strong

    word_gap(doc)
    table(details, _FIELD_WIDTHS)
    word_gap(doc)
    table(activities, _ACTIVITY_WIDTHS, header=True)
    word_gap(doc)
    table(reflection, _FIELD_WIDTHS)
    if mathematics:
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer.add_run("CikguLaju AI  •  ").font.size = Pt(7.5)
        page = OxmlElement("w:fldSimple")
        page.set(qn("w:instr"), "PAGE")
        footer._p.append(page)
    doc.save(output)


def _pdf(output, heading, details, activities, reflection, *, compact=False,
         mathematics=False, teacher=None, label_fill=None):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import BaseDocTemplate, Frame, KeepInFrame, PageTemplate, Paragraph, Spacer, Table
    from web.rph_document_style import pdf_box_style, pdf_fonts

    fill = colors.HexColor("#" + (label_fill or (_MATHEMATICS_FILL if mathematics else _SCIENCE_FILL)))
    details, activities = _rph_display_rows(details, activities)
    from web.rph_supporting_fields_20261121 import supplement_details
    details = supplement_details(heading, details, activities, reflection)
    activities = _activity_table(activities, english=heading[0] == "Daily Lesson Plan")
    if mathematics:
        heading, details = _math_details(heading, details, teacher)
    details, teacher_fields = _premium_header_payload(heading, details)
    regular, bold, _ = pdf_fonts()
    font_size = 9 if mathematics else 9.5
    leading = (9.35 if compact else 9.9) if mathematics else (11 if compact else 12)
    body = ParagraphStyle("DLP body", fontName=regular, fontSize=font_size, leading=leading)
    label = ParagraphStyle("DLP label", parent=body, fontName=bold)
    table_heading = ParagraphStyle("DLP table heading", parent=label, alignment=TA_CENTER)
    title = ParagraphStyle("DLP title", parent=table_heading, fontSize=14 if mathematics else 15, leading=17)
    subtitle = ParagraphStyle("DLP subtitle", parent=body, alignment=TA_CENTER)

    def paragraph(value, style):
        lines = _cell_lines(value, False)
        formatted = []
        for line, strong in lines:
            line = escape(line)
            formatted.append(f'<b>{line}</b>' if strong else line)
        return Paragraph("<br/>".join(formatted), style)

    def table(rows, widths, header=False):
        cells = [[paragraph(row[0], label), *(paragraph(value, body) for value in row[1:])]
                 for row in rows]
        if header:
            cells[0] = [paragraph(value, table_heading) for value in rows[0]]
        result = Table(cells, colWidths=[width * mm for width in widths], repeatRows=int(header))
        padding = 2.5 if mathematics else (3 if compact else 4)
        commands = pdf_box_style(padding)
        commands.append(("BACKGROUND", (0, 0), (0, -1), fill))
        if header:
            commands.append(("BACKGROUND", (1, 0), (-1, 0), fill))
        result.setStyle(commands)
        return result

    def footer(canvas, document):
        canvas.setFont(regular, 7.5)
        canvas.drawCentredString(A4[0] / 2, 5 * mm, f"CikguLaju AI  •  {document.page}")

    doc = BaseDocTemplate(output, pagesize=A4, title=f"{heading[0]} · {heading[2]}")
    frame = Frame(14 * mm, 11 * mm if mathematics else 15 * mm,
                  182 * mm, 274 * mm if mathematics else 267 * mm,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    if mathematics:
        doc.addPageTemplates(PageTemplate("RPH A4", frames=[frame], onPage=footer))
    else:
        doc.addPageTemplates(PageTemplate("DLP A4", frames=[frame]))
    # Keep the original title above the two-panel header, in full-width
    # centred text. Both identity and teacher data remain source-authored.
    identity_fields = _separated_header_identity(heading)
    if identity_fields:
        opening = [
            Paragraph(f"<b>{escape(name)}:</b> {escape(value)}", body)
            for name, value in identity_fields
        ]
    else:
        opening = [paragraph(heading[0], title),
                   paragraph(heading[1], subtitle),
                   paragraph(heading[2], label)]
    # Use the native ReportLab Paragraph parser here. The wrapper helper
    # escapes markup by design for curriculum content; passing formatting
    # through that helper prints literal <b> tags in the downloadable PDF.
    teacher_lines = [Paragraph(f"<b>{escape(name)}:</b> {escape(value)}", body)
                     for name, value in teacher_fields]
    title_panel = Table([[opening, teacher_lines]], colWidths=[118 * mm, 64 * mm], style=[
        ("BACKGROUND", (0, 0), (-1, -1), fill),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#" + _TEACHER_PANEL_FILL)),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.55, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])
    story = [
        *([paragraph(heading[0], title), Spacer(1, 3)] if identity_fields else []),
        title_panel,
        Spacer(1, 6),
        table(details, _FIELD_WIDTHS),
        Spacer(1, 6),
        table(activities, _ACTIVITY_WIDTHS, header=True),
        Spacer(1, 6),
        table(reflection, _FIELD_WIDTHS),
    ]
    if mathematics:
        story = [KeepInFrame(182 * mm, 274 * mm, story, mode="shrink")]
    doc.build(story)
