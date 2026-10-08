"""Read-only PJPK curriculum coverage audit v26.70.

Usage: python scripts/audit_pjpk_coverage_v2670.py /path/to/CikguLaju.db
Reports verified PJ/PK rows with unique SK and SP; never writes to the DB.
"""
import json
import sqlite3
import sys

SUBJECTS = ("Pendidikan Jasmani", "Pendidikan Kesihatan")
YEARS = tuple(f"Tahun {i}" for i in range(1, 7))

def audit(db_path):
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"rpt_entries", "rpt_entry_standards"}.issubset(tables):
            return {"error": "Required RPT tables missing", "tables_found": sorted(tables)}
        entry_columns = {r[1] for r in connection.execute("PRAGMA table_info(rpt_entries)")}
        standard_columns = {r[1] for r in connection.execute("PRAGMA table_info(rpt_entry_standards)")}
        required_entries = {"id","year_label","subject","verified","content_verified"}
        required_standards = {"rpt_entry_id","standard_type","standard_code","standard_text","verified"}
        if not required_entries.issubset(entry_columns) or not required_standards.issubset(standard_columns):
            return {"error": "Required RPT columns missing"}
        rows = connection.execute("""
            SELECT e.id, e.year_label, e.subject,
                   e.verified, e.content_verified,
                   SUM(CASE WHEN s.standard_type='SK' AND s.verified=1
                         AND TRIM(COALESCE(s.standard_code,''))<>'' AND TRIM(COALESCE(s.standard_text,''))<>''
                         THEN 1 ELSE 0 END),
                   SUM(CASE WHEN s.standard_type='SP' AND s.verified=1
                         AND TRIM(COALESCE(s.standard_code,''))<>'' AND TRIM(COALESCE(s.standard_text,''))<>''
                         THEN 1 ELSE 0 END)
            FROM rpt_entries e
            LEFT JOIN rpt_entry_standards s ON s.rpt_entry_id=e.id
            WHERE e.year_label IN (?,?,?,?,?,?) AND e.subject IN (?,?)
            GROUP BY e.id,e.year_label,e.subject,e.verified,e.content_verified
        """, YEARS + SUBJECTS).fetchall()
        result = {}
        for year in YEARS:
            for subject in SUBJECTS:
                selected = [r for r in rows if r[1] == year and r[2] == subject]
                valid = [r for r in selected if r[3] == 1 and r[4] == 1 and r[5] == 1 and r[6] == 1]
                result[f"{year} / {subject}"] = {
                    "rpt_rows": len(selected),
                    "single_verified_sk_sp": len(valid),
                    "needs_review": len(selected)-len(valid),
                    "missing_or_multiple_sk_sp": sum(r[5] != 1 or r[6] != 1 for r in selected),
                }
        return result
    finally:
        connection.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/audit_pjpk_coverage_v2670.py DB_PATH")
    print(json.dumps(audit(sys.argv[1]), ensure_ascii=False, indent=2))
