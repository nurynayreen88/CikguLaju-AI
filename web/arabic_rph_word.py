"""Render the reviewed, source-matched Arabic RPH in the original three-table layout."""

from datetime import date
from unicodedata import bidirectional

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT, WD_TABLE_DIRECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


_ARABIC_FILL = "FCE8D8"


def _paragraph(paragraph, text, *, bold=False, size=11, centered=False):
    first_strong = next(
        (direction for char in text if (direction := bidirectional(char)) in ("L", "R", "AL")),
        "L",
    )
    if centered:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if first_strong in ("R", "AL"):
        props = paragraph._p.get_or_add_pPr()
        props.insert_element_before(OxmlElement("w:bidi"), "w:jc")
        if not centered:
            props.get_or_add_jc().set(qn("w:val"), "start")
    elif not centered:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    run = paragraph.add_run(text)
    run.font.name = "Amiri"
    run.font.size = Pt(size)
    run.bold = bold
    run.font.cs_bold = bold
    rpr = run._r.get_or_add_rPr()
    rpr.rFonts.set(qn("w:cs"), "Amiri")
    cs_size = OxmlElement("w:szCs")
    cs_size.set(qn("w:val"), str(2 * size))
    rpr.insert_element_before(cs_size, "w:rtl")


def _table(doc, widths, rows, *, header=False, align_right=False, teacher_left=False):
    if doc.tables:
        spacer = doc.add_paragraph()
        spacer.paragraph_format.line_spacing = Pt(5)
        spacer.paragraph_format.space_after = Pt(0)
    table = doc.add_table(rows=0, cols=len(widths))
    table.table_direction = WD_TABLE_DIRECTION.RTL
    # With RTL in LibreOffice, unspecified alignment can offset the other
    # 18.7 cm tables by ~5 pt even when OOXML column sums are equal.
    # Anchor every RTL table to the same right page margin.
    table.alignment = WD_TABLE_ALIGNMENT.RIGHT
    table.style = "Table Grid"
    table.autofit = False
    for column, width in zip(table.columns, widths):
        column.width = Cm(width)
    for row_index, values in enumerate(rows):
        row = table.add_row()
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for index, (cell, value, width) in enumerate(zip(row.cells, values, widths)):
            cell.width = Cm(width)
            is_label = ((index == 1) if teacher_left else (index == 0)) or (header and row_index == 0)
            if is_label:
                shade = OxmlElement("w:shd")
                shade.set(qn("w:val"), "clear")
                shade.set(qn("w:fill"), _ARABIC_FILL)
                cell._tc.get_or_add_tcPr().append(shade)
            _paragraph(cell.paragraphs[0], value, bold=is_label)
    return table


def _automatic_reflection(plan):
    """Replace only the generic count template with the exact success evidence."""
    original = plan["reflection"]
    if original.strip() == "بلغ هدف الدرس ____ من ____ تلميذًا. إجراء المتابعة ____________________.":
        success = plan["success"].strip()
        if success:
            return "____ / ____ تحقق لديهم معيار النجاح: " + success + " المتابعة: ____."
    return original


def render_arabic_word(plan, teacher_fields, reflection, dest):
    class_name, date_iso, time, pupils, _ = teacher_fields
    lesson_date = date.fromisoformat(date_iso).strftime("%d/%m/%Y") if date_iso else ""
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(1)
    section.left_margin = section.right_margin = Cm(1.15)
    section.footer_distance = Cm(0.45)

    title = doc.add_paragraph()
    _paragraph(title, "خطة التدريس اليومية لمادة اللغة العربية", bold=True, size=17, centered=True)
    # The Arabic title remains centred OUTSIDE the first RTL grid.
    # Earlier shading/borders turned this separate title into a second
    # floating box. Remove only that decoration; preserve the actual title.
    title.paragraph_format.space_after = Pt(4)
    numerals = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
    year = str(plan["year"]).translate(numerals)
    pages = plan["pages"].replace(" & ", " و").translate(numerals)
    # A4 printable width is 18.70 cm (21 cm minus two 1.15 cm margins).
    # Restore the owner-approved example: 9.95 cm identity on the RIGHT,
    # 8.75 cm teacher metadata on the LEFT in the physical RTL table.
    # Keep the single full-width 18.7 cm outer border; do not change SK/SP
    # and do not duplicate curriculum identity in the details table.
    identity_rows = (
        ("الصف", year),
        ("الوحدة", plan["topic"]),
        ("موضوع الدرس", plan["focus"]),
    )
    header = _table(doc, (9.95, 3.25, 5.5), [
        ("", "الفصل", class_name or ""),
        ("", "التاريخ", lesson_date),
        ("", "الوقت", time or ""),
        ("", "عدد التلاميذ", pupils or ""),
    ], align_right=True, teacher_left=True)
    identity_cell = header.cell(0, 0).merge(header.cell(3, 0))
    # Vertical merges inherit empty paragraphs from all four source cells.
    # Remove those ONLY in this new identity panel to avoid blank lines.
    for paragraph in list(identity_cell.paragraphs)[1:]:
        identity_cell._tc.remove(paragraph._p)
    identity_cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    shade = OxmlElement("w:shd")
    shade.set(qn("w:val"), "clear")
    shade.set(qn("w:fill"), _ARABIC_FILL)
    identity_cell._tc.get_or_add_tcPr().append(shade)
    for index, (label, value) in enumerate(identity_rows):
        paragraph = (identity_cell.paragraphs[0] if index == 0
                     else identity_cell.add_paragraph())
        # One RTL-aligned tab stop keeps both label and value starts
        # vertically consistent for subject/year/topic without retyping
        # any source field. The teacher's existing 3-column header already
        # aligns its Class/Date/Time/Pupil-count values by real grid cells.
        paragraph.paragraph_format.tab_stops.add_tab_stop(Cm(3.1))
        _paragraph(paragraph, f"{label}:\t{value}", bold=(index == 0), size=11)
    _table(doc, (4.3, 14.4), [
        ("معيار المحتوى", f"\u2066{plan['sk']}\u2069  {plan['content_standard']}"),
        ("معيار التعلّم", f"\u2066{plan['sp']}\u2069  {plan['learning_standard']}"),
        ("هدف التعلّم", plan["objective"]),
        ("معيار النجاح", plan["success"]),
    ])
    _table(doc, (3.1, 12.0, 3.6), [
        ("المرحلة", "أنشطة التعليم والتعلّم", "ملاحظات"),
        ("التمهيد", plan["induction"], ""),
        ("النشاط الأول", plan["activity_1"], plan.get("activity_1_note", "ترديد جماعي")),
        ("النشاط الثاني", plan["activity_2"], "عمل ثنائي"),
        ("التقويم التكويني", plan["assessment"], "أداء فردي"),
        ("الخاتمة", plan["closure"], ""),
    ], header=True)
    _table(doc, (4.3, 14.4), [
        ("الوسائل التعليمية", plan["materials"]),
        ("المرجع", f"كتاب اللغة العربية للصفّ {year}، ص {pages}."),
        ("تأمّل المعلّم", reflection or _automatic_reflection(plan)),
    ])
    _paragraph(section.footer.paragraphs[0], "CikguLaju AI", size=8, centered=True)
    doc.core_properties.title = "خطة التدريس اليومية لمادة اللغة العربية"
    doc.save(dest)
