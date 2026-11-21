"""Native PDF teacher box/outer-width parity without source lesson reconstruction."""
from collections import Counter
from io import BytesIO
from pathlib import Path

import fitz
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from web.rph_native_pdf_header_20261121 import premium_pdf_story
from web.rph_reference_pdf_style_20261121 import style_pdf_bytes
from web.rph_reference_style_20261121 import color_for_state

SUBJECTS = (
    "Bahasa Melayu", "English", "Matematik", "Sejarah", "Pendidikan Muzik",
    "Pendidikan Jasmani dan Pendidikan Kesihatan", "Pendidikan Moral",
    "Pendidikan Seni Visual", "Reka Bentuk dan Teknologi",
)


def fixture(subject):
    styles = getSampleStyleSheet()
    cell = ParagraphStyle("PDFCell", parent=styles["Normal"], fontName="Helvetica",
                          fontSize=7.75, leading=8.85)
    title = ParagraphStyle("PDFTitle", parent=styles["Title"], fontName="Helvetica-Bold",
                           fontSize=14, leading=16)
    en = subject == "English"
    pairs = [
        ("Subject", "English") if en else ("Mata Pelajaran", subject),
        ("Year / Form", "Year 3") if en else ("Tahun/Tingkatan", "Tahun 3"),
        ("Date", "") if en else ("Tarikh", ""),
        ("Day", "") if en else ("Hari", ""),
        ("Time", "") if en else ("Masa", ""),
        ("Class", "") if en else ("Kelas", ""),
        ("Number of Pupils", "") if en else ("Bilangan Murid", ""),
        ("Topic", "Helping at Home") if en else ("Tajuk", "Bantu-membantu di Dapur"),
        ("Standard Kandungan", "2.1 Asas membaca dan memahami"),
        ("Standard Pembelajaran", "2.1.1 Membaca dengan sebutan yang betul."),
        ("Objektif Pembelajaran", "Murid membaca petikan dan menjawab tiga soalan."),
        ("Kriteria Kejayaan", "Dua jawapan yang betul."),
        ("EMK / NILAI", "Kerjasama dan tanggungjawab"),
        ("KBAT / PAK21", "Think-Pair-Share"),
        ("Pentaksiran", "Guru menyemak bacaan dan respons individu."),
    ]
    rows = [[Paragraph(f"<b>{lab}</b>", cell), Paragraph(value, cell)]
            for lab, value in pairs]
    info = Table(rows, colWidths=[48 * mm, 124 * mm])
    info.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .5, colors.black)]))

    activities = [
        [Paragraph("<b>Fasa</b>", cell),
         Paragraph("<b>Aktiviti Pengajaran dan Pembelajaran</b>", cell),
         Paragraph("<b>Catatan</b>", cell)]
    ]
    for label, value in (
        ("Set Induksi", "Guru menunjukkan gambar dan mengaitkan pengalaman murid."),
        ("Aktiviti Utama", "Aktiviti 1: Murid membaca ayat secara berpandu. "
         "Aktiviti 2: Murid menjawab tiga soalan. Aktiviti 3: Murid berkongsi jawapan."),
        ("Penutup", "Murid menyatakan semula pembelajaran hari ini."),
    ):
        activities.append([Paragraph(label, cell), Paragraph(value, cell),
                           Paragraph("", cell)])
    phase = Table(activities, colWidths=[32 * mm, 112 * mm, 28 * mm])
    phase.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .5, colors.black)]))
    tail = Table([
        [Paragraph("<b>Pemulihan / Pengayaan</b>", cell),
         Paragraph("Bimbingan berfokus dan latihan tambahan.", cell)],
        [Paragraph("<b>Refleksi</b>", cell), Paragraph("", cell)],
    ], colWidths=[48 * mm, 124 * mm])
    tail.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .5, colors.black)]))
    title_text = "DAILY LESSON PLAN" if en else "RANCANGAN PENGAJARAN HARIAN"
    return [Paragraph(title_text, title), Spacer(1, 2 * mm), info,
            Spacer(1, 3 * mm), phase, Spacer(1, 3 * mm), tail]


def _text_objects(piece):
    if isinstance(piece, Paragraph):
        yield piece.getPlainText()
    elif isinstance(piece, Table):
        for row in piece._cellvalues:
            for cell in row:
                yield from _text_objects(cell)
    elif isinstance(piece, (list, tuple)):
        for item in piece:
            yield from _text_objects(item)


def _pdf(payload, path):
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=14 * mm,
                      rightMargin=14 * mm, topMargin=12 * mm,
                      bottomMargin=14 * mm).build(payload)
    return path.read_bytes()


def test_nine_subjects_same_width_teacher_right_short_and_source_preserved(tmp_path):
    for subject in SUBJECTS:
        state = {"task": "rph", "subject": subject}
        before = fixture(subject)
        original_text = Counter(_text_objects(before))
        next_story = premium_pdf_story(state, before)
        assert next_story is not before, subject
        assert Counter(_text_objects(next_story)) == original_text, subject

        banner = next_story[0]
        assert isinstance(banner, Table) and len(banner._cellvalues) == 1
        assert len(banner._cellvalues[0]) == 2
        assert abs(sum(banner._colWidths) - 172 * mm) < .001
        assert abs(sum(next_story[2]._colWidths) - 172 * mm) < .001
        assert abs(sum(next_story[4]._colWidths) - 172 * mm) < .001
        assert abs(sum(next_story[6]._colWidths) - 172 * mm) < .001
        teacher = list(_text_objects(banner._cellvalues[0][1]))
        assert ("Kelas" in teacher or "Class" in teacher), subject
        assert ("Tarikh" in teacher or "Date" in teacher), subject
        assert "____" not in " ".join(teacher)
        assert banner._colWidths[0] > banner._colWidths[1], subject
        identity_text = list(_text_objects(banner._cellvalues[0][0]))
        assert any(t in identity_text for t in ("Mata Pelajaran", "Subject")), subject

        baseline = _pdf(fixture(subject), tmp_path / (
            subject.replace(" ", "_") + "-original.pdf"))
        document = _pdf(next_story, tmp_path / (subject.replace(" ", "_") + ".pdf"))
        with (fitz.open(stream=baseline, filetype="pdf") as old_pdf,
              fitz.open(stream=document, filetype="pdf") as pdf):
            assert len(pdf) == len(old_pdf) == 1, subject
            text = pdf[0].get_text()
            assert "2.1.1" in text and "Aktiviti 1" in text and "Refleksi" in text
            assert "Kelas" in text or "Class" in text
            assert pdf[0].rect.width > 590 and pdf[0].rect.height > 840
            # Same original paragraph words after header reflow; do not
            # silently drop SK/SP, objectives or teacher metadata.
            words_before = Counter(word[4] for page in old_pdf
                                   for word in page.get_text("words"))
            words_after = Counter(word[4] for page in pdf
                                  for word in page.get_text("words"))
            assert words_before == words_after, subject

            teacher_label = "Class" if subject == "English" else "Kelas"
            teacher_boxes = pdf[0].search_for(teacher_label)
            assert teacher_boxes and min(box.x0 for box in teacher_boxes) > 310, subject
            assert "____" not in text
            # Confirm actual vector-rule alignment, not merely Table props.
            rules = [item["rect"] for item in pdf[0].get_drawings()
                     if item["rect"].width > 480
                     and item["rect"].height < 1.5]
            assert len(rules) >= 6, subject
            assert max(box.x0 for box in rules) - min(box.x0 for box in rules) < .6
            assert max(box.x1 for box in rules) - min(box.x1 for box in rules) < .6
        decorated = style_pdf_bytes(document, color_for_state(state))
        with (fitz.open(stream=decorated, filetype="pdf") as pdf,
              fitz.open(stream=document, filetype="pdf") as source_pdf):
            assert len(pdf) == len(source_pdf) == 1
            assert pdf[0].get_text() == source_pdf[0].get_text()


def test_specialty_and_unknown_layout_fail_closed():
    source = fixture("Bahasa Melayu")
    for state in (
        {"task": "rph", "subject": "Sains"},
        {"task": "rph", "subject": "Matematik", "curriculum_version": "DLP"},
        {"task": "rph", "subject": "English", "programme": "PPKI"},
        {"task": "rph", "subject": "Pendidikan Islam"},
        {"task": "rph", "subject": "Bahasa Arab"},
        {"task": "rpt", "subject": "Bahasa Melayu"},
    ):
        assert premium_pdf_story(state, source) is source, state

    damaged = fixture("Bahasa Melayu")
    damaged[2]._cellvalues[3][0] = Paragraph("Mislabeled", damaged[2]._cellvalues[3][0].style)
    assert premium_pdf_story({"task": "rph", "subject": "Bahasa Melayu"}, damaged) is damaged
    too_long = fixture("Bahasa Melayu")
    too_long[2]._cellvalues[7][1] = Paragraph("Topic " * 60, too_long[2]._cellvalues[7][1].style)
    assert premium_pdf_story({"task": "rph", "subject": "Bahasa Melayu"}, too_long) is too_long


def test_unapproved_titles_and_outer_grids_are_not_reflowed():
    state = {"task": "rph", "subject": "Bahasa Melayu"}
    for changed in ("wrong-title", "phase-width", "reflection-width",
                    "additional-flowable", "missing-spacer"):
        story = fixture("Bahasa Melayu")
        if changed == "wrong-title":
            story[0] = Paragraph("Different lesson format", story[0].style)
        elif changed == "phase-width":
            story[4]._colWidths[-1] += 8 * mm
        elif changed == "reflection-width":
            story[6]._colWidths[-1] += 8 * mm
        elif changed == "additional-flowable":
            story.append(Spacer(1, mm))
        else:
            story[5] = Paragraph("not a spacer", story[0].style)
        assert premium_pdf_story(state, story) is story, changed
    assert premium_pdf_story(None, fixture("Bahasa Melayu")) is not None


def test_source_app_uses_native_pdf_story_only_at_one_rph_build_site():
    source = (Path(__file__).resolve().parents[1] / "app.py").read_text("utf-8")
    needle = "story = premium_pdf_story(s, story)"
    assert source.count(needle) == 1
    where = source.index(needle)
    assert "story.append(tt)" in source[where - 380:where]
    assert "pdf.build(story,onFirstPage=_hf,onLaterPages=_hf)" in source[where:where + 450]


def test_native_pdf_activity_title_bold_preserves_real_paragraph_text(tmp_path):
    """The pre-render PDF story must preserve all source instruction wording."""
    from web.rph_native_pdf_header_20261121 import premium_pdf_story

    for subject in ("Bahasa Melayu", "English", "Matematik"):
        story = fixture(subject)
        activities = story[4]
        row = activities._cellvalues[2]
        heading = "Activity" if subject == "English" else "Aktiviti"
        old = row[1]
        row[1] = Paragraph(
            f"{heading} 1 - Membaca dan mengenal pasti<br/>"
            "Guru menerangkan dengan jelas.<br/>"
            f"{heading} 2 - Perbincangan kumpulan<br/>"
            "Murid menyiapkan latihan.<br/>"
            f"{heading} 3 - Pentaksiran individu<br/>"
            "Guru menyemak jawapan.",
            old.style,
        )
        unchanged_text = row[1].getPlainText()
        updated = premium_pdf_story({"task": "rph", "subject": subject}, story)
        actual = updated[4]._cellvalues[2][1]
        assert actual.getPlainText() == unchanged_text
        for n in (1, 2, 3):
            assert f"<b>{heading} {n} -" in actual.text
        assert "<b>Guru menerangkan" not in actual.text
        assert "<b>Murid menyiapkan" not in actual.text
        assert "<b>Guru menyemak" not in actual.text
        pdf_path = tmp_path / (subject.replace(" ", "_") + "_titles.pdf")
        _pdf(updated, pdf_path)
        from pypdf import PdfReader
        pdf = PdfReader(str(pdf_path))
        assert len(pdf.pages) >= 1
        content = " ".join(p.extract_text() for p in pdf.pages)
        assert heading + " 1" in content
        assert "Guru menerangkan dengan jelas" in content
