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
from web.telegram_native_bm_sequence_rph_bridge import _state as _bm_state, _content as _bm_content
from web_v1_dropdown_catalog import _bm_verified_structured_rows, bm_sequence_token


def _all_word_text(path):
    from docx import Document
    doc = Document(path)
    assert len(doc.tables) == 4
    return doc, "\n".join(cell.text for table in doc.tables
                          for row in table.rows for cell in row.cells)


def check_one(runtime, path, row, code, output_dir):
    import fitz
    subject = "Pendidikan Islam" if code == "PI" else "Bahasa Melayu"
    source_label = row.get("id") or row.get("source_sequence_no") or row.get("topic")
    teacher = {"class": "", "date": "", "time": "", "students": "", "reflection": ""}
    if code == "PI":
        selection = {"year": 2, "subject": code, "unit": pi_navigation_unit(row),
                     "lesson": int(row["id"])}
        state = _native_state(runtime, selection, teacher)
        native = _native_text(runtime, state)
    else:
        # BM is NOT an RPT-entry-ID route: use the exact live verified PdP
        # sequence token and grouped SK/SP mapping (Web and Telegram agree).
        token = bm_sequence_token(2, row["theme"], row["unit_code"],
                                  row["unit_title"], row["topic"])
        state = _bm_state(runtime, 2, row["unit_title"], token, teacher)
        native = _bm_content(runtime, state)
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
            source_label, objective, criterion, reflection
        )
        assert "____ / ____" in reflection
        # A stock BM criterion such as "membaca bahan sasaran mengikut
        # fokus kemahiran" is still generic. The verified actual SP and
        # specific topic must appear in the reflection instead.
        assert "bahan sasaran" not in reflection.casefold(), reflection
        assert "fokus kemahiran" not in reflection.casefold(), reflection
        if str(row.get("topic") or "").strip() and len(str(row["topic"])) <= 55:
            assert str(row["topic"]).casefold() in reflection.casefold(), (row["topic"], reflection)

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
            # QA-only production-source check: every source-authored Aktiviti
            # heading is bold and occupies its own line, never the end of a
            # numbered teacher instruction. Do not touch Word or source text.
            lines = [
                line for block in page.get_text("dict")["blocks"]
                for line in block.get("lines", [])
            ]
            for n in (1, 2, 3):
                matches = [
                    line for line in lines
                    if any("Aktiviti " + str(n) in span["text"]
                           for span in line["spans"])
                ]
                assert len(matches) == 1, ("heading count", n, matches)
                line_text = "".join(span["text"] for span in matches[0]["spans"])
                assert line_text.strip().startswith("Aktiviti " + str(n)), (
                    "title shares teacher-instruction line", n, line_text
                )
                assert any("Bold" in span["font"] and "Aktiviti " in span["text"]
                           for span in matches[0]["spans"]), (
                    "source activity heading not bold", n, line_text
                )
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
                    subject, source_label, "Word crossed one-page A4 limit")
                assert 594 < converted_pdf[0].rect.width < 597
                assert 840 < converted_pdf[0].rect.height < 844
    shutil.copy2(word, output_dir / ("CIKGULAJU_" + code + "_REFLEKSI_OBJ_AKTIF.docx"))
    shutil.copy2(pdf, output_dir / ("CIKGULAJU_" + code + "_REFLEKSI_OBJ_PDF_NATIVE.pdf"))
    print("REAL REFLECTION PASS", subject, source_label, "objective_length",
          len(objective), "criterion_length", len(criterion),
          "reflection_length", len(reflection), "A4_WORD_PDF_ONE_PAGE")
    word.unlink(missing_ok=True)
    pdf.unlink(missing_ok=True)
    return source_label


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
                "BM": [],
            }
        bm_rows = _bm_verified_structured_rows(db_path, 2)
        grouped = {}
        for item in bm_rows:
            key = (item["theme"], item["unit_code"], item["unit_title"], item["topic"])
            grouped.setdefault(key, item)
        candidates["BM"] = list(grouped.values())[:25]
        print("REAL_BM_VERIFIED_PDP_SEQUENCE_CHOICES", len(grouped), flush=True)
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
                    errors.append((row.get("id") or row.get("source_sequence_no") or row.get("topic"), type(exc).__name__, str(exc)[:150]))
            if not checked:
                raise AssertionError(("No verified " + code + " candidate fits one-page RPH", errors[:8]))
    finally:
        tmp.cleanup()


if __name__ == "__main__":
    main()
