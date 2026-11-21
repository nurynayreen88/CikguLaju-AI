"""Fail-closed PI Word header: narrow physical LEFT, Jawi RTL, no source loss.

Uses an exact synthetic version of the existing native PI/Jawi 3-table input.
Real authenticated PI PDF output remains a separate protected audit.
"""
from __future__ import annotations

from collections import Counter
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import subprocess

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_TABLE_DIRECTION
from docx.shared import Cm, Pt
from lxml import etree
from pypdf import PdfReader
import fitz

from web.rph_equal_width_20261121 import equal_width_four_table_bytes
from web.rph_premium_header_20261121 import premium_header_bytes
from web.rph_reference_style_20261121 import color_for_state, style_three_table_word_bytes

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
JAWI_META = (
    ("مات ڤلاجرن", "ڤنديديقن اسلام"),
    ("تاهون / تيڠکتن", "تاهون ٢"),
    ("تاريخ", ""),
    ("هاري", ""),
    ("ماس", "08:00 - 09:00"),
    ("کلس", "٢ امانه"),
    ("بيلڠن موريد", "٢٨"),
    ("تاجوق", "کبيهقن ديري"),
)


def fixture():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.15)
    sec.top_margin = sec.bottom_margin = Cm(1)
    doc.styles["Normal"].font.size = Pt(9)
    doc.add_paragraph("رنچڠن ڤڠاجرن هارين")
    info = doc.add_table(rows=0, cols=2)
    info.table_direction = WD_TABLE_DIRECTION.RTL
    info.alignment = WD_TABLE_ALIGNMENT.RIGHT
    for label, value in (*JAWI_META,
                         ("ستاندرد کاندوڠن", "1.1 منڠنل ڤركارا اوتام"),
                         ("ستاندرد ڤمبلاجرن", "1.1.1 منرڠکن ڤرلوکن")):
        row = info.add_row()
        row.cells[0].text = label
        row.cells[1].text = value
    activities = doc.add_table(rows=4, cols=3)
    activities.table_direction = WD_TABLE_DIRECTION.RTL
    activities.alignment = WD_TABLE_ALIGNMENT.RIGHT
    for index, (label, action) in enumerate((
        ("فاسا", "اکتيۏيتي ڤڠاجرن"),
        ("ست ايندوکسي", "ݢورو ممڤرکنلکن تاجوق"),
        ("اکتيۏيتي اوتام", "موريد منڠنل ڤستي دان منوليس جوابن"),
        ("ڤنوتوڤ", "موريد منرڠکن ڤمبلاجرن"),
    )):
        activities.cell(index, 0).text = label
        activities.cell(index, 1).text = action
    closing = doc.add_table(rows=2, cols=2)
    closing.table_direction = WD_TABLE_DIRECTION.RTL
    closing.alignment = WD_TABLE_ALIGNMENT.RIGHT
    closing.cell(0, 0).text = "ڤموليهن / ڤڠاياءن"
    closing.cell(0, 1).text = "لاتيهن ڤڠوکوهان"
    closing.cell(1, 0).text = "رفليكسي"
    closing.cell(1, 1).text = ""
    out = BytesIO()
    doc.save(out)
    return out.getvalue()


def tokens(data):
    with ZipFile(BytesIO(data)) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    return Counter(node.text for node in root.iter(W + "t"))


def test_jawi_short_left_teacher_long_right_source_tokens_and_fixed_grid():
    source = fixture()
    fill = color_for_state({"task": "rph", "subject": "Pendidikan Islam"})
    assert fill
    styled = style_three_table_word_bytes(source, fill)
    heading = premium_header_bytes(styled, fill, rtl_jawi=True)
    final = equal_width_four_table_bytes(heading, rtl_jawi=True)
    assert final != styled
    assert tokens(final) == tokens(styled)
    assert premium_header_bytes(final, fill, rtl_jawi=True) == final
    assert equal_width_four_table_bytes(final, rtl_jawi=True) == final
    doc = Document(BytesIO(final))
    assert len(doc.tables) == 4
    assert doc.tables[0].table_direction == WD_TABLE_DIRECTION.RTL
    assert doc.tables[0].alignment == WD_TABLE_ALIGNMENT.RIGHT
    assert doc.tables[0].columns[0].width > doc.tables[0].columns[1].width
    # RTL first logical column is physically RIGHT: identity on the right,
    # the short teacher block (second logical column) is physically LEFT.
    right = doc.tables[0].cell(0, 0).text
    left = doc.tables[0].cell(0, 1).text
    assert "مات ڤلاجرن" in right and "تاجوق" in right
    assert "کلس" in left and "تاريخ" in left
    assert "1.1.1" in doc.tables[1].cell(1, 1).text
    assert "____" not in left

    with ZipFile(BytesIO(final)) as zipped:
        root = etree.fromstring(zipped.read("word/document.xml"))
    tables = root.find(W + "body").findall(W + "tbl")
    assert len(tables) == 4
    widths = []
    for table in tables:
        pr = table.find(W + "tblPr")
        assert pr.find(W + "bidiVisual") is not None
        assert pr.find(W + "jc").get(W + "val") == "right"
        widths.append(int(pr.find(W + "tblW").get(W + "w")))
    assert len(set(widths)) == 1
    assert all(t.table_direction == WD_TABLE_DIRECTION.RTL for t in doc.tables)


def test_unrecognized_jawi_or_ltr_input_fails_closed():
    original = fixture()
    doc = Document(BytesIO(original))
    doc.tables[0].cell(3, 0).text = "Wrong Jawi label"
    out = BytesIO()
    doc.save(out)
    assert premium_header_bytes(out.getvalue(), "ECE4F6", rtl_jawi=True) == out.getvalue()
    unchanged = fixture()
    assert premium_header_bytes(unchanged, "ECE4F6") == unchanged


def test_pi_rtl_word_renders_a4_without_moving_source_text(tmp_path):
    fill = color_for_state({"task": "rph", "subject": "Pendidikan Islam"})
    docx = tmp_path / "pi-jawi-short-left.docx"
    docx.write_bytes(equal_width_four_table_bytes(
        premium_header_bytes(style_three_table_word_bytes(fixture(), fill),
                             fill, rtl_jawi=True), rtl_jawi=True))
    import shutil
    assert shutil.which("libreoffice"), "Install LibreOffice for real A4 validation"
    p = subprocess.run(["libreoffice",
                        "-env:UserInstallation=" + (tmp_path / "profile").as_uri(),
                        "--headless", "--convert-to", "pdf",
                        "--outdir", str(tmp_path), str(docx)],
                       capture_output=True, text=True, timeout=90)
    assert p.returncode == 0, p.stderr
    output = tmp_path / "pi-jawi-short-left.pdf"
    assert output.exists()
    pdf = PdfReader(str(output))
    assert len(pdf.pages) == 1
    assert abs(float(pdf.pages[0].mediabox.width)-595.28) < 2
    assert abs(float(pdf.pages[0].mediabox.height)-841.89) < 2
    # Check PHYSICAL PDF rules, not only equal OOXML widths. A past
    # LibreOffice RTL rendering difference shifted one of the tables.
    # For A4 with 1.15 cm margins, each approved table occupies 18.70 cm.
    with fitz.open(str(output)) as rendered:
        page = rendered[0]
        rules = [
            fitz.Rect(item["rect"]) for item in page.get_drawings()
            if 520 < fitz.Rect(item["rect"]).width < 538
            and fitz.Rect(item["rect"]).height < 1.7
        ]
        wide = [
            (item.get("type"), tuple(round(x, 1) for x in fitz.Rect(item["rect"])))
            for item in page.get_drawings()
            if fitz.Rect(item["rect"]).width > 1
        ]
        assert len(rules) >= 6, ("Jawi PDF drawing diagnostic", len(page.get_drawings()), wide[:75])
        assert max(r.x0 for r in rules)-min(r.x0 for r in rules) < 2, rules
        assert max(r.x1 for r in rules)-min(r.x1 for r in rules) < 2, rules
        # Neither Jawi text nor table geometry should exceed A4 bounds.
        for word in page.get_text("words"):
            assert word[0] >= -1 and word[2] <= page.rect.width + 1
            assert word[1] >= -1 and word[3] <= page.rect.height + 1

