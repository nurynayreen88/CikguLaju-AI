"""Compact differentiated supports on actual RPH Word/PDF without layout regression."""
from io import BytesIO

import pytest
from docx import Document
from pypdf import PdfReader

from dlp_year2_rph import _pdf, _word
from web.rph_supporting_fields_20261121 import supplement_details


SAMPLES = (
    ("Rancangan Pengajaran Harian", "Sains · Tahun 5 SK · 2027", "Mengukur jarak"),
    ("Rancangan Pengajaran Harian", "Matematik SK Tahun 5 · 2027", "Membandingkan nombor"),
    ("Daily Lesson Plan", "Science (DLP) · Year 3 SK", "Investigating shadows"),
    ("Daily Lesson Plan", "Mathematics (DLP) · Year 4 SK", "Comparing fractions"),
    ("Rancangan Pengajaran Harian", "PPKI · Pengurusan Kehidupan · Tahun 2", "Menjaga kebersihan diri"),
)
DETAILS = [
    ("Standard Kandungan", "2.1 Mengetahui cara menggunakan peralatan"),
    ("Standard Pembelajaran", "2.1.1 Mengenal pasti dan mengaplikasikan"),
    ("Objektif", "Murid dapat membandingkan dua keadaan menggunakan pemerhatian."),
    ("Bahan", "Kad bergambar, pembaris dan jadual pemerhatian"),
]
ACTIVITIES = [
    ("Fasa", "Guru", "Murid"),
    ("Set Induksi", "Tunjukkan dua gambar.", "Murid mengenal pasti gambar."),
    ("Aktiviti 1", "Modelkan pemerhatian.", "Murid berbincang dengan rakan dan merekod dua bacaan."),
    ("Pentaksiran PBD", "Semak dua bacaan secara individu.", "Murid membandingkan dua bacaan."),
    ("Penutup", "Minta rumusan.", "Murid membuat rumusan berdasarkan hasil."),
]
FOOTER = [
    ("Evidens PBD", "Dua bacaan dan satu perbandingan yang tepat."),
    ("Refleksi", "___ / ___ murid mencapai objektif."),
]


@pytest.mark.parametrize("heading", SAMPLES)
def test_derived_fields_preserve_evidence_and_reflection(heading):
    original_details = list(DETAILS)
    original_activities = list(ACTIVITIES)
    original_footer = list(FOOTER)
    rows = supplement_details(heading, DETAILS, ACTIVITIES, FOOTER)
    assert len(rows) == len(DETAILS) + 2
    assert rows[:len(DETAILS)] == DETAILS
    assert DETAILS == original_details
    assert ACTIVITIES == original_activities
    assert FOOTER == original_footer
    combined = "\n".join(value for _, value in rows)
    if heading[0] == "Daily Lesson Plan":
        for term in ("Cross-curricular", "21st-century", "Higher-order", "Remedial", "Enrichment"):
            assert term.lower() in combined.lower() or any(term in x for x, _ in rows)
    else:
        for term in ("EMK:", "PAK21:", "KBAT:", "Pemulihan:", "Pengayaan:"):
            assert term in combined
    assert "Kolaborasi dan komunikasi" in combined or "Collaboration and communication" in combined
    assert "Dua bacaan dan satu perbandingan" in FOOTER[0][1]


@pytest.mark.parametrize("heading", SAMPLES)
def test_actual_renderers_keep_three_tables_and_a4(heading):
    for renderer in (_word, _pdf):
        out = BytesIO()
        english = heading[0] == "Daily Lesson Plan"
        renderer(out, heading, DETAILS, ACTIVITIES, FOOTER,
                 mathematics=("matematik" in heading[1].casefold() or "mathematics" in heading[1].casefold()),
                 teacher={"class": "", "date": "", "time": "", "students": ""})
        raw = out.getvalue()
        if renderer is _word:
            doc = Document(BytesIO(raw))
            assert len(doc.tables) == 3
            assert doc.tables[2].cell(0, 1).text == FOOTER[0][1]
            assert doc.tables[2].cell(1, 1).text == FOOTER[1][1]
            cells = "\n".join(cell.text for row in doc.tables[0].rows for cell in row.cells)
            for term in (("EMK", "PAK21", "KBAT", "Pemulihan", "Pengayaan") if not english
                         else ("Cross-curricular", "21st-century", "Higher-order", "Remedial", "Enrichment")):
                assert term.casefold() in cells.casefold()
            section = doc.sections[0]
            assert round(section.page_width.cm, 1) == 21.0
            assert round(section.page_height.cm, 1) == 29.7
        else:
            pages = PdfReader(BytesIO(raw)).pages
            assert len(pages) == 1, (heading[1], len(pages))
            text = " ".join(page.extract_text() for page in pages)
            assert "___ / ___" in text
            assert ("Remedial" if english else "Pemulihan") in text
            assert ("Enrichment" if english else "Pengayaan") in text


def test_ppki_uses_existing_verified_support_text():
    heading = SAMPLES[-1]
    existing = [("Sokongan", "Beri dua kad bergambar. Terima jawapan secara isyarat."),
                ("Pentaksiran Bilik Darjah", "Dua tindakan yang betul."),
                ("Refleksi", "___ murid mencapai objektif.")]
    result = supplement_details(heading, DETAILS, ACTIVITIES, existing)
    assert result[:len(DETAILS)] == DETAILS
    assert existing[0][1] not in result[-1][1]
    assert "bahagian Sokongan" in result[-1][1]
    assert existing[0][1] == "Beri dua kad bergambar. Terima jawapan secara isyarat."


def test_no_duplication_and_other_subjects_unchanged():
    english = ("Daily Lesson Plan", "English Year 3", "Listening to directions")
    assert supplement_details(english, DETAILS, ACTIVITIES, FOOTER) is DETAILS
    sains = supplement_details(SAMPLES[0], DETAILS, ACTIVITIES, FOOTER)
    assert supplement_details(SAMPLES[0], sains, ACTIVITIES, FOOTER) == sains


def test_real_ppki_catalogue_renders_without_replacing_support():
    from staging.ppki.catalog import UNIT, YEAR, catalog
    from staging.ppki.render_pengurusan_kehidupan import render_lesson
    catalogue = catalog(UNIT, year=YEAR)
    lesson = catalogue["lessons"][0]
    teacher = {"class": "", "date": "", "time": "", "students": "", "reflection": ""}
    data = render_lesson(catalogue, lesson, "docx", teacher)
    doc = Document(BytesIO(data))
    assert len(doc.tables) == 3
    content = "\n".join(cell.text for row in doc.tables[0].rows for cell in row.cells)
    footer = "\n".join(cell.text for row in doc.tables[2].rows for cell in row.cells)
    assert "EMK" in content and "PAK21" in content
    assert "Pemulihan" in content and "Pengayaan" in content
    assert "Sokongan" in footer and lesson["support"] in footer
    assert lesson["assessment"] in footer and "2.1.1" in content
    pdf = render_lesson(catalogue, lesson, "pdf", teacher)
    assert len(PdfReader(BytesIO(pdf)).pages) == 1


def test_real_science_dlp_year2_keeps_three_tables_and_a4():
    from dlp_year2_rph import catalog, render
    units = catalog()["SCIENCE_DLP"]
    first = units[0]["lessons"][0]
    teacher = {"class": "", "date": "", "time": "", "students": "", "reflection": ""}
    word = render("SCIENCE_DLP", units[0], first, "word", teacher)
    doc = Document(BytesIO(word))
    assert len(doc.tables) == 3
    fields = "\n".join(cell.text for row in doc.tables[0].rows for cell in row.cells)
    assert "21st-century" in fields and "Remedial" in fields and "Enrichment" in fields
    pdf = render("SCIENCE_DLP", units[0], first, "pdf", teacher)
    assert len(PdfReader(BytesIO(pdf)).pages) == 1
