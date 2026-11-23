"""Native RPH PDF pastel must not rewrite content, class metadata, page size, or links."""
from io import BytesIO
from pathlib import Path

import fitz
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from web.rph_reference_pdf_style_20261121 import (
    MARKER, install, style_pdf_bytes, style_pdf_path,
)
from web.rph_reference_style_20261121 import color_for_state


SUBJECTS = (
    "Bahasa Melayu", "English", "Matematik", "Pendidikan Islam",
    "Sejarah", "Pendidikan Muzik",
    "Pendidikan Jasmani dan Pendidikan Kesihatan",
    "Pendidikan Moral", "Pendidikan Seni Visual", "Reka Bentuk dan Teknologi",
)


def _pdf(title="RANCANGAN PENGAJARAN HARIAN"):
    stream = BytesIO()
    page = Canvas(stream, pagesize=A4)
    page.setFont("Helvetica-Bold", 14)
    page.drawCentredString(298, 800, title)
    page.setFont("Helvetica", 9)
    rows = (
        ("MATA PELAJARAN", "Bahasa Melayu"),
        ("TAHUN/TINGKATAN", "Tahun 3"),
        ("KELAS", ""),
        ("TARIKH", ""),
        ("MASA", ""),
        ("BILANGAN MURID", ""),
        ("STANDARD KANDUNGAN", "1.1 Mendengar dan bertutur"),
        ("STANDARD PEMBELAJARAN", "1.1.1 Mengenal pasti dan menyebut."),
        ("OBJEKTIF PEMBELAJARAN", "Murid menerangkan tiga fakta."),
    )
    for i, (label, value) in enumerate(rows):
        y = 760 - i*23
        page.rect(35, y-7, 520, 20)
        page.line(195, y-7, 195, y+13)
        page.drawString(42, y, label)
        if value:
            page.drawString(202, y, value)
    page.drawString(42, 480, "SET INDUKSI")
    page.drawString(42, 455, "AKTIVITI UTAMA")
    page.drawString(42, 430, "PENTAKSIRAN")
    page.drawString(42, 405, "PENUTUP")
    page.drawString(42, 380, "PEMULIHAN / PENGAYAAN")
    page.drawString(42, 355, "REFLEKSI")
    page.save()
    return stream.getvalue()


def _inspect(payload):
    pdf = fitz.open(stream=payload, filetype="pdf")
    try:
        return (tuple(page.get_text(sort=False) for page in pdf),
                tuple((page.rect.width, page.rect.height) for page in pdf),
                tuple(len(page.get_links()) for page in pdf),
                tuple(len(page.get_drawings()) for page in pdf),
                pdf.metadata.get("keywords") or "")
    finally:
        pdf.close()


def test_ten_sk_subject_colors_keep_all_pdf_text_and_one_page_a4():
    original = _pdf()
    txt, dimensions, links, drawings, _ = _inspect(original)
    for subject in SUBJECTS:
        state = {"task": "rph", "subject": subject}
        color = color_for_state(state)
        assert color and len(color) == 6, subject
        styled = style_pdf_bytes(original, color)
        assert styled != original, subject
        new_text, new_sizes, new_links, shapes, keywords = _inspect(styled)
        assert new_text == txt, subject
        assert new_sizes == dimensions, subject
        assert new_links == links, subject
        assert len(new_sizes) == 1
        assert abs(new_sizes[0][0] - 595.28) < 1
        assert abs(new_sizes[0][1] - 841.89) < 1
        assert shapes[0] > drawings[0], subject
        assert MARKER in keywords, subject
        assert style_pdf_bytes(styled, color) == styled, subject
        # PDF metadata previously empty must remain blank; no underscores added.
        assert "____" not in new_text[0]


def test_english_and_non_rph_are_styled_only_when_title_and_subject_match():
    english = _pdf("DAILY LESSON PLAN")
    styled = style_pdf_bytes(english, color_for_state({"task": "rph", "subject": "English"}))
    assert styled != english
    assert _inspect(styled)[0] == _inspect(english)[0]
    no_title = _pdf("TEACHER WORKSHEET")
    assert style_pdf_bytes(no_title, "E9F3F9") == no_title
    assert style_pdf_bytes(b"not a PDF", "EAF1FB") == b"not a PDF"


def test_reference_subjects_never_change_pdf_or_teacher_download(tmp_path):
    path = tmp_path / "lesson.pdf"
    original = _pdf()
    class Runtime:
        def __init__(self):
            self.calls = 0
        def create_pdf_file(self, state, text, chat):
            self.calls += 1
            path.write_bytes(original)
            return str(path)
    runtime = Runtime()
    assert install(runtime)
    first = runtime.create_pdf_file
    assert install(runtime) and runtime.create_pdf_file is first
    for state in (
        {"task": "rph", "subject": "Science"},
        {"task": "rph", "subject": "Matematik", "curriculum_version": "DLP"},
        {"task": "rph", "subject": "English", "programme": "PPKI"},
        {"task": "rph", "subject": "Bahasa Arab"},
        {"task": "rpt", "subject": "Bahasa Melayu"},
    ):
        assert runtime.create_pdf_file(state, "real curriculum text", "test") == str(path)
        assert path.read_bytes() == original, state
    assert runtime.calls == 5
    assert runtime.create_pdf_file({"task": "rph", "subject": "Bahasa Melayu"}, "", "test") == str(path)
    assert path.read_bytes() != original
    assert _inspect(path.read_bytes())[0] == _inspect(original)[0]


def test_path_skips_unknown_pdf_and_invalid_color(tmp_path):
    missing = tmp_path / "missing.pdf"
    assert style_pdf_path(missing, "EAF1FB") is False
    text_file = tmp_path / "invalid.docx"
    text_file.write_bytes(b"not a PDF")
    assert style_pdf_path(text_file, "EAF1FB") is False
    try:
        style_pdf_bytes(_pdf(), "XY0000")
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid RGB must be rejected")


def test_reportlab_separate_rule_grid_colors_full_label_cell():
    """Regression for production ReportLab's individual h/v table lines."""
    buffer = BytesIO()
    page = Canvas(buffer, pagesize=A4)
    page.setFont("Helvetica-Bold", 14)
    page.drawCentredString(298, 800, "RANCANGAN PENGAJARAN HARIAN")
    page.setFont("Helvetica", 9)
    left, divider, right = 35, 195, 555
    top, middle, bottom = 760, 740, 720
    for y in (top, middle, bottom):
        page.line(left, y, right, y)
    for x in (left, divider, right):
        page.line(x, bottom, x, top)
    page.drawString(42, 745, "MATA PELAJARAN")
    page.drawString(202, 745, "Matematik")
    page.drawString(42, 725, "STANDARD KANDUNGAN")
    page.drawString(202, 725, "4.1")
    page.save()

    original = buffer.getvalue()
    colored = style_pdf_bytes(original, "F0EBFA")
    before = fitz.open(stream=original, filetype="pdf")
    after = fitz.open(stream=colored, filetype="pdf")
    try:
        assert before[0].get_text() == after[0].get_text()
        assert len(before) == len(after) == 1
        # A full label cell should be filled: 160 pt, not a text-width strip.
        shaded = [
            item["rect"] for item in after[0].get_drawings()
            if item.get("fill") is not None and
            155 <= item["rect"].width <= 165 and
            18 <= item["rect"].height <= 22
        ]
        assert len(shaded) >= 2, shaded
        assert all(rect.x1 <= divider+2 for rect in shaded)
    finally:
        before.close()
        after.close()



def test_pdf_title_box_width_follows_actual_three_table_outer_grid():
    """Native RPH title frame shares x0/x1 with the rows below."""
    original = _pdf()
    baseline = fitz.open(stream=original, filetype="pdf")
    try:
        expected = [
            d["rect"] for d in baseline[0].get_drawings()
            if 500 <= d["rect"].width <= 530
            and d["rect"].y0 > 60
            and d["rect"].height <= 25
        ]
        assert len(expected) >= 2
        x0, x1 = expected[0].x0, expected[0].x1
        for rect in expected:
            assert abs(rect.x0-x0) < .25
            assert abs(rect.x1-x1) < .25
    finally:
        baseline.close()
    for subject in SUBJECTS:
        fill = color_for_state({"task":"rph", "subject":subject})
        styled = style_pdf_bytes(original, fill)
        with fitz.open(stream=styled, filetype="pdf") as pdf:
            frames = [
                d["rect"] for d in pdf[0].get_drawings()
                if d.get("fill") is not None and d["rect"].y0 < 65
                and d["rect"].width > 450
            ]
            assert frames, subject
            assert any(abs(rect.x0-x0)<.5 and abs(rect.x1-x1)<.5
                       for rect in frames), (subject, frames)
            assert pdf[0].get_text() == _inspect(original)[0][0]
            assert len(pdf) == 1


def test_pdf_title_box_fails_closed_without_repeated_source_grid():
    """A single unknown rectangle cannot define an authoritative page margin."""
    stream = BytesIO()
    page = Canvas(stream, pagesize=A4)
    page.setFont("Helvetica-Bold", 14)
    page.drawCentredString(298, 800, "RANCANGAN PENGAJARAN HARIAN")
    page.rect(35, 690, 520, 20)
    page.drawString(45, 695, "Tajuk")
    page.save()
    result = style_pdf_bytes(stream.getvalue(), "EAF1FB")
    with fitz.open(stream=result, filetype="pdf") as pdf:
        boxes = [
            d["rect"] for d in pdf[0].get_drawings()
            if d.get("fill") is not None and d["rect"].y0 < 60
        ]
        assert boxes and max(rect.width for rect in boxes) < 400
