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
from web.rph_equal_width_20261121 import equal_width_four_table_bytes
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
        assert doc.paragraphs[0].text == (
            "DAILY LESSON PLAN" if subject == "English"
            else "RANCANGAN PENGAJARAN HARIAN"
        )
        # The title belongs outside the first pastel box in every year.
        with ZipFile(BytesIO(upgraded)) as archive:
            root = etree.fromstring(archive.read("word/document.xml"))
        body = root.find(W + "body")
        first_table = body.find(W + "tbl")
        title_node = next(p for p in body.findall(W + "p")
                          if any((n.text or "").strip() in
                                 ("RANCANGAN PENGAJARAN HARIAN", "DAILY LESSON PLAN")
                                 for n in p.iter(W + "t")))
        assert body.index(title_node) < body.index(first_table)
        props = title_node.find(W + "pPr")
        assert props.find(W + "jc").get(W + "val") == "center"
        assert props.find(W + "pBdr") is None
        assert props.find(W + "shd") is None
        hcells = first_table.find(W + "tr").findall(W + "tc")
        assert [len(c.findall(W + "p")) for c in hcells] == [3, 5]
        for cell, stop in zip(hcells, ("2050", "1430")):
            for p in cell.findall(W + "p"):
                tabs = p.find(W + "pPr/" + W + "tabs")
                assert len(tabs.findall(W + "tab")) == 1
                assert tabs.find(W + "tab").get(W + "pos") == stop
                assert p.find(W + "pPr/" + W + "jc").get(W + "val") == "left"
        header = doc.tables[0]
        assert len(header.columns) == 2
        teacher = header.cell(0, 1).text
        assert ("Kelas" in teacher or "Class" in teacher), subject
        assert ("Tarikh" in teacher or "Date" in teacher), subject
        assert "____" not in teacher
        assert "Mata Pelajaran" in header.cell(0, 0).text or "Subject" in header.cell(0, 0).text
        assert header.columns[0].width > header.columns[1].width
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
    for subject in ("Bahasa Melayu", "English", "Matematik", "Sejarah", "Pendidikan Muzik",
                    "Pendidikan Jasmani dan Pendidikan Kesihatan", "Pendidikan Moral",
                    "Pendidikan Seni Visual", "Reka Bentuk dan Teknologi"):
        original = fixture(subject)
        fill = color_for_state({"task": "rph", "subject": subject})
        updated = equal_width_four_table_bytes(premium_header_bytes(style_three_table_word_bytes(original, fill), fill))
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
        # Inspect the rendered PDF font, not merely the Word OOXML flags.
        import fitz
        with fitz.open(str(out / (word.stem + ".pdf"))) as real_pdf:
            spans = [span for block in real_pdf[0].get_text("dict")["blocks"]
                     for line in block.get("lines", []) for span in line["spans"]]
        assert any("Aktiviti 1" in span["text"]
                   and "Bold" in span["font"] for span in spans), subject
        assert any("Murid membaca petikan" in span["text"]
                   and "Bold" not in span["font"] for span in spans), subject



def test_all_four_outer_table_edges_have_the_same_width_for_nine_subjects():
    """Native header, standards, activities and reflection use one fixed grid."""
    cases = (
        "Bahasa Melayu", "English", "Matematik", "Sejarah", "Pendidikan Muzik",
        "Pendidikan Jasmani dan Pendidikan Kesihatan",
        "Pendidikan Moral", "Pendidikan Seni Visual", "Reka Bentuk dan Teknologi",
    )
    for subject in cases:
        fill = color_for_state({"task": "rph", "subject": subject})
        original = fixture(subject)
        header = premium_header_bytes(style_three_table_word_bytes(original, fill), fill)
        aligned = equal_width_four_table_bytes(header)
        assert aligned != header, subject
        assert xml_tokens(aligned) == xml_tokens(header), subject
        assert equal_width_four_table_bytes(aligned) == aligned, subject
        with ZipFile(BytesIO(header)) as a, ZipFile(BytesIO(aligned)) as b:
            assert a.namelist() == b.namelist()
            for name in a.namelist():
                if name != "word/document.xml":
                    assert a.read(name) == b.read(name), (subject, name)
            root = etree.fromstring(b.read("word/document.xml"))
        table_nodes = root.find(W + "body").findall(W + "tbl")
        assert len(table_nodes) == 4
        widths = []
        for index, table in enumerate(table_nodes):
            props = table.find(W + "tblPr")
            outer = props.find(W + "tblW")
            assert outer.get(W + "type") == "dxa"
            widths.append(int(outer.get(W + "w")))
            assert props.find(W + "tblInd").get(W + "w") == "0"
            assert props.find(W + "jc").get(W + "val") == "left"
            cols = table.find(W + "tblGrid").findall(W + "gridCol")
            assert len(cols) == (2, 2, 3, 2)[index]
            assert sum(int(col.get(W + "w")) for col in cols) == widths[-1]
            expected = [int(col.get(W + "w")) for col in cols]
            for row in table.findall(W + "tr"):
                assert [int(cell.find(W + "tcPr").find(W + "tcW").get(W + "w"))
                        for cell in row.findall(W + "tc")] == expected
        assert len(set(widths)) == 1, (subject, widths)
        assert "____" not in Document(BytesIO(aligned)).tables[0].cell(0, 1).text
        assert int(table_nodes[0].find(W + "tblGrid").findall(W + "gridCol")[0].get(W + "w")) > int(table_nodes[0].find(W + "tblGrid").findall(W + "gridCol")[1].get(W + "w"))


def test_equal_width_fails_closed_when_document_has_unapproved_table_count():
    original = fixture("Bahasa Melayu")
    assert equal_width_four_table_bytes(original) == original


def test_real_native_word_main_activity_titles_are_bold_on_separate_lines():
    """Teacher-facing Word: existing title lines bold; teaching text unchanged."""
    from web.rph_reference_style_20261121 import style_three_table_word_bytes

    for subject in ("Bahasa Melayu", "English", "Matematik", "Sejarah", "Pendidikan Muzik",
                    "Pendidikan Jasmani dan Pendidikan Kesihatan", "Pendidikan Moral",
                    "Pendidikan Seni Visual", "Reka Bentuk dan Teknologi"):
        document = Document(BytesIO(fixture(subject)))
        activity = document.tables[1].cell(2, 1)
        heading = "Activity" if subject == "English" else "Aktiviti"
        activity.text = (
            f"{heading} 1 – Membaca dan mengenal pasti\n"
            "Guru menerangkan langkah dan murid membaca petikan.\n"
            f"{heading} 2 – Membandingkan jawapan\n"
            "Murid menjawab soalan secara berpasangan.\n"
            f"{heading} 3 – Pentaksiran individu\n"
            "Guru menyemak jawapan yang dihasilkan."
        )
        original_text = activity.text
        buf = BytesIO()
        document.save(buf)
        raw = buf.getvalue()
        styled = style_three_table_word_bytes(
            raw, color_for_state({"task": "rph", "subject": subject})
        )
        result = Document(BytesIO(styled))
        after = result.tables[1].cell(2, 1)
        assert after.text == original_text, subject
        assert xml_tokens(raw) == xml_tokens(styled), subject
        runs = after.paragraphs[0].runs
        assert any(r.bold and f"{heading} 1" in r.text for r in runs), subject
        assert any(r.bold and f"{heading} 2" in r.text for r in runs), subject
        assert any(r.bold and f"{heading} 3" in r.text for r in runs), subject
        for sentence in (
            "Guru menerangkan langkah", "Murid menjawab soalan",
            "Guru menyemak jawapan",
        ):
            assert any(sentence in r.text and not r.bold for r in runs), (subject, sentence)
        assert not any("____" in r.text for r in runs)


def test_bm_kp2027_teacher_panel_neutral_and_no_optional_rows_created():
    """The right teacher panel is neutral; missing source fields stay missing."""
    from docx.oxml.ns import qn
    for subject in ("Bahasa Melayu", "English", "Pendidikan Moral"):
        source = Document(BytesIO(fixture(subject)))
        table = source.tables[0]
        # Deliberately absent optional teaching rows: do not invent them.
        for i in reversed(range(len(table.rows))):
            if table.cell(i, 0).text in ("EMK / Nilai", "KBAT / PAK21"):
                table._tbl.remove(table.rows[i]._tr)
        stream = BytesIO()
        source.save(stream)
        raw = stream.getvalue()
        fill = color_for_state({"task": "rph", "subject": subject})
        updated = premium_header_bytes(style_three_table_word_bytes(raw, fill), fill)
        doc = Document(BytesIO(updated))
        assert len(doc.tables) == 4
        header = doc.tables[0]
        assert header.cell(0, 0)._tc.get_or_add_tcPr().find(W + "shd").get(W + "fill") == fill.upper()
        assert header.cell(0, 1)._tc.get_or_add_tcPr().find(W + "shd").get(W + "fill") == "F5F7FA"
        body = "\n".join(cell.text for table in doc.tables
                         for row in table.rows for cell in row.cells)
        assert "EMK / Nilai" not in body
        assert "KBAT / PAK21" not in body
        assert xml_tokens(updated) == xml_tokens(raw)
