"""Real, source-preserving English Y6 boxed Word presentation QA.

Never mutates lesson files, quota, payment, source DB or any other RPH route.
"""
from collections import Counter
from io import BytesIO
from zipfile import ZipFile

from docx import Document
from lxml import etree

from web.english_y6_rph_2027_http import FIELDS, make_docx, source_rows
from web.rph_year6_boxed_word_20261123 import boxed_word_bytes

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def tokens(data):
    with ZipFile(BytesIO(data)) as package:
        root = etree.fromstring(package.read("word/document.xml"))
    return Counter(p.text for p in root.iter(W + "t"))


def fixture():
    return {
        key: ("Activity 1 (10 minutes)\nTeacher: Model reading.\nPupils: Read and point."
              "\n\nActivity 2 (18 minutes)\nTeacher: Compare details."
              "\n\nActivity 3 (15 minutes)\nPupils: Explain."
              if key == "AKTIVITI UTAMA"
              else ("Teacher follow-up based on evidence." if key == "REFLEKSI"
                    else f"Source-preserved {label}, SK/SP 3.2.1"))
        for key, label in FIELDS
    }


def test_fifteen_source_fields_and_document_text_remain_exactly_unchanged():
    rows = fixture()
    before = make_docx(1, rows).getvalue()
    after = boxed_word_bytes(before, FIELDS)
    assert after != before
    assert tokens(after) == tokens(before)
    assert boxed_word_bytes(after, FIELDS) == after  # no repeated styling
    doc = Document(BytesIO(after))
    assert len(doc.tables) == 4
    assert len(doc.tables[0].rows) == 1
    assert len(doc.tables[0].columns) == 2
    assert doc.tables[0].columns[0].width > doc.tables[0].columns[1].width
    assert "RANCANGAN PENGAJARAN HARIAN" in doc.tables[0].cell(0, 0).text
    assert "Class:" in doc.tables[0].cell(0, 1).text
    assert len(doc.tables[1].rows) == 9
    assert len(doc.tables[2].rows) == 3
    assert len(doc.tables[3].rows) == 2
    assert "Source-preserved" in doc.tables[1].cell(1, 1).text
    assert "Teacher follow-up" in doc.tables[3].cell(1, 1).text
    assert doc.sections[0].page_width.twips == 11906
    with ZipFile(BytesIO(after)) as z:
        xml = z.read("word/document.xml")
        assert b"E9F3F9" in xml
        assert b"F5F7FA" in xml
        assert b"Activity 1" in xml
        bold_nodes = etree.fromstring(xml).xpath(
            "//*[local-name()='p'][.//*[local-name()='t' and contains(text(), 'Activity 1')]]"
            "//*[local-name()='b']"
        )
        assert bold_nodes


def test_source_files_from_verified_y6_lesson_catalog_are_not_rewritten():
    for lesson in (1, 16, 32, 80, 160):
        rows = source_rows(lesson)
        assert rows is not None, lesson
        before = make_docx(lesson, rows).getvalue()
        after = boxed_word_bytes(before, FIELDS)
        assert after != before, lesson
        assert tokens(after) == tokens(before), lesson
        doc = Document(BytesIO(after))
        assert len(doc.tables) == 4, lesson
        for index, (key, label) in enumerate(FIELDS):
            table_idx = 1 if index < 9 else (2 if index < 12 else 3)
            offset = 0 if table_idx == 1 else (9 if table_idx == 2 else 12)
            assert doc.tables[table_idx].cell(index - offset, 0).text == label + ":"
            original_value = rows.get(key) or "—"
            assert doc.tables[table_idx].cell(index - offset, 1).text == original_value


def test_fail_closed_on_bad_zip_unexpected_header_or_missing_field():
    original = make_docx(1, fixture()).getvalue()
    assert boxed_word_bytes(b"not a Word file", FIELDS) == b"not a Word file"
    assert boxed_word_bytes(original[:180], FIELDS) == original[:180]
    assert boxed_word_bytes(original, [("NOT_A_FIELD", "Bad")]) == original
    doc = Document(BytesIO(original))
    doc.paragraphs[0].text = "Unknown layout"
    b = BytesIO()
    doc.save(b)
    assert boxed_word_bytes(b.getvalue(), FIELDS) == b.getvalue()


def test_non_document_zip_members_preserved_byte_for_byte():
    original = make_docx(1, fixture()).getvalue()
    styled = boxed_word_bytes(original, FIELDS)
    with ZipFile(BytesIO(original)) as source, ZipFile(BytesIO(styled)) as target:
        assert source.namelist() == target.namelist()
        for name in source.namelist():
            if name != "word/document.xml":
                assert source.read(name) == target.read(name)


def test_real_word_to_pdf_renders_a4_with_complete_header(tmp_path):
    import subprocess
    import fitz

    rows = source_rows(1)
    assert rows is not None
    data = boxed_word_bytes(make_docx(1, rows).getvalue(), FIELDS)
    word = tmp_path / "english-y6-001.docx"
    word.write_bytes(data)
    result = subprocess.run(
        ["libreoffice",
         "-env:UserInstallation=" + (tmp_path / "profile").as_uri(),
         "--headless", "--convert-to", "pdf",
         "--outdir", str(tmp_path), str(word)],
        timeout=100, capture_output=True, text=True,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    pdf = tmp_path / "english-y6-001.pdf"
    assert pdf.is_file()
    with fitz.open(pdf) as document:
        assert 1 <= len(document) <= 4
        combined = "\n".join(page.get_text() for page in document)
        assert "RANCANGAN PENGAJARAN HARIAN" in combined
        assert "Main Learning Standard" in combined
        assert "Activity 1" in combined
        assert "Reflection" in combined
        for page in document:
            assert abs(page.rect.width - 595.3) < 3
            assert abs(page.rect.height - 841.9) < 3
            for box in page.get_text("blocks"):
                assert box[0] >= -1 and box[2] <= page.rect.width + 1
                assert box[1] >= -1 and box[3] <= page.rect.height + 1
