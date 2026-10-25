"""Opt-in, read-only PJPK source adapter for CikguLaju v26.16.

This module intentionally does not switch DB_PATH or patch app.py.
Only rows from pjpk_ready_pdp may be exposed. Unverified rows remain hidden.
"""
from pathlib import Path
import sqlite3

DB_NAME = "CikguLaju_Curriculum_Master_v26_16_PJPK_SAFE_RELEASE.db"
SUBJECTS = frozenset(("Pendidikan Jasmani", "Pendidikan Kesihatan"))

def ready_pdp(year_label, subject, db_path=None):
    if subject not in SUBJECTS or year_label not in {f"Tahun {i}" for i in range(1, 7)}:
        return []
    path = Path(db_path) if db_path else Path(__file__).resolve().parents[1] / DB_NAME
    if not path.is_file():
        return []
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as con:
            con.row_factory = sqlite3.Row
            cols = {r[1] for r in con.execute("PRAGMA table_info(pjpk_ready_pdp)")}
            if not {"id", "year_label", "subject", "sequence_no", "content_verified", "sequence_verified", "schedule_verified"}.issubset(cols):
                return []
            rows = con.execute("""
                SELECT * FROM pjpk_ready_pdp
                WHERE year_label=? AND subject=?
                  AND content_verified=1 AND sequence_verified=1 AND schedule_verified=1
                ORDER BY sequence_no, id
            """, (year_label, subject)).fetchall()
            return [dict(r) for r in rows]
    except (sqlite3.Error, OSError):
        return []
