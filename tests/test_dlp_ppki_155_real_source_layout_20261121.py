"""Read-only design audit: every reviewed Year-2 DLP and PPKI pilot lesson.

Exactly 141 DLP (63 Science + 78 Mathematics) plus 14 PPKI pilot lessons
from source JSONs. This does NOT validate DLP/PPKI Year 3–6, other programme
components, authenticated teacher downloads, or visually approve every glyph.
No DB, Web, Telegram, payments, quotas, or curriculum rewrites.
"""
from io import BytesIO

import fitz
from docx import Document

from dlp_year2_rph import catalog as dlp_catalog, render as dlp_render
from staging.ppki.render_pengurusan_kehidupan import (
    load_catalog as ppki_catalog, render_lesson as ppki_render,
)
from web.rph_premium_readback_20261121 import premium_rph_details


TEACHER = {
    "class": "", "date": "", "time": "", "students": "",
    "reflection": "Catatan refleksi asal dilengkapkan selepas PdP.",
}


def _check_output(word, pdf, *, label, objective, subject):
    doc = Document(BytesIO(word))
    assert len(doc.tables) == 4, (label, len(doc.tables))
    widths = [sum(c.width.mm for c in table.columns) for table in doc.tables]
    assert all(abs(width - 182) < 1 for width in widths), (label, widths)
    assert max(widths) - min(widths) < 0.8, (label, widths)
    assert doc.tables[0].columns[0].width > doc.tables[0].columns[1].width, label
    fields = premium_rph_details(doc)
    metadata = (
        ("Kelas", "Tarikh", "Masa", "Bilangan Murid")
        if subject == "PPKI"
        else ("Class", "Date", "Time", "Number of pupils")
    )
    for name in metadata:
        assert name in fields, (label, name)
        assert fields[name] == "", (label, name, fields[name])
    full_word = "\n".join(
        [p.text for p in doc.paragraphs]
        + [c.text for t in doc.tables for row in t.rows for c in row.cells]
    )
    assert objective in full_word, (label, "source objective lost")
    assert TEACHER["reflection"] in full_word, (label, "teacher reflection lost")
    assert "____" not in doc.tables[0].cell(0, 1).text, label

    assert pdf.startswith(b"%PDF-"), label
    with fitz.open(stream=pdf, filetype="pdf") as artifact:
        assert 1 <= len(artifact) <= 4, (label, len(artifact))
        text = " ".join(page.get_text() for page in artifact)
        assert len(text.strip()) > 150, (label, "PDF text missing")
        assert ("Content Standards" if subject != "PPKI" else "Standard Kandungan") in text, label
        assert TEACHER["reflection"] in " ".join(text.split()), (label, "PDF reflection lost")
        for page in artifact:
            assert abs(page.rect.width - 595.28) < 2, label
            assert abs(page.rect.height - 841.89) < 2, label
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                x0, y0, x1, y1 = block["bbox"]
                assert -1 <= x0 < x1 <= page.rect.width + 1, (label, block["bbox"])
                assert -1 <= y0 < y1 <= page.rect.height + 1, (label, block["bbox"])


def test_all_141_dlp_year2_reviewed_lessons_keep_premium_word_and_pdf():
    sources = dlp_catalog()
    assert set(sources) == {"SCIENCE_DLP", "MATH_DLP"}
    counts = {}
    for subject, expected in (("SCIENCE_DLP", 63), ("MATH_DLP", 78)):
        count = 0
        for unit in sources[subject]:
            for lesson in unit["lessons"]:
                label = subject + ":" + lesson["id"]
                word = dlp_render(subject, unit, lesson, "word", TEACHER)
                pdf = dlp_render(subject, unit, lesson, "pdf", TEACHER)
                _check_output(word, pdf, label=label,
                              objective=lesson["objective"], subject=subject)
                count += 1
        assert count == expected, (subject, count)
        counts[subject] = count
    assert sum(counts.values()) == 141
    print("DLP_YEAR2_ALL_REVIEWED_SOURCE_WORD_PDF_A4_PASS", counts)


def test_all_14_ppki_year2_pilot_lessons_keep_premium_word_and_pdf():
    source = ppki_catalog()
    assert source["year"] == 2
    assert len(source["lessons"]) == 14
    for i, lesson in enumerate(source["lessons"], 1):
        word = ppki_render(source, lesson, "docx", TEACHER)
        pdf = ppki_render(source, lesson, "pdf", TEACHER)
        _check_output(word, pdf, label=f"PPKI_T2_PdP_{i:02d}",
                      objective=lesson["objective"], subject="PPKI")
    print("PPKI_YEAR2_PILOT_ALL_SOURCE_WORD_PDF_A4_PASS", len(source["lessons"]))
