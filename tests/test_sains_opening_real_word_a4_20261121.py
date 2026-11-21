"""A4 smoke using actual app.py Word function with source-backed Sains PdP.

The full Telegram app is not imported (no webhook, DB writes or quota action).
This proves offline Word/PDF pagination against the production function body,
not authenticated downloads and not a teacher-facing release.
"""
import ast
from pathlib import Path
import re
import subprocess

from docx import Document
from docx.shared import Pt
from pypdf import PdfReader

from web.sains_unit_awal import LESSONS as OTHER_LESSONS, STANDARDS
from web.sains_y3_unit_awal import LESSONS as YEAR3_LESSONS, SP as YEAR3_SP, plan_rows

ROOT = Path(__file__).resolve().parents[1]
TARGET_YEARS = (2, 3, 4, 5, 6)


def _real_word_function():
    """Compile exactly the last app.py Word builder; do not modify its source."""
    text = (ROOT / "app.py").read_text(encoding="utf-8")
    needle = "\ndef _create_rph_word("
    if needle not in text:
        raise AssertionError("Live Word function not available in app.py")
    start = text.rindex(needle) + 1
    body_start = text.index("\n", start) + 1
    following = re.search(r"(?m)^(?:async )?def ", text[body_start:])
    end = body_start + following.start() if following else len(text)
    source = text[start:end]
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.FunctionDef) and node.name == "_create_rph_word"
    from qa import english_word_builder_snapshot as isolated
    ns = {key: value for key, value in vars(isolated).items() if not key.startswith("__")}
    # Isolate only the ancillary dependencies; do NOT replace the native builder.
    ns["_rph_title"] = lambda state: "RANCANGAN PENGAJARAN HARIAN"
    ns["_PI_RPH_FILL"] = "F5F1DF"
    ns["_SAINS_RPH_FILL"] = "EAF5EE"
    ns["_rph_blank_or_value"] = lambda value, *a, **k: str(value or "").strip()
    ns["_rph_attendance_value"] = lambda value: str(value or "").strip()
    exec(compile(ast.Module(body=[node], type_ignores=[]), "app.py", "exec"), ns)
    return ns["_create_rph_word"]


def _real_lesson(year):
    source = YEAR3_LESSONS if year == 3 else OTHER_LESSONS
    return next(p for p in source if p.year == year)


def test_real_word_function_offline_a4(tmp_path):
    writer = _real_word_function()
    dest = tmp_path / "word"
    dest.mkdir()
    files = []
    for year in TARGET_YEARS:
        lesson = _real_lesson(year)
        standards = YEAR3_SP if year == 3 else STANDARDS[year]
        rows = plan_rows({
            "MATA PELAJARAN": "Sains",
            "TAHUN/TINGKATAN": f"Tahun {year}",
            "TAJUK": lesson.title,
            "TARIKH": "", "HARI": "", "MASA": "", "KELAS": "",
            "BILANGAN MURID": "",
            "PENGETAHUAN SEDIA ADA": "Murid menggunakan pemerhatian awal.",
            "REFLEKSI": "",
        }, lesson, standards)
        document = Document()
        document.styles["Normal"].font.name = "Arial"
        document.styles["Normal"].font.size = Pt(10)
        outfile = dest / f"Sains_T{year}_{lesson.code}.docx"
        state = {"task": "rph", "subject": "Sains", "year": f"Tahun {year}",
                 "pdp_sequence_code": lesson.code, "topic": lesson.title}
        writer(document, document.sections[0], state, rows, str(outfile))
        assert outfile.exists() and outfile.stat().st_size > 1000
        parsed = Document(str(outfile))
        assert len(parsed.tables) == 3, (year, len(parsed.tables))
        # Permanent owner rule: preserve the existing Sains renderer while
        # proving that all three OUTER table edges align on the same A4 grid.
        # Do not force Sains through the generic LTR adapter or alter SK/SP.
        widths = [sum(col.width.mm for col in table.columns)
                  for table in parsed.tables]
        assert all(140 < width < 190 for width in widths), (year, widths)
        assert max(widths) - min(widths) < .8, (year, widths)
        content = "\n".join(c.text for t in parsed.tables for row in t.rows for c in row.cells)
        assert rows["EMK / NILAI"] in content
        assert rows["KBAT / PAK21"] in content
        assert lesson.assessment in content
        assert lesson.follow_up in content
        assert all(f"{sp} {standards[sp]}" in content for sp in lesson.standards)
        assert not any("____" in parsed.tables[0].cell(i, 1).text for i in (2, 3, 4, 5, 6))
        files.append(outfile)

    pdfdir = tmp_path / "pdf"
    pdfdir.mkdir()
    process = subprocess.run(
        ["libreoffice", "-env:UserInstallation=file://" + str(tmp_path / "lo-profile"),
         "--headless", "--convert-to", "pdf", "--outdir", str(pdfdir),
         *map(str, files)],
        capture_output=True, text=True, timeout=150,
    )
    assert process.returncode == 0, process.stderr[-500:]
    for file in files:
        pdf = pdfdir / (file.stem + ".pdf")
        assert pdf.is_file(), file.name
        pages = PdfReader(str(pdf)).pages
        assert len(pages) == 1, (file.name, len(pages))
        assert abs(float(pages[0].mediabox.width) - 595.28) < 2
        assert abs(float(pages[0].mediabox.height) - 841.89) < 2
        body = pages[0].extract_text()
        # Actual PDF generated from the SAME Word file must retain
        # curriculum identity and source-backed SP without clipping.
        assert "Sains" in body and "Standard Pembelajaran" in body
        assert "KBAT" in body and "EMK" in body
        assert "Pemulihan" in body


def test_all_32_source_backed_opening_lessons_have_aligned_word_and_a4_pdf(tmp_path):
    """Audit EVERY source-backed Sains opening lesson (32), not just 5 samples.

    This is an offline test of the original native writer using real PdP
    source records. No app server, teacher login, database write or quota.
    The remaining whole-year Sains catalogue is explicitly out of scope.
    """
    import fitz

    lessons = {
        year: tuple(
            p for p in (YEAR3_LESSONS if year == 3 else OTHER_LESSONS)
            if p.year == year
        )
        for year in TARGET_YEARS
    }
    expected_counts = {2: 7, 3: 9, 4: 6, 5: 5, 6: 5}
    assert {year: len(rows) for year, rows in lessons.items()} == expected_counts
    assert sum(expected_counts.values()) == 32

    writer = _real_word_function()
    worddir = tmp_path / "sains-source-backed-word"
    pdfdir = tmp_path / "sains-source-backed-pdf"
    worddir.mkdir()
    pdfdir.mkdir()
    produced = []
    for year, candidates in lessons.items():
        standards = YEAR3_SP if year == 3 else STANDARDS[year]
        for lesson in candidates:
            rows = plan_rows({
                "MATA PELAJARAN": "Sains",
                "TAHUN/TINGKATAN": f"Tahun {year}",
                "TAJUK": lesson.title,
                "TARIKH": "", "HARI": "", "MASA": "", "KELAS": "",
                "BILANGAN MURID": "",
                "PENGETAHUAN SEDIA ADA": "Murid menggunakan pemerhatian awal.",
                "REFLEKSI": "",
            }, lesson, standards)
            word = worddir / f"Sains_T{year}_{lesson.code}.docx"
            state = {
                "task": "rph", "subject": "Sains",
                "year": f"Tahun {year}", "pdp_sequence_code": lesson.code,
                "topic": lesson.title,
            }
            document = Document()
            document.styles["Normal"].font.name = "Arial"
            document.styles["Normal"].font.size = Pt(10)
            writer(document, document.sections[0], state, rows, str(word))
            assert word.is_file() and word.stat().st_size > 1000, lesson.code

            parsed = Document(str(word))
            assert len(parsed.tables) == 3, lesson.code
            widths = [sum(col.width.mm for col in t.columns)
                      for t in parsed.tables]
            assert all(140 < w < 190 for w in widths), (lesson.code, widths)
            assert max(widths) - min(widths) < 0.8, (lesson.code, widths)
            contents = "\n".join(
                cell.text for table in parsed.tables
                for row in table.rows for cell in row.cells
            )
            for exact in (
                rows["STANDARD KANDUNGAN"], rows["STANDARD PEMBELAJARAN"],
                rows["EMK / NILAI"], rows["KBAT / PAK21"],
                lesson.guided, lesson.independent, lesson.assessment,
                lesson.follow_up,
            ):
                assert exact in contents, (lesson.code, exact[:80])
            assert not any("____" in cell.text for row in parsed.tables[0].rows for cell in row.cells), lesson.code
            produced.append((word, lesson.code, lesson.standards))

    conversion = subprocess.run([
        "libreoffice",
        "-env:UserInstallation=" + (tmp_path / "lo-all-32").as_uri(),
        "--headless", "--convert-to", "pdf",
        "--outdir", str(pdfdir),
        *(str(item[0]) for item in produced),
    ], capture_output=True, text=True, timeout=240)
    assert conversion.returncode == 0, conversion.stderr[-1200:]

    for word, code, standards in produced:
        pdf_path = pdfdir / (word.stem + ".pdf")
        assert pdf_path.is_file(), (code, conversion.stdout[-1200:])
        with fitz.open(str(pdf_path)) as pdf:
            assert 1 <= len(pdf) <= 2, (code, len(pdf))
            document_text = " ".join(p.get_text() for p in pdf)
            for required in ("Sains", "Standard Pembelajaran", "EMK", "KBAT",
                             "Pemulihan", *standards):
                assert required in document_text, (code, required)
            for page in pdf:
                assert abs(page.rect.width - 595.28) < 2, code
                assert abs(page.rect.height - 841.89) < 2, code
                for block in page.get_text("dict")["blocks"]:
                    if block.get("type") != 0:
                        continue
                    x0, y0, x1, y1 = block["bbox"]
                    assert -1 <= x0 < x1 <= page.rect.width + 1, (code, block["bbox"])
                    assert -1 <= y0 < y1 <= page.rect.height + 1, (code, block["bbox"])
    print("SAINS_SOURCE_BACKED_32_WORD_PDF_A4_PASS", len(produced))
