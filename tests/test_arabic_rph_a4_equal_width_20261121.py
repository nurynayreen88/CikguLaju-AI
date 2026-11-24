"""Physical A4 regression for approved Arabic RTL RPH Word format.

Uses the real Arabic renderer, converts the DOCX to PDF in an isolated
LibreOffice profile, and checks all four full-width outer grid coordinates.
This does NOT make Arabic PDF a teacher-downloadable feature.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import shutil
import subprocess

from docx import Document
from docx.enum.table import WD_TABLE_DIRECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import fitz

from web.arabic_rph_word import render_arabic_word


SAMPLE = {
    "year": 2, "lesson": 1, "topic": "المدرسة", "focus": "الفصل",
    "pages": "2 & 4", "sk": "1.1", "sp": "1.1.1",
    "content_standard": "الاستماع",
    "learning_standard": "يسمع التلميذ",
    "objective": "يذكر التلميذ الكلمات",
    "success": "يذكر كلمتين",
    "induction": "يشاهد الصور",
    "activity_1": "يستمع إلى الكلمات",
    "activity_2": "يردد الكلمات",
    "assessment": "يسمي صورتين",
    "closure": "يلخص النشاط",
    "materials": "بطاقات",
    "reflection": "متابعة",
}


def test_approved_arabic_word_renders_physical_equal_width_a4(tmp_path):
    assert shutil.which("libreoffice"), "CI must install a real A4 Word renderer"
    docx = tmp_path / "arabic-approved-rtl.docx"
    with docx.open("wb") as file:
        render_arabic_word(
            SAMPLE, ("2 AMANAH", "", "08:00 - 09:00", "28", None),
            "متابعة", file,
        )
    document = Document(str(docx))
    assert len(document.tables) == 4
    assert document.paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.CENTER
    title_props = document.paragraphs[0]._p.get_or_add_pPr()
    assert title_props.find(qn("w:pBdr")) is None
    assert title_props.find(qn("w:shd")) is None
    identity_paras = document.tables[0].cell(0, 0).paragraphs
    assert len(identity_paras) == 3
    for paragraph in identity_paras:
        tabs = paragraph._p.get_or_add_pPr().find(qn("w:tabs"))
        assert tabs is not None
        stops = tabs.findall(qn("w:tab"))
        assert len(stops) == 1
        assert abs(int(stops[0].get(qn("w:pos"))) - 1758) < 10
        assert "\t" in paragraph.text
    assert all(t.table_direction == WD_TABLE_DIRECTION.RTL for t in document.tables)
    widths = [sum(col.width.mm for col in t.columns) for t in document.tables]
    assert max(widths)-min(widths) < .8, widths
    assert all(abs(x-187)<1 for x in widths)
    assert document.tables[0].rows[1].cells[2].text == ""
    identity = document.tables[0].rows[0].cells[0].text
    for token in ("المدرسة", "الفصل", "الصف"):
        assert token in identity

    isolated_profile = (tmp_path / "lo-profile").as_uri()
    proc = subprocess.run(
        [
            "libreoffice", "-env:UserInstallation=" + isolated_profile,
            "--headless", "--convert-to", "pdf",
            "--outdir", str(tmp_path), str(docx),
        ],
        capture_output=True, text=True, timeout=90, check=False,
    )
    path = docx.with_suffix(".pdf")
    assert proc.returncode == 0 and path.is_file(), (
        proc.returncode, proc.stdout, proc.stderr
    )
    with fitz.open(str(path)) as pdf:
        assert len(pdf) == 1, len(pdf)
        page = pdf[0]
        assert abs(page.rect.width-595.28) < 1
        assert abs(page.rect.height-841.89) < 1
        # Four 187 mm boxes from the actual PDF drawing operators.
        horizontal = [
            fitz.Rect(item["rect"]) for item in page.get_drawings()
            if 523 < fitz.Rect(item["rect"]).width < 534
            and fitz.Rect(item["rect"]).height < 1.7
        ]
        assert len(horizontal) >= 6, horizontal
        assert max(r.x0 for r in horizontal)-min(r.x0 for r in horizontal) < 2
        assert max(r.x1 for r in horizontal)-min(r.x1 for r in horizontal) < 2
        assert page.get_text().strip(), "Arabic renderer output must not be blank"
