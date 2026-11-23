"""Read-only diagnostic: compare full active PI source with native render stages."""
import sqlite3
from tools.bm_native_v26_navigation_audit import database

def main():
    from tools import run_telegram_with_curriculum_api as live
    from web.telegram_verified_rpt_rph_bridge import _native_state, _native_text
    from web.pi_navigation import pi_navigation_unit
    runtime = live.telegram_runtime
    tmp, db_path = database()
    try:
        runtime.DB_PATH = str(db_path)
        runtime.CIKGULAJU_DB_V2600_ACTIVE = True
        with sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            source = dict(db.execute("SELECT * FROM rpt_entries WHERE id=1275 AND subject='Pendidikan Islam' AND verified=1").fetchone())
        sel = {"year":2, "subject":"PI", "unit":pi_navigation_unit(source), "lesson":1275}
        state = _native_state(runtime, sel, {
            "class":"","date":"","time":"","students":"","reflection":""
        })
        native = _native_text(runtime, state)
        rows = runtime._rph_rows(state, native)
        if callable(getattr(runtime, "_rph_document_rows", None)):
            final_rows = runtime._rph_document_rows(state, rows)
        else:
            final_rows = rows
        for label, value in (
            ("SOURCE", source["activity_note"]),
            ("STATE", state["rpt_activity_note"]),
            ("NATIVE_TEXT_ACTIVITY_SECTION", native[native.find("اکتيۏيتي"):native.find("اکتيۏيتي")+750]),
            ("ROWS_MAIN", rows.get("AKTIVITI UTAMA", "")),
            ("DOCUMENT_ROWS_MAIN", final_rows.get("AKTIVITI UTAMA", "")),
            ("DISPLAY_FORMATTED", runtime._rph_format_activity_lines(final_rows.get("AKTIVITI UTAMA", ""))),
        ):
            print("PI_RENDER_STAGE", label, "LENGTH", len(value), "TEXT", repr(value[:850]))
        assert len(str(source["activity_note"])) >= 110
        # Grounded acceptance: exact complete RPT rows, not just removal of '2.'.
        fragments = (
            "1. ممباچ اية سچارا تلقي دان مشافهة",
            "2. ممبتولكن باچاءن يڠ كورڠ فصيح",
            "3. ممبيمبيڠ راكن سباي",
            "4. ݢورو مريكوت ڤنچاڤاين موريد.",
        )
        for field in ("ROWS_MAIN", "DOCUMENT_ROWS_MAIN"):
            value = rows["AKTIVITI UTAMA"] if field == "ROWS_MAIN" else final_rows["AKTIVITI UTAMA"]
            for item in fragments:
                assert item in value, (field, "missing original source step", item)
            assert "مشافهة 2." not in value, (field, "old truncated display survived")
        # Export through the SAME two Telegram functions Web invokes. Never
        # upload to materials, change credits or alter the verified DB.
        import uuid, shutil
        from pathlib import Path
        from docx import Document
        import fitz
        output_dir = Path("qa/pi-source-steps-fixed")
        output_dir.mkdir(parents=True, exist_ok=True)
        unique = "audit_pi_" + uuid.uuid4().hex[:16]
        word_file = Path(runtime.create_word_file(state, native, unique))
        pdf_file = Path(runtime.create_pdf_file(state, native, unique+"p"))
        assert word_file.is_file() and pdf_file.is_file()
        word_doc = Document(str(word_file))
        assert len(word_doc.tables) == 4
        for table in word_doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        assert abs(paragraph.paragraph_format.line_spacing - 1.5) < 0.0001, ("Active PI Word missing 1.5x spacing", paragraph.text[:70])
        print("PI_ACTIVE_SOURCE_WORD_SPACING_1_5_VALIDATED")
        whole_word = "\\n".join(cell.text for table in word_doc.tables
                               for row in table.rows for cell in row.cells)
        for item in fragments:
            assert item in whole_word, ("Word output lost source step", item)
        assert "مشافهة 2." not in whole_word, "Word output retains source truncation"
        with fitz.open(str(pdf_file)) as generated_pdf:
            assert len(generated_pdf) == 1, "Native PI PDF exceeded one A4 page"
            assert abs(generated_pdf[0].rect.width - 595.3) < 2
            assert abs(generated_pdf[0].rect.height - 841.9) < 2
        shutil.copy2(word_file, output_dir / "CIKGULAJU_PI_T2_PDP001_4_LANGKAH_SUMBER_AKTIF.docx")
        shutil.copy2(pdf_file, output_dir / "CIKGULAJU_PI_T2_PDP001_4_LANGKAH_SUMBER_AKTIF_NATIVE.pdf")
        print("PI_ACTUAL_NATIVE_WORD_PDF_4_SOURCE_STEPS_SUCCESS")
        word_file.unlink(missing_ok=True)
        pdf_file.unlink(missing_ok=True)
    finally:
        tmp.cleanup()

if __name__ == "__main__":
    main()
