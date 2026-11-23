"""Read-only one-RPH smoke from the SAME active v26 Telegram master source.

Never uses the deprecated 696 archive, invents any RPH prose or edits
production DB/storage. Exports one actual native Word and native PDF through
the installed Telegram runtime, as a private GitHub CI QA artifact.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import json
import os
import shutil
import sqlite3
import uuid

from tools.bm_native_v26_navigation_audit import database


def main():
    from tools import run_telegram_with_curriculum_api as running
    from web.pi_navigation import pi_navigation_unit
    from web.telegram_verified_rpt_rph_bridge import _native_state, _native_text

    runtime = running.telegram_runtime
    tmp, master = database()
    try:
        runtime.DB_PATH = str(master)
        runtime.CIKGULAJU_DB_V2600_ACTIVE = True
        with sqlite3.connect(master.resolve().as_uri() + "?mode=ro", uri=True) as con:
            con.row_factory = sqlite3.Row
            assert con.execute("PRAGMA quick_check").fetchone()[0] == "ok"
            pi_count = con.execute(
                "SELECT COUNT(*) FROM rpt_entries WHERE subject=? AND verified=1",
                ("Pendidikan Islam",)
            ).fetchone()[0]
            assert pi_count >= 800, pi_count
            choices = [dict(row) for row in con.execute(
                """SELECT * FROM rpt_entries
                   WHERE subject='Pendidikan Islam'
                     AND year_label='Tahun 2' AND verified=1
                     AND lower(COALESCE(notes,'')) NOT LIKE '%superseded%'
                     AND length(COALESCE(activity_note,'')) > 75
                   ORDER BY sequence_no ASC, id ASC LIMIT 28"""
            )]
        assert choices, "No real source lessons available"

        output_dir = Path("qa/pi-active-real")
        output_dir.mkdir(parents=True, exist_ok=True)
        selected = None
        outcomes = []
        for row in choices:
            label = pi_navigation_unit(row)
            if not label:
                continue
            selection = {"year": 2, "subject": "PI",
                         "unit": label, "lesson": int(row["id"])}
            teacher = {"class": "", "date": "", "time": "",
                       "students": "", "reflection": ""}
            try:
                state = _native_state(runtime, selection, teacher)
                lesson_text = _native_text(runtime, state)
                assert len(lesson_text.strip()) >= 500
                unique = "pi_true_" + uuid.uuid4().hex[:14]
                word = Path(runtime.create_word_file(state, lesson_text, unique))
                pdf = Path(runtime.create_pdf_file(state, lesson_text, unique+"p"))
                assert word.exists() and pdf.exists()
                original_word = word.read_bytes()
                original_pdf = pdf.read_bytes()
                assert len(original_word) > 1000 and len(original_pdf) > 1000
                assert original_word.startswith(b"PK\x03\x04")
                assert original_pdf.startswith(b"%PDF-")
                with ZipFile(word) as z:
                    assert z.testzip() is None
                    assert "word/document.xml" in z.namelist()
                import fitz
                with fitz.open(stream=original_pdf, filetype="pdf") as document:
                    assert 1 <= len(document) <= 4
                    assert all(abs(page.rect.width-595.3) < 3 and
                               abs(page.rect.height-841.9) < 3
                               for page in document)
                    pages = len(document)
                word_dest = output_dir / "CIKGULAJU_PI_AKTIF_T2_RPH_CONTOH_SEBENAR.docx"
                pdf_dest = output_dir / "CIKGULAJU_PI_AKTIF_T2_RPH_CONTOH_PDF_ASAL.pdf"
                shutil.copy2(word, word_dest)
                shutil.copy2(pdf, pdf_dest)
                selected = {
                    "source": "v26.00 verified master RPT (ACTIVE Telegram native)",
                    "not_used": "PI 696 archive",
                    "year": 2,
                    "pdp_no": row.get("sequence_no"),
                    "rpt_entry_id": row["id"],
                    "unit": label,
                    "activity_note_chars": len(row.get("activity_note") or ""),
                    "native_lesson_text_chars": len(lesson_text),
                    "generated_from": "runtime.create_word_file and runtime.create_pdf_file",
                    "word_sha256": sha256(original_word).hexdigest(),
                    "pdf_sha256": sha256(original_pdf).hexdigest(),
                    "pdf_pages": pages,
                    "note": "Native PDF remains on its existing separate renderer. Only the Word Jawi presentation has received latest RTL styling."
                }
                break
            except Exception as exc:
                # Safe sampling: no lesson-specific/private data in CI logs.
                outcomes.append(type(exc).__name__)
        if selected is None:
            raise RuntimeError("Active PI native export failed; errors=" + str(outcomes[:15]))
        (output_dir / "SOURCE_PROVENANCE.json").write_text(
            json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")
        print("Source check: 800+ PI verified rows", pi_count)
        print("Export active sample SUCCESS:", "Tahun 2", "RPT ID", selected["rpt_entry_id"],
              "Word+PDF", selected["pdf_pages"], "PDF pages")
    finally:
        tmp.cleanup()


if __name__ == "__main__":
    main()
