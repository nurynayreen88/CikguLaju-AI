"""Read-only lookup of existing English standalone RPH for an exact verified RPT row."""
import sqlite3
from pathlib import Path
from english_standalone_adapter import load_english_rph


def verified_english_rph_metadata(db_path, year, rpt_row_id):
    if type(year) is not int or year not in (1, 2, 3):
        raise ValueError("invalid year")
    if type(rpt_row_id) is not int or rpt_row_id < 1:
        raise ValueError("invalid RPT row")
    path = Path(db_path)
    if not path.is_file():
        raise FileNotFoundError("active curriculum database unavailable")
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=2) as con:
        con.execute("PRAGMA query_only=ON")
        rows = con.execute(
            "SELECT sequence_no FROM rpt_entries WHERE id=? AND year_label=? "
            "AND subject=? AND verified=1 "
            "AND lower(COALESCE(notes,'')) NOT LIKE '%superseded%' LIMIT 2",
            (rpt_row_id, f"Tahun {year}", "Bahasa Inggeris"),
        ).fetchall()
    if len(rows) != 1:
        return []
    sequence = rows[0][0]
    if type(sequence) is not int or not 1 <= sequence <= 160:
        return []
    if load_english_rph(year, sequence) is None:
        return []
    return [{
        "id": f"english-rph-{year}-{rpt_row_id}",
        "title": f"RPH English Tahun {year} Lesson {sequence}",
        "type": "rph",
        "approved": True,
        "download_enabled": False,
    }]
