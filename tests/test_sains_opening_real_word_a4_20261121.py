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
TARGET_YEARS = (2, 3, 4)


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
        assert "KBAT" in body and "EMK" in body
        assert "Pemulihan" in body
