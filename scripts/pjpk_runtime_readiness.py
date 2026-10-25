#!/usr/bin/env python3
"""Read-only PJPK runtime readiness counts; never changes a curriculum database."""
import sqlite3
from pathlib import Path
from scripts.pjpk_v26_16_adapter import DB_NAME, ready_pdp

def report(db_path=None):
    path = Path(db_path) if db_path else Path(__file__).resolve().parents[1] / DB_NAME
    if not path.is_file():
        raise FileNotFoundError(path)
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as con:
        con.row_factory = sqlite3.Row
        columns = {r[1] for r in con.execute("PRAGMA table_info(rpt_entry_standards)")}
        required = {"rpt_entry_id", "standard_type", "standard_code", "standard_text", "verified"}
        if not required.issubset(columns):
            raise RuntimeError("Missing verified standard columns")
        output = []
        for year in range(1, 7):
            for subject in ("Pendidikan Jasmani", "Pendidikan Kesihatan"):
                rows = ready_pdp(f"Tahun {year}", subject, db_path=path)
                eligible = 0
                blocked = []
                for row in rows:
                    found = {r["standard_type"] for r in con.execute(
                        """SELECT standard_type FROM rpt_entry_standards
                           WHERE rpt_entry_id=? AND verified=1
                           AND TRIM(COALESCE(standard_code,''))!=''
                           AND TRIM(COALESCE(standard_text,''))!=''
                           AND standard_type IN ('SK','SP')""", (row["id"],)
                    )}
                    eligible += int({"SK", "SP"}.issubset(found))
                    if not {"SK", "SP"}.issubset(found):
                        blocked.append((row["id"], ",".join(sorted({"SK", "SP"} - found))))
                output.append((f"Tahun {year}", subject, len(rows), eligible))
                for entry_id, missing in blocked:
                    print(f"BLOCKED_ENTRY year={year} subject={subject} rpt_entry_id={entry_id} missing={missing}")
        return output

if __name__ == "__main__":
    print("year,subject,safe_rows,verified_sk_sp_rows")
    for row in report():
        print(",".join(map(str, row)))
