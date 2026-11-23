"""Single CikguLaju RPH generator entrance: backward compatibility checks."""
from io import BytesIO

import fitz
import pytest
from docx import Document

from dlp_year2_rph import _word, _pdf, catalog, render
from staging.ppki.render_pengurusan_kehidupan import (
    load_catalog, render_lesson,
)
from web.rph_unified_engine import (
    MASTER_NAME, HEADER_PANELS, TEACHER_PANEL_FILL,
    render_structured_rph,
)


def _text_from_word(blob):
    document = Document(BytesIO(blob))
    return (len(document.tables), tuple(
        tuple(cell.text for cell in row.cells)
        for table in document.tables for row in table.rows
    ))


def _text_from_pdf(blob):
    with fitz.open(stream=blob, filetype="pdf") as doc:
        return (len(doc), tuple(page.get_text() for page in doc))


@pytest.mark.parametrize("fmt", ["word", "docx", "pdf"])
@pytest.mark.parametrize("source", ["dlp", "ppki"])
def test_unified_generator_preserves_legacy_renderer_content(source, fmt):
    # A real structured source is provided by its own curriculum adapter.
    # We do not fabricate optional EMK, PAK21 or PBD rows.
    if source == "ppki":
        heading = ("Rancangan Pengajaran Harian",
                   "PPKI · Pengurusan Kehidupan · Tahun 2", "Menjaga kebersihan")
        details = [("Unit", "1"), ("PdP", "001"),
                   ("Standard Kandungan", "1.1 Mengurus diri"),
                   ("Standard Pembelajaran", "1.1.1 Mengenal alat kebersihan"),
                   ("Objektif Pembelajaran", "Murid mengenal alat kebersihan.")]
        activities = [("Fasa", "Guru", "Murid"),
                      ("Set Induksi", "Menunjukkan gambar.", "Melihat gambar."),
                      ("Aktiviti 1", "Membimbing murid.", "Memilih gambar."),
                      ("Penutup", "Membuat rumusan.", "Menyatakan jawapan.")]
        footer = [("Sokongan", "Bimbingan individu."),
                  ("Refleksi", "18 murid mencapai objektif.")]
        options = {"compact": True, "label_fill": "EEE6F7"}
    else:
        heading = ("Daily Lesson Plan", "Science (DLP) · Year 2 SK", "Light")
        details = [("Unit", "Light"), ("Lesson / PdP", "Lesson 01"),
                   ("Class", "2 Amanah"), ("Date", "2027-01-12"),
                   ("Time", "08:00 - 09:00"), ("Number of pupils", "25"),
                   ("Content Standards", "6.1 Light"),
                   ("Learning Standards", "6.1.1 Identify sources of light"),
                   ("Learning objective", "Pupils identify two sources of light.")]
        activities = [("Phase", "Teacher", "Pupils"),
                      ("Induction", "Shows a torch.", "Observe the torch."),
                      ("Activity 1", "Guides pupils.", "Identify sources."),
                      ("Closure", "Reviews answers.", "Answer questions.")]
        footer = [("Reflection", "20 pupils achieved the objective.")]
        options = {}

    baseline_stream = BytesIO()
    legacy = _pdf if fmt == "pdf" else _word
    legacy(baseline_stream, heading, details, activities, footer, **options)
    unified = render_structured_rph(
        source=source, fmt=fmt, heading=heading, details=details,
        activities=activities, footer=footer, **options,
    )
    baseline = baseline_stream.getvalue()
    inspect = _text_from_pdf if fmt == "pdf" else _text_from_word
    assert inspect(baseline) == inspect(unified)
    if fmt != "pdf":
        doc = Document(BytesIO(unified))
        assert len(doc.tables) == 4
        assert doc.tables[0].cell(0, 1)._tc.get_or_add_tcPr().find(
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd"
        ).get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill") == TEACHER_PANEL_FILL


def test_reviewed_source_catalogs_still_use_one_shared_entrance():
    teacher = {"class": "2 Bestari", "date": "2027-01-12",
               "time": "08:00 - 09:00", "students": "25",
               "reflection": "Catatan guru disimpan tanpa perubahan."}
    for subject in ("SCIENCE_DLP", "MATH_DLP"):
        unit = catalog()[subject][0]
        word = render(subject, unit, unit["lessons"][0], "word", teacher)
        pdf = render(subject, unit, unit["lessons"][0], "pdf", teacher)
        assert teacher["reflection"] in str(_text_from_word(word))
        assert teacher["reflection"] in str(_text_from_pdf(pdf))
    ppki = load_catalog()
    word = render_lesson(ppki, ppki["lessons"][0], "docx", teacher)
    pdf = render_lesson(ppki, ppki["lessons"][0], "pdf", teacher)
    assert teacher["reflection"] in str(_text_from_word(word))
    assert teacher["reflection"] in str(_text_from_pdf(pdf))


def test_source_and_orientation_guards_are_fail_closed():
    assert MASTER_NAME == "BM_SK_KP2027_T1"
    assert TEACHER_PANEL_FILL == "F5F7FA"
    assert HEADER_PANELS["ltr"] == ("identity", "teacher")
    assert HEADER_PANELS["rtl"] == ("teacher", "identity")
    for source in ("jawi", "arabic", "sains", "sjkc", "kp2027", "unknown"):
        with pytest.raises(ValueError, match="not yet verified"):
            render_structured_rph(
                source=source, fmt="pdf", heading=("A", "B", "C"),
                details=[], activities=[], footer=[],
            )
    with pytest.raises(ValueError, match="Unsupported"):
        render_structured_rph(
            source="dlp", fmt="xlsx", heading=("A","B","C"),
            details=[], activities=[], footer=[],
        )
    with pytest.raises(ValueError, match="cannot use"):
        render_structured_rph(
            source="ppki", fmt="word", heading=("A","B","C"),
            details=[], activities=[], footer=[], mathematics=True,
        )


def test_single_teacher_fill_token_shared_across_existing_renderers():
    import dlp_year2_rph
    from web import rph_native_pdf_header_20261121, rph_premium_header_20261121
    assert dlp_year2_rph._TEACHER_PANEL_FILL == TEACHER_PANEL_FILL
    assert rph_native_pdf_header_20261121.TEACHER_PANEL_FILL == TEACHER_PANEL_FILL
    assert rph_premium_header_20261121.TEACHER_PANEL_FILL == TEACHER_PANEL_FILL
