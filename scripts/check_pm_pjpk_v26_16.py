#!/usr/bin/env python3
"""Read-only PM/PJPK release gate. Does not modify the app or database.
Run after reconstructing the versioned v26.16 database:
    python scripts/check_pm_pjpk_v26_16.py
"""
from pathlib import Path
import sqlite3
import sys

DB = Path(__file__).resolve().parents[1] / "CikguLaju_Curriculum_Master_v26_16_PJPK_SAFE_RELEASE.db"
SUBJECTS = ("Pendidikan Moral", "Pendidikan Jasmani", "Pendidikan Kesihatan")

def main():
    if not DB.is_file():
        raise SystemExit(f"Missing reconstructed database: {DB}")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        if con.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise SystemExit("FAIL: SQLite integrity check")
        views = {x[0] for x in con.execute("SELECT name FROM sqlite_master WHERE type='view'")}
        if "pjpk_ready_pdp" not in views:
            raise SystemExit("FAIL: safe PJPK ready view missing")
        for subject in SUBJECTS:
            total, flagged = con.execute(
                "SELECT COUNT(*), COALESCE(SUM(verified),0) FROM rpt_entries WHERE subject=?",
                (subject,)
            ).fetchone()
            print(f"{subject}: total={total}, verified_flag={flagged}")
        columns = [x[1] for x in con.execute("PRAGMA table_info(pjpk_ready_pdp)")]
        ready = con.execute("SELECT COUNT(*) FROM pjpk_ready_pdp").fetchone()[0]
        print(f"PJPK safe-release rows: {ready}; columns={columns}")
        if ready != 33:
            raise SystemExit(f"FAIL: expected 33 ready PJPK rows, got {ready}")
        unsafe = con.execute("""
            SELECT COUNT(*) FROM pjpk_ready_pdp
            WHERE COALESCE(content_verified,0)!=1
               OR COALESCE(sequence_verified,0)!=1
               OR COALESCE(schedule_verified,0)!=1
        """).fetchone()[0]
        if unsafe:
            raise SystemExit(f"FAIL: {unsafe} unsafe rows in ready view")
        print("PASS: release view checked; do not route unfinished PJPK entries into RPH.")
        print("NOTE: This check does not activate PJPK in the running app.")
    finally:
        con.close()

if __name__ == "__main__":
    main()
