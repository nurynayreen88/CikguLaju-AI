"""Non-destructive premium Word RPH banner: nine Latin/English SK families.

The fixture mirrors the audited native three-table renderer, not curriculum data.
"""
from collections import Counter
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.shared import Cm, Pt
from lxml import etree

from web.rph_premium_header_20261121 import premium_header_bytes
from web.rph_reference_style_20261121 import color_for_state, style_three_table_word_bytes

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def fixture(subject="Bahasa Melayu", *, year=3, enough_rows=True):
    en = subject == "English"
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(.75)
    doc.styles["Normal"].font.size = Pt(8.5)
    doc.add_paragraph("DAILY LESSON PLAN" if en else "RANCANGAN PENGAJARAN HARIAN")
    t = doc.add_table(rows=0, cols=2)
    meta = [
        ("Subject", "English") if en else ("Mata Pelajaran", subject),
        ("Year / Form", f"Year {year}") if en else ("Tahun/Tingkatan", f"Tahun {year}"),
        ("Date", "") if en else ("Tarikh", ""),
        ("Day", "") if en else ("Hari", ""),
        ("Time", "") if en else ("Masa", ""),
        ("Class", "") if en else ("Kelas", ""),
        ("Number of Pupils", "") if en else ("Bilangan Murid", ""),
        ("Topic", "Helping at Home") if en else ("Tajuk", "Bantu-membantu di Dapur"),
    ]
    for label, value in meta + [
        ("Standard Kandungan", "2.1 Asas membaca dan memahami"),
        ("Standard Pembelajaran", "2.1.1 Membaca dengan sebutan yang betul."),
        ("Objektif Pembelajaran", "Murid membaca petikan dan menjawab tiga soalan."),
        ("Kriteria Kejayaan", "Murid memberikan sekurang-kurangnya dua jawapan tepat."),
        ("EMK / Nilai", "Kerjasama dan tanggungjawab"),
        ("KBAT / PAK21", "Berkomunikasi secara berpasangan"),
        ("Pentaksiran", "Semakan individu"),
    ]:
        row = t.add_row()
        row.cells[0].text = label
        row.cells[1].text = value
    a = doc.add_table(rows=4, cols=3)
    for i, (phase, text) in enumerate([
        ("Fasa", "Aktiviti PdP"),
        ("Set Induksi", "Guru memperkenalkan tajuk."),
        ("Aktiviti Utama", "Aktiviti 1 – Baca dan cari bukti\nMurid membaca petikan."),
        ("Penutup", "Murid merumuskan hasil pembelajaran."),
    ]):
        a.cell(i, 0).text = phase
        a.cell(i, 1).text = text
    tail = doc.add_table(rows=2, cols=2)
    tail.cell(0, 0).text = "Pemulihan / Pengayaan"
    tail.cell(0, 1).text = "Bimbingan berpandu dan tugasan tambahan."
    tail.cell(1, 0).text = "Refleksi"
    tail.cell(1, 1).text = ""
    buff = BytesIO()
    doc.save(buff)
    return buff.getvalue()


def xml_tokens(data):
    with ZipFile(BytesIO(data)) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
    return Counter(t.text for t in root.iter(W + "t"))


def test_all_nine_legacy_subjects_keep_every_source_word_and_header_right():
    names = (
        "Bahasa Melayu", "English", "Matematik", "Sejarah",
        "Pendidikan Muzik", "Pendidikan Jasmani dan Pendidikan Kesihatan",
        "Pendidikan Moral", "Pendidikan Seni Visual", "Reka Bentuk dan Teknologi",
    )
    for subject in names:
        original = fixture(subject)
        fill = color_for_state({"task": "rph", "subject": subject})
        assert fill, subject
        styled = style_three_table_word_bytes(original, fill)
        upgraded = premium_header_bytes(styled, fill)
        doc = Document(BytesIO(upgraded))
        assert len(doc.tables) == 4, subject
        header = doc.tables[0]
        assert len(header.columns) == 2
        teacher = header.cell(0, 1).text
        assert ("Kelas" in teacher or "Class" in teacher), subject
        assert ("Tarikh" in teacher or "Date" in teacher), subject
        assert "____" not in teacher
        assert len(doc.tables[1].rows) == 7
        assert "2.1.1" in doc.tables[1].cell(1, 1).text
        assert "Aktiviti 1" in doc.tables[2].cell(2, 1).text
        assert xml_tokens(upgraded) == xml_tokens(styled), subject
        assert premium_header_bytes(upgraded, fill) == upgraded, subject
        with ZipFile(BytesIO(styled)) as before, ZipFile(BytesIO(upgraded)) as after:
            for name in before.namelist():
                if name != "word/document.xml":
                    assert before.read(name) == after.read(name), (subject, name)


def test_unexpected_or_specialty_layout_is_left_as_is():
    original = fixture()
    doc = Document(BytesIO(original))
    doc.add_table(rows=1, cols=2)
    output = BytesIO()
    doc.save(output)
    assert premium_header_bytes(output.getvalue(), "EAF1FB") == output.getvalue()
    for subject in ("Sains", "Science", "Bahasa Arab"):
        assert color_for_state({"task": "rph", "subject": subject}) is None
    assert color_for_state({"task": "rph", "subject": "Matematik", "curriculum": "DLP"}) is None
    assert color_for_state({"task": "rph", "subject": "English", "programme": "PPKI"}) is None


def test_broken_metadata_order_is_fail_closed():
    doc = Document(BytesIO(fixture()))
    doc.tables[0].cell(2, 0).text = "Incorrect field"
    output = BytesIO()
    doc.save(output)
    assert premium_header_bytes(output.getvalue(), "EAF1FB") == output.getvalue()


def test_word_to_pdf_a4_one_page(tmp_path):
    import subprocess
    from pypdf import PdfReader
    for subject in ("Bahasa Melayu", "English", "Matematik"):
        original = fixture(subject)
        fill = color_for_state({"task": "rph", "subject": subject})
        updated = premium_header_bytes(style_three_table_word_bytes(original, fill), fill)
        word = tmp_path / (subject.replace(" ", "_") + ".docx")
        word.write_bytes(updated)
        out = tmp_path / "pdf"
        out.mkdir(exist_ok=True)
        cmd = ["libreoffice", "-env:UserInstallation=file://" + str(tmp_path / "lo-profile"),
               "--headless", "--convert-to", "pdf", "--outdir", str(out), str(word)]
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        assert run.returncode == 0, run.stderr
        pages = PdfReader(str(out / (word.stem + ".pdf"))).pages
        assert len(pages) == 1
        assert abs(float(pages[0].mediabox.width) - 595.28) < 2
        assert abs(float(pages[0].mediabox.height) - 841.89) < 2
