"""Design-only audit of all 120 reviewed Arabic RPH source records.

No synthetic lesson data, production credentials, billing, user metadata or
curriculum edits. A separate PDF readiness decision is still required.
"""
from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_TABLE_DIRECTION
import fitz

from web.arabic_rph_word import render_arabic_word


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "rph_standalone" / "bahasa_arab"
TEXT_KEYS = (
    "topic", "focus", "content_standard", "learning_standard",
    "objective", "success", "induction", "activity_1", "activity_2",
    "assessment", "closure", "materials", "reflection",
)
PDF_SAMPLES = tuple((year, lesson) for year in (2, 3) for lesson in range(1, 61))


def _plan(year, lesson):
    file = SOURCE / f"year{year}" / f"pdp_{lesson:03d}_ar.json"
    plan = json.loads(file.read_text(encoding="utf-8"))
    assert plan["year"] == year and plan["lesson"] == lesson, file
    return plan


def _render(plan):
    data = BytesIO()
    # Empty *teacher* fields must remain empty; source reflection remains
    # unchanged, including a manual-fill template in existing source data.
    render_arabic_word(plan, ("", "", "", "", None), "", data)
    return data.getvalue()


def _assert_design_and_source(raw, plan):
    doc = Document(BytesIO(raw))
    assert len(doc.tables) == 4, (plan["year"], plan["lesson"])
    assert all(t.table_direction == WD_TABLE_DIRECTION.RTL for t in doc.tables)
    assert all(t.alignment == WD_TABLE_ALIGNMENT.RIGHT for t in doc.tables)
    widths = [sum(c.width.mm for c in t.columns) for t in doc.tables]
    assert max(widths) - min(widths) < 0.8, (plan["year"], plan["lesson"], widths)
    assert all(abs(w - 187) < 1 for w in widths)
    header = doc.tables[0]
    assert len(header.columns) == 3
    assert header.columns[0].width.mm > (
        header.columns[1].width.mm + header.columns[2].width.mm
    ), "RTL wide lesson identity must remain RIGHT of small teacher panel"
    assert [r.cells[2].text for r in header.rows] == ["", "", "", ""]
    # Source SK/SP/activities must remain verbatim. Do not normalize,
    # regenerate, translate or shorten any lesson to fit the page.
    displayed = "\n".join(
        c.text for table in doc.tables for row in table.rows for c in row.cells
    )
    for field in TEXT_KEYS:
        assert plan[field] in displayed, (plan["year"], plan["lesson"], field)
    for standard in ("sk", "sp"):
        assert plan[standard] in displayed
    assert "الصف" in header.cell(0, 0).text
    assert "الحصّة" not in header.cell(0, 0).text
    assert "الحصة" not in header.cell(0, 0).text
    assert doc.paragraphs[0].runs[0].bold
    assert "اللغة العربية" in doc.paragraphs[0].text
    # RTL: Arabic activity labels are in their own cells, with bold Amiri.
    # The source activities in adjacent cells must remain normal, verbatim.
    phases = doc.tables[2]
    for row_index, label in ((2, "النشاط الأول"), (3, "النشاط الثاني")):
        heading_cell = phases.rows[row_index].cells[0]
        action_cell = phases.rows[row_index].cells[1]
        assert heading_cell.text.strip() == label, (plan["year"], plan["lesson"], label)
        assert any(run.bold and label in run.text
                   for para in heading_cell.paragraphs for run in para.runs)
        assert not any(run.bold and run.text.strip()
                       for para in action_cell.paragraphs for run in para.runs)
    return doc


def test_all_120_real_reviewed_arabic_lessons_keep_source_and_outer_grid():
    total = 0
    for year in (2, 3):
        for lesson in range(1, 61):
            plan = _plan(year, lesson)
            _assert_design_and_source(_render(plan), plan)
            total += 1
    assert total == 120


def test_all_120_real_arabic_lessons_word_to_pdf_a4(tmp_path):
    assert len(PDF_SAMPLES) == 120 and len(set(PDF_SAMPLES)) == 120
    assert shutil.which("libreoffice"), "Real Word-to-PDF converter required"
    inputs = []
    for year, number in PDF_SAMPLES:
        plan = _plan(year, number)
        data = _render(plan)
        _assert_design_and_source(data, plan)
        path = tmp_path / f"Arab_Y{year}_PdP{number:03d}.docx"
        path.write_bytes(data)
        inputs.append(path)
    pdfdir = tmp_path / "pdf"
    pdfdir.mkdir()
    proc = subprocess.run(
        [
            "libreoffice",
            "-env:UserInstallation=" + (tmp_path / "lo").as_uri(),
            "--headless", "--convert-to", "pdf",
            "--outdir", str(pdfdir),
            *(str(file) for file in inputs),
        ],
        capture_output=True, text=True, timeout=600,
    )
    assert proc.returncode == 0, proc.stderr[-1000:]
    assert len(inputs) == 120
    assert len(list(pdfdir.glob('Arab_Y*_PdP*.pdf'))) == 120, (
        'missing PDF outputs', proc.stdout[-1000:], proc.stderr[-1000:])
    for word in inputs:
        path = pdfdir / (word.stem + ".pdf")
        assert path.exists(), (word.name, proc.stdout, proc.stderr)
        with fitz.open(str(path)) as pdf:
            assert len(pdf) == 1, (word.name, len(pdf))
            page = pdf[0]
            assert abs(page.rect.width - 595.28) < 2
            assert abs(page.rect.height - 841.89) < 2
            assert page.get_text().strip(), word.name
            # Text extraction is not a final glyph/ligature approval, but
            # catch blank/tofu-only text and missing Amiri font substitution.
            # This inspects all 120 REAL PDF outputs, not synthetic fixtures.
            rendered_blocks = page.get_text("dict")["blocks"]
            spans = [span for block in rendered_blocks if block.get("type") == 0
                     for line in block.get("lines", []) for span in line["spans"]]
            arabic_spans = [span for span in spans if any(
                0x0600 <= ord(char) <= 0x08FF for char in span["text"])]
            assert arabic_spans, (word.name, "Arabic script not extractable")
            assert any("amiri" in str(span["font"]).casefold()
                       for span in arabic_spans), (word.name, "Arabic Amiri not embedded")
            for block in rendered_blocks:
                if block.get("type") == 0:
                    x0, y0, x1, y1 = block["bbox"]
                    assert -1 <= x0 < x1 <= page.rect.width + 1, word.name
                    assert -1 <= y0 < y1 <= page.rect.height + 1, word.name
            strokes = [
                fitz.Rect(d["rect"]) for d in page.get_drawings()
                if 523 < fitz.Rect(d["rect"]).width < 534
                and fitz.Rect(d["rect"]).height < 1.7
            ]
            assert len(strokes) >= 6, (word.name, len(strokes))
            assert max(p.x0 for p in strokes) - min(p.x0 for p in strokes) < 2
            assert max(p.x1 for p in strokes) - min(p.x1 for p in strokes) < 2
