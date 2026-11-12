"""Editable pupil Word worksheets for four verified English Year 4 lessons.

The exact source registry and teacher-note filter are shared with PDF output.
The Word download is not a new lesson generator and never changes RPH credits.
"""
from io import BytesIO

from web.english_y4_worksheet_pdf_20261112 import _source, _student_lines, _pdf_text


def worksheet_docx(year, lesson):
    """Build an A4 editable DOCX from the exact approved source, or None."""
    record = _source(year, lesson)
    if record is None:
        return None

    from docx import Document
    from docx.shared import Mm, Pt, RGBColor

    _title, raw = record
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.top_margin, section.bottom_margin = Mm(15), Mm(13)
    section.left_margin, section.right_margin = Mm(16), Mm(16)
    section.header_distance, section.footer_distance = Mm(6), Mm(7)

    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(9.5)
    normal.paragraph_format.space_after = Pt(2.5)
    normal.paragraph_format.line_spacing = 1.05

    head = section.header.paragraphs[0]
    head.text = "CIKGULAJU AI  |  ENGLISH YEAR 4"
    head.style = normal
    for run in head.runs:
        run.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(18, 89, 76)

    for source_line in _student_lines(raw):
        text = _pdf_text(source_line)
        if text.startswith("# "):
            p = doc.add_paragraph(style="Normal")
            p.paragraph_format.space_before = Pt(5)
            p.paragraph_format.space_after = Pt(7)
            run = p.add_run(text[2:])
            run.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(18, 89, 76)
        elif text.startswith("## "):
            p = doc.add_paragraph(style="Normal")
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(text[3:])
            run.bold = True
            run.font.size = Pt(10.5)
            run.font.color.rgb = RGBColor(18, 89, 76)
        elif not text.strip():
            p = doc.add_paragraph(style="Normal")
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 0.45
        else:
            p = doc.add_paragraph(style="Normal")
            p.add_run(text)

    foot = section.footer.paragraphs[0]
    foot.style = normal
    foot.text = (
        "Teacher-created supplementary worksheet. Not an official textbook page."
        "  |  Lesson %03d" % lesson
    )
    for run in foot.runs:
        run.font.size = Pt(7.5)
        run.font.color.rgb = RGBColor(76, 98, 93)

    doc.core_properties.title = "CikguLaju English Year 4 Lesson %03d - Worksheet" % lesson
    doc.core_properties.subject = "Teacher-authored pupil worksheet, editable A4"
    doc.core_properties.author = "CikguLaju AI"

    stream = BytesIO()
    doc.save(stream)
    result = stream.getvalue()
    if not result.startswith(bytes.fromhex("504b0304")) or len(result) < 5000 or len(result) > 200000:
        raise ValueError("Invalid Word worksheet output")
    return result
