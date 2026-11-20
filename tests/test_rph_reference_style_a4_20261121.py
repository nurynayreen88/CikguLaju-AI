"""A4 regression: native-structure English RPH before and after pastel Word styling.

Uses the AST-locked Word builder copied from app.py, and checks the active
builder's strict AST parity before rendering. No live accounts, DB or quotas.
"""
from io import BytesIO
from pathlib import Path
import subprocess

from docx import Document
from pypdf import PdfReader

from tools.audit_english_rph_word_a4_layout import (
    validate_word_function_snapshot, write_word,
)
from web.rph_reference_style_20261121 import style_three_table_word_bytes


SOURCE = {
    "MAIN CONTENT STANDARD": "1.2 Understand meaning in a variety of familiar contexts.",
    "MAIN LEARNING STANDARD": "1.2.1 Understand with support the main idea of short simple texts.",
    "COMPLEMENTARY CONTENT STANDARD": "2.1 Communicate simple information intelligibly.",
    "COMPLEMENTARY LEARNING STANDARD": "2.1.1 Give very basic personal information.",
    "OBJEKTIF PEMBELAJARAN": "Pupils identify three classroom objects and describe one feature of each object.",
    "KRITERIA KEJAYAAN": "Three matching object names and one spoken explanation.",
    "BAHAN BANTU MENGAJAR": "Student's Book, picture cards and object labels.",
    "SET INDUKSI": "Teacher displays three familiar classroom objects. Pupils name each one.",
    "AKTIVITI UTAMA": (
        "Activity 1\nTeacher models the vocabulary using picture cards. "
        "Pupils practise naming the objects in pairs.\n"
        "Activity 2\nPupils match object cards and describe one feature. "
        "Teacher checks each pupil's response.\n"
        "Activity 3\nPupils explain their answers to a partner and correct errors."
    ),
    "PENTAKSIRAN": "Teacher checks three matching answers and one individual explanation.",
    "PENUTUP": "Pupils state two new words learnt today.",
    "PEMULIHAN / PENGAYAAN": "Use labelled pictures for remediation; describe a fourth object for enrichment.",
}


def _pdf(file, outdir, profile):
    outdir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["libreoffice", "-env:UserInstallation=file://" + str(profile),
         "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(file)],
        text=True, capture_output=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-800:]
    generated = outdir / (file.stem + ".pdf")
    assert generated.is_file(), (file, proc.stdout, proc.stderr)
    return generated


def test_english_native_word_pastel_does_not_add_a4_pages(tmp_path):
    validate_word_function_snapshot()  # strict existing production parity gate
    pairs = []
    for year, lesson in ((2, 1), (4, 6), (6, 16)):
        origin = tmp_path / "base" / f"English_Y{year}_L{lesson:03d}.docx"
        styled = tmp_path / "styled" / origin.name
        origin.parent.mkdir(exist_ok=True)
        styled.parent.mkdir(exist_ok=True)
        write_word(year, lesson, SOURCE, origin)
        original_bytes = origin.read_bytes()
        updated = style_three_table_word_bytes(original_bytes, "E9F3F9")
        assert updated != original_bytes
        before, after = Document(BytesIO(original_bytes)), Document(BytesIO(updated))
        assert len(before.tables) == len(after.tables) == 3
        before_text = "\n".join(c.text for t in before.tables for row in t.rows for c in row.cells)
        after_text = "\n".join(c.text for t in after.tables for row in t.rows for c in row.cells)
        assert before_text == after_text
        assert SOURCE["AKTIVITI UTAMA"].splitlines()[0] in after_text
        assert all("____" not in after.tables[0].cell(n, 1).text for n in (2, 3, 4, 5, 6))
        styled.write_bytes(updated)
        pairs.append((origin, styled))

    for original, styled in pairs:
        base_pdf = _pdf(original, tmp_path / "basepdf", tmp_path / "lo-base")
        styled_pdf = _pdf(styled, tmp_path / "styledpdf", tmp_path / "lo-styled")
        pre = PdfReader(str(base_pdf)).pages
        post = PdfReader(str(styled_pdf)).pages
        assert len(post) == len(pre) == 1, (styled.name, len(pre), len(post))
        for page in post:
            assert abs(float(page.mediabox.width) - 595.28) < 2
            assert abs(float(page.mediabox.height) - 841.89) < 2
            txt = page.extract_text()
            assert "Activity" in txt and "Reflection" in txt
