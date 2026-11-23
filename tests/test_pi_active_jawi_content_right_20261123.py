"""Fail-closed PI ACTIVE Jawi Word alignment, not the retired 696 archive."""
from collections import Counter
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.enum.table import WD_TABLE_DIRECTION
from docx.shared import Cm
from lxml import etree

from web.rph_active_pi_rtl_alignment_20261123 import align_active_pi_rtl_value_bytes
from web.rph_reference_style_20261121 import (
    color_for_state, style_three_table_word_bytes, style_word_path,
    _preserves_source_content,
)
from web.rph_premium_header_20261121 import premium_header_bytes
from web.rph_equal_width_20261121 import equal_width_four_table_bytes

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def native_pi_word():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.15)
    doc.add_paragraph("رنچڠن ڤڠاجرن هارين")
    details = doc.add_table(rows=0, cols=2)
    details.table_direction = WD_TABLE_DIRECTION.RTL
    rows = [
        ("مات ڤلاجرن", "ڤنديديقن اسلام"),
        ("تاهون / تيڠکتن", "تاهون ٣"),
        ("تاريخ", ""),
        ("هاري", ""),
        ("ماس", ""),
        ("کلس", ""),
        ("بيلڠن موريد", ""),
        ("تاجوق", "عقيدة دان كهيدوڤن"),
        ("ستاندرد کاندوڠن", "1.1 مڠنل دان مڠعملكن علمو"),
        ("ستاندرد ڤمبلاجرن", "1.1.1 مڠهوريكن ڤمبلاجرن دڠن بتول"),
    ]
    for label, value in rows:
        r = details.add_row()
        r.cells[0].text = label
        r.cells[1].text = value
    phases = doc.add_table(rows=0, cols=3)
    phases.table_direction = WD_TABLE_DIRECTION.RTL
    for label, value in (
        ("فاسا", "ڤڠاجرن"),
        ("ست ايندوکسي", "ݢورو منرڠكن توجوان ڤمبلاجرن"),
        ("اکتيۏيتي اوتام", "اکتيۏيتي 1 – موريد ممباچ دان منوليس\n"
                            "موريد مڠنل ڤستي ماكلومت، ݢورو ممبري بيمبيڠن.\n"
                            "اکتيۏيتي 2 – موريد منرڠكن دليل."),
        ("ڤنوتوڤ", "موريد مروموسكن ڤمبلاجرن هارين"),
    ):
        r = phases.add_row()
        r.cells[0].text = label
        r.cells[1].text = value
    footer = doc.add_table(rows=2, cols=2)
    footer.table_direction = WD_TABLE_DIRECTION.RTL
    footer.cell(0, 0).text = "ڤموليهن"
    footer.cell(0, 1).text = "لاتيهن ڤموليهن دڠن بيمبيڠن"
    footer.cell(1, 0).text = "رفليكسي"
    footer.cell(1, 1).text = "30 murid mencapai objektif."
    buff = BytesIO()
    doc.save(buff)
    return buff.getvalue()


def formatted_original():
    source = native_pi_word()
    fill = color_for_state({"task": "rph", "subject": "Pendidikan Islam"})
    result = equal_width_four_table_bytes(
        premium_header_bytes(style_three_table_word_bytes(source, fill),
                             fill, rtl_jawi=True), rtl_jawi=True)
    return source, result


def test_only_source_values_move_to_physical_rtl_right_without_losing_activity():
    source, before = formatted_original()
    with ZipFile(BytesIO(before)) as z:
        xml = etree.fromstring(z.read("word/document.xml"))
        body = xml.find(W+"body")
        tbls = body.findall(W+"tbl")
        assert len(tbls)==4
        header = tbls[0].find(W+"tr").findall(W+"tc")
        assert "ڤنديديقن اسلام" in "".join(n.text or "" for n in header[0].iter(W+"t"))
        assert "کلس" in "".join(n.text or "" for n in header[1].iter(W+"t"))
        for i, tb in enumerate(tbls[1:]):
            assert tb.find(W+"tblPr/"+W+"bidiVisual") is not None
            assert all(len(x.findall(W+"tc")) == (2,3,2)[i] for x in tb.findall(W+"tr"))
        val = tbls[2].findall(W+"tr")[2].findall(W+"tc")[1].find(W+"p")
        assert any("\u0600" <= c <= "\u08ff" for c in "".join(n.text or "" for n in val.iter(W+"t")))
        assert val.find(W+"pPr/"+W+"jc") is None, etree.tostring(val, encoding="unicode")[:1200]
    after = align_active_pi_rtl_value_bytes(before)
    if after == before:
        with ZipFile(BytesIO(before)) as z:
            root = etree.fromstring(z.read("word/document.xml"))
            body = root.find(W + "body")
            tables = body.findall(W + "tbl")
            parts = [t.findall(W + "tr") for t in tables]
            detail = {
                "title": ["".join(n.text or "" for n in p.iter(W+"t")) for p in body.findall(W+"p")],
                "table_sizes": [[len(row.findall(W+"tc")) for row in rows] for rows in parts],
                "bidi": [t.find(W+"tblPr/"+W+"bidiVisual") is not None for t in tables],
                "header0": "".join(n.text or "" for n in parts[0][0].findall(W+"tc")[0].iter(W+"t")),
                "header1": "".join(n.text or "" for n in parts[0][0].findall(W+"tc")[1].iter(W+"t")),
                "value": "".join(n.text or "" for n in parts[2][2].findall(W+"tc")[1].iter(W+"t")),
            }
        assert after != before, detail
    assert _preserves_source_content(before, after)
    assert _preserves_source_content(source, after)
    assert align_active_pi_rtl_value_bytes(after) == after
    doc = Document(BytesIO(after))
    assert doc.paragraphs[0].text == "رنچڠن ڤڠاجرن هارين"
    assert len(doc.tables) == 4
    assert doc.tables[0].cell(0, 0).text.startswith("مات ڤلاجرن")
    assert "اکتيۏيتي 2" in doc.tables[2].cell(2, 1).text
    with ZipFile(BytesIO(after)) as z:
        root = etree.fromstring(z.read("word/document.xml"))
        tables = root.find(W + "body").findall(W + "tbl")
        assert all(t.find(W + "tblPr/" + W + "bidiVisual") is not None for t in tables)
        p = tables[2].findall(W + "tr")[2].findall(W + "tc")[1].find(W + "p")
        assert p.find(W + "pPr/" + W + "jc").get(W + "val") == "left"
        assert p.find(W + "pPr/" + W + "bidi").get(W + "val") == "1"
        latin = tables[3].findall(W + "tr")[1].findall(W + "tc")[1].find(W + "p")
        # Latin teacher-entered reflection is NOT rewritten or reoriented.
        assert latin.find(W + "pPr/" + W + "jc") is None
        assert "30 murid mencapai objektif." in "".join(latin.itertext())


def test_plain_legacy_and_non_jawi_document_fail_closed():
    source, before = formatted_original()
    assert align_active_pi_rtl_value_bytes(source) == source
    doc = Document(BytesIO(before))
    doc.paragraphs[0].text = "RANCANGAN PENGAJARAN HARIAN"
    stream = BytesIO()
    doc.save(stream)
    unknown = stream.getvalue()
    assert align_active_pi_rtl_value_bytes(unknown) == unknown
    assert align_active_pi_rtl_value_bytes(b"broken") == b"broken"


def test_actual_native_word_style_path_preserves_all_source_text(tmp_path):
    source = native_pi_word()
    path = tmp_path / "active_PI_RPH.docx"
    path.write_bytes(source)
    fill = color_for_state({"task": "rph", "subject": "Pendidikan Islam"})
    assert style_word_path(path, fill, premium_header=True, rtl_jawi=True)
    result = path.read_bytes()
    assert _preserves_source_content(source, result)
    doc = Document(BytesIO(result))
    assert doc.paragraphs[0].text == "رنچڠن ڤڠاجرن هارين"
    assert "موريد مڠنل ڤستي ماكلومت" in doc.tables[2].cell(2, 1).text
    assert len(doc.tables) == 4
    assert not style_word_path(path, fill, premium_header=True, rtl_jawi=True)


def test_real_a4_print_keeps_jawi_within_page(tmp_path):
    import shutil
    import subprocess
    import fitz
    assert shutil.which("libreoffice")
    data = native_pi_word()
    word = tmp_path / "source.docx"
    word.write_bytes(data)
    fill = color_for_state({"task": "rph", "subject": "Pendidikan Islam"})
    assert style_word_path(word, fill, premium_header=True, rtl_jawi=True)
    converted = subprocess.run(
        ["libreoffice", "-env:UserInstallation=" + (tmp_path / "profile").as_uri(),
         "--headless", "--convert-to", "pdf", "--outdir", str(tmp_path), str(word)],
        capture_output=True, text=True, timeout=90,
    )
    assert converted.returncode == 0, converted.stderr
    with fitz.open(tmp_path / "source.pdf") as pdf:
        assert len(pdf) == 1
        page = pdf[0]
        assert abs(page.rect.width - 595.3) < 2
        assert abs(page.rect.height - 841.9) < 2
        words = page.get_text("words")
        assert len(words) > 20
        assert all(x0 >= -1 and y0 >= -1 and x1 <= page.rect.width + 1
                   and y1 <= page.rect.height + 1
                   for x0, y0, x1, y1, *_ in words)
