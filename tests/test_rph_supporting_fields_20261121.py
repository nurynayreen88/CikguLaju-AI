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



@pytest.mark.parametrize("heading", SAMPLES)
def test_dlp_sains_matematik_ppki_all_outer_boxes_are_equal_width_a4(heading):
    """Owner's permanent rule: physical 182 mm grid in each specialty layout.

    This checks actual Word/PDF renderers, not a source-code constant alone.
    The content and existing RTL/subject-specific procedures are untouched.
    """
    import fitz

    is_math = "matematik" in heading[1].casefold() or "mathematics" in heading[1].casefold()
    teacher = {"class": "", "date": "", "time": "", "students": ""}
    word = BytesIO()
    _word(word, heading, DETAILS, ACTIVITIES, FOOTER,
          mathematics=is_math, teacher=teacher)
    doc = Document(BytesIO(word.getvalue()))
    assert len(doc.tables) == 3
    physical_widths = [sum(column.width.mm for column in table.columns)
                       for table in doc.tables]
    assert all(abs(width - 182) < .8 for width in physical_widths), (
        heading[1], physical_widths,
    )
    assert max(physical_widths)-min(physical_widths) < .4
    assert round(doc.sections[0].page_width.cm, 1) == 21
    assert round(doc.sections[0].page_height.cm, 1) == 29.7

    output = BytesIO()
    _pdf(output, heading, DETAILS, ACTIVITIES, FOOTER,
         mathematics=is_math, teacher=teacher)
    with fitz.open(stream=output.getvalue(), filetype="pdf") as pdf:
        assert len(pdf) == 1, (heading[1], len(pdf))
        page = pdf[0]
        assert abs(page.rect.width-595.28) < 1
        assert abs(page.rect.height-841.89) < 1
        # Actual ReportLab line operators should share both outer edges
        # across details, activity and reflection tables (not label widths).
        rules = [
            fitz.Rect(item["rect"]) for item in page.get_drawings()
            if 513 < fitz.Rect(item["rect"]).width < 520
            and fitz.Rect(item["rect"]).height < 1.6
        ]
        assert len(rules) >= 5, (heading[1], rules)
        assert max(rect.x0 for rect in rules)-min(rect.x0 for rect in rules) < 2
        assert max(rect.x1 for rect in rules)-min(rect.x1 for rect in rules) < 2
        txt = page.get_text()
        assert "2.1.1" in txt and "Set Induksi" in txt or (
            heading[0] == "Daily Lesson Plan" and "Set Induction" in txt
        )


def test_real_ppki_and_dlp_year2_word_table_outer_edges_stay_182mm():
    """Read the reviewed source bank, not only synthetic display fixtures."""
    from dlp_year2_rph import catalog, render
    from staging.ppki.catalog import UNIT, YEAR, catalog as ppki_catalog
    from staging.ppki.render_pengurusan_kehidupan import render_lesson

    teacher = {"class": "", "date": "", "time": "", "students": "", "reflection": ""}
    examples = []
    source = ppki_catalog(UNIT, year=YEAR)
    examples.append(("PPKI", render_lesson(source, source["lessons"][0], "docx", teacher)))
    for subject in ("SCIENCE_DLP", "MATH_DLP"):
        unit = catalog()[subject][0]
        examples.append((subject, render(subject, unit, unit["lessons"][0], "word", teacher)))

    for label, payload in examples:
        doc = Document(BytesIO(payload))
        widths = [sum(column.width.mm for column in table.columns)
                  for table in doc.tables]
        assert len(widths) == 3, (label, len(widths))
        assert max(widths)-min(widths) < .4, (label, widths)
        assert all(abs(width-182)<.8 for width in widths), (label, widths)
