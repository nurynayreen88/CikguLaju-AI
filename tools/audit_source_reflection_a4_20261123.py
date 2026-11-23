"""Read-only end-to-end checks of auto reflection on two real verified v26 lessons.

Only selects source-backed PI/BM from active Telegram master. Never uses 696,
changes database/user quotas, or sends an API request. All generated Word/PDF
are temporary and must fit one A4 page for the samples under review.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import subprocess
import shutil
import uuid

from tools.bm_native_v26_navigation_audit import database
from web.pi_navigation import pi_navigation_unit
from web.telegram_verified_rpt_rph_bridge import _native_state, _native_text


def _all_word_text(path):
    from docx import Document
    doc = Document(path)
    assert len(doc.tables) == 4
    return doc, "\n".join(cell.text for table in doc.tables
                          for row in table.rows for cell in row.cells)


def check_one(runtime, path, row, code, output_dir):
    import fitz
    subject = "Pendidikan Islam" if code == "PI" else "Bahasa Melayu"
    unit = pi_navigation_unit(row) if code == "PI" else str(row.get("unit_title") or "").strip()
    selection = {"year": 2, "subject": code, "unit": unit, "lesson": int(row["id"])}
    state = _native_state(runtime, selection, {
        "class": "", "date": "", "time": "", "students": "", "reflection": ""
    })
    native = _native_text(runtime, state)
    rows = runtime._rph_rows(state, native)
    criterion = rows.get("KRITERIA KEJAYAAN", "")
    objective = rows.get("OBJEKTIF PEMBELAJARAN", "")
    reflection = rows.get("REFLEKSI", "")
    assert isinstance(reflection, str) and reflection.strip()
    assert rows.get("AKTIVITI UTAMA")
    if code == "PI":
        assert "سورة" in str(row.get("objective_jawi") or "") or "القر" in str(row.get("topic") or ""), (row["id"], row.get("objective_jawi"))
        assert "موريد منچاپاي ساسرن" in reflection, (row["id"], reflection)
        assert "____ / ____" in reflection
        assert "فوکوس ڤدڤ" not in reflection
    else:
        assert reflection.startswith("____ / ____ murid: "), (
            row["id"], objective, criterion, reflection
        )
        assert "____ / ____" in reflection

    unique = "objqa" + uuid.uuid4().hex[:14]
    word = Path(runtime.create_word_file(state, native, unique))
    pdf = Path(runtime.create_pdf_file(state, native, unique + "p"))
    assert word.is_file() and pdf.is_file()
    doc, text = _all_word_text(word)
    assert reflection in text, "Word did not print criterion-driven reflection"
    with fitz.open(str(pdf)) as book:
        assert len(book) == 1, "Native PDF exceeded one A4 page"
        page = book[0]
        assert 594 < page.rect.width < 597 and 840 < page.rect.height < 844
        if code == "BM":
            # Latin text extraction is well supported for these audit samples.
            assert "murid:" in page.get_text().casefold()
    if code == "PI":
        assert "سورة" in text
        assert "موري" in text
        assert "2. ممبتولكن باچاءن" in text
        assert "3. ممبيمبيڠ راكن سباي" in text
        assert "4. ݢورو مريكوت ڤنچاڤاين" in text
    # Rendering an authentic active source to PDF from the *Word* validates
    # 1.5 paragraph spacing and real page boundaries (not theoretical height).
    if shutil.which("libreoffice"):
        with TemporaryDirectory() as temp:
            profile = Path(temp) / "profile"
            result = subprocess.run([
                "libreoffice", "-env:UserInstallation=" + profile.as_uri(),
                "--headless", "--convert-to", "pdf", "--outdir", temp, str(word)
            ], capture_output=True, text=True, timeout=100)
            assert result.returncode == 0, (result.stderr, result.stdout)
            converted = Path(temp) / (word.stem + ".pdf")
            with fitz.open(str(converted)) as converted_pdf:
                assert len(converted_pdf) == 1, (
                    subject, row["id"], "1.5x Word crossed one-page A4 limit")
                assert 594 < converted_pdf[0].rect.width < 597
                assert 840 < converted_pdf[0].rect.height < 844
    shutil.copy2(word, output_dir / ("CIKGULAJU_" + code + "_REFLEKSI_OBJ_AKTIF.docx"))
    shutil.copy2(pdf, output_dir / ("CIKGULAJU_" + code + "_REFLEKSI_OBJ_PDF_NATIVE.pdf"))
    print("REAL REFLECTION PASS", subject, row["id"], "objective_length",
          len(objective), "criterion_length", len(criterion),
          "reflection_length", len(reflection), "A4_WORD_PDF_ONE_PAGE")
    word.unlink(missing_ok=True)
    pdf.unlink(missing_ok=True)
    return row["id"]


def main():
    from tools import run_telegram_with_curriculum_api as live
    runtime = live.telegram_runtime
    tmp, db_path = database()
    try:
        runtime.DB_PATH = str(db_path)
        runtime.CIKGULAJU_DB_V2600_ACTIVE = True
        with sqlite3.connect(db_path.resolve().as_uri()+"?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            candidates = {
                "PI": [dict(r) for r in db.execute(
                    "SELECT * FROM rpt_entries WHERE id=1275 AND subject='Pendidikan Islam' AND verified=1")],
                "BM": [dict(r) for r in db.execute(
                    """SELECT * FROM rpt_entries
                       WHERE subject='Bahasa Melayu' AND year_label='Tahun 2' AND verified=1
                       AND length(COALESCE(activity_note,''))>55
                       AND length(COALESCE(unit_title,''))>3
                       AND lower(COALESCE(notes,'')) NOT LIKE '%superseded%'
                       ORDER BY id LIMIT 16"""
                )]
            }
        output_dir = Path("qa/rph-source-reflections")
        output_dir.mkdir(parents=True, exist_ok=True)
        for code, records in candidates.items():
            errors = []
            checked = False
            for row in records:
                try:
                    check_one(runtime, db_path, row, code, output_dir)
                    checked = True
                    break
                except Exception as exc:
                    errors.append((row["id"], type(exc).__name__, str(exc)[:150]))
            if not checked:
                raise AssertionError(("No verified " + code + " candidate fits one-page RPH", errors[:8]))
    finally:
        tmp.cleanup()


if __name__ == "__main__":
    main()
