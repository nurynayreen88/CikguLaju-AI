#!/usr/bin/env python3
"""Non-destructive SK/SP gap audit for PJPK v26.16.

Writes a CSV report only; never updates the curriculum database.
"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "CikguLaju_Curriculum_Master_v26_16_PJPK_SAFE_RELEASE.db"
REPORT = ROOT / "PJPK_T1_SK_mapping_gaps_v26_16.csv"

def main():
    if not DB.is_file():
        raise SystemExit(f"Missing source DB: {DB}")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute("""
            SELECT r.id, r.year_label, r.sequence_no, r.unit_title, r.topic,
                   GROUP_CONCAT(CASE WHEN s.standard_type='SP' THEN s.standard_code END, ', ') AS sp_codes,
                   SUM(CASE WHEN s.standard_type='SK' AND s.verified=1 THEN 1 ELSE 0 END) AS verified_sk
            FROM pjpk_ready_pdp r
            LEFT JOIN rpt_entry_standards s ON s.rpt_entry_id=r.id
            WHERE r.year_label='Tahun 1' AND r.subject='Pendidikan Jasmani'
            GROUP BY r.id
            ORDER BY r.sequence_no
        """).fetchall()
    finally:
        con.close()
    with REPORT.open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(("rpt_entry_id", "tahun", "pdp", "unit", "tajuk",
                         "SP_sedia_ada", "SK_disahkan", "status"))
        for row in rows:
            writer.writerow((row["id"], row["year_label"], row["sequence_no"],
                             row["unit_title"], row["topic"], row["sp_codes"] or "",
                             "", "PERLU SEMAK DSKP" if not row["verified_sk"] else "SK TERSEDIA"))
    print(f"Audited {len(rows)} PdP; report={REPORT}; source DB unchanged")

if __name__ == "__main__":
    main()
