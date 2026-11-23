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
    finally:
        tmp.cleanup()

if __name__ == "__main__":
    main()
