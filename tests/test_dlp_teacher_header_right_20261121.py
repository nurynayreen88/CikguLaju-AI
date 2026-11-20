"""Guard the DLP class-metadata header without altering curriculum text."""
from io import BytesIO

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from pypdf import PdfReader

from dlp_year2_rph import _extract_teacher_header, _pdf, _word


def test_extract_teacher_header_preserves_source_order():
    fields = [
        ("Unit", "Unit 1"), ("Date", ""), ("Time", "08:00 - 09:00"),
        ("Class", "2 Amanah"), ("Content Standards", "1.1 Identify"),
        ("Number of pupils", "28"), ("Learning objective", "Recognise"),
    ]
    kept, header = _extract_teacher_header(fields, english=True)
    assert kept == [
        ("Unit", "Unit 1"), ("Content Standards", "1.1 Identify"),
        ("Learning objective", "Recognise"),
    ]
    assert header == [
        ("Class", "2 Amanah"), ("Date", ""), ("Time", "08:00 - 09:00"),
        ("Number of pupils", "28"),
    ]


def _sample():
    heading = ("Daily Lesson Plan", "Science (DLP) · Year 2 SK", "Our senses")
    fields = [
        ("Unit", "Unit 1"),
        ("Date", "04/01/2027"), ("Time", ""), ("Class", ""),
        ("Number of pupils", ""),
        ("Content Standards", "1.1 Describe"),
        ("Learning Standards", "1.1.1 Observe"),
        ("Learning objective", "Pupils describe their observations."),
        ("Materials", "Picture cards"),
    ]
    activities = [
        ("Phase", "Teacher", "Pupils"),
        ("Set Induction", "Shows pictures.", "Observe pictures."),
        ("Activity 1", "Explains the pictures.", "Describe details."),
        ("Closure", "Summarises.", "Respond orally."),
    ]
    reflection = [("Reflection", "Teacher records pupil learning.")]
    return heading, fields, activities, reflection


def test_word_header_is_top_right_and_fields_not_duplicated():
    buf = BytesIO()
    _word(buf, *_sample())
    doc = Document(BytesIO(buf.getvalue()))
    assert len(doc.tables) == 4
    top = doc.tables[0]
    assert top.alignment == WD_TABLE_ALIGNMENT.RIGHT
    assert [row.cells[0].text for row in top.rows] == [
        "Class", "Date", "Time", "Number of pupils",
    ]
    assert [row.cells[1].text for row in top.rows] == [
        "", "04/01/2027", "", "",
    ]
    body = " ".join(c.text for t in doc.tables[1:] for row in t.rows for c in row.cells)
    assert "Content Standards" in body
    assert "Learning objective" in body
    assert "Number of pupils" not in body


def test_pdf_keeps_teacher_header_and_standards_on_one_a4():
    buf = BytesIO()
    _pdf(buf, *_sample())
    reader = PdfReader(BytesIO(buf.getvalue()))
    assert len(reader.pages) == 1
    page = reader.pages[0]
    assert abs(float(page.mediabox.width) - 595.28) < 1
    text = page.extract_text()
    for value in ("Class", "Date", "Time", "Number of pupils",
                  "04/01/2027", "Content Standards", "1.1.1 Observe"):
        assert value in text
