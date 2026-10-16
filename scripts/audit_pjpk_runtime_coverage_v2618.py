"""Read-only discovery of PJPK RPT/SK/SP coverage across bundled DB checkpoints.

All reconstructed databases live only in a temporary CI directory. No source
DB, production DB, or curriculum mapping is modified.
"""
import json
import sqlite3
import tempfile
from pathlib import Path

from audit_pjpk_coverage_v2670 import audit

ROOT = Path(__file__).resolve().parents[1]
STEMS = (
    "CikguLaju_Curriculum_Master_v25_89_PI_T1_T6_JAWI_COMPLETE_FINAL.db",
    "CikguLaju_Curriculum_Master_v25_90_RUNTIME_PLUS_PI_T1_T6.db",
    "CikguLaju_Curriculum_Master_v25_91_PI_RPT_T1_T6_COMPLETE.db",
    "CikguLaju_Curriculum_Master_v25_92_PI_ENGLISH_Y1_Y3.db",
    "CikguLaju_Curriculum_Master_v25_93_PI_ENGLISH_Y1_Y4.db",
)

def inspect_db(target):
    with sqlite3.connect(target.as_uri() + "?mode=ro", uri=True) as con:
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        report = {"db_integrity": integrity, "tables_have_rpt_entries": "rpt_entries" in tables,
                  "tables_have_rpt_entry_standards": "rpt_entry_standards" in tables}
        if "rpt_entries" in tables:
            report["pjpk_subject_labels"] = [
                {"year_label": row[0], "subject": row[1], "rows": row[2]}
                for row in con.execute(
                    "SELECT year_label, subject, COUNT(*) FROM rpt_entries "
                    "WHERE lower(COALESCE(subject,'')) LIKE '%jasmani%' "
                    "OR lower(COALESCE(subject,'')) LIKE '%kesihatan%' "
                    "OR lower(COALESCE(subject,'')) LIKE '%pjpk%' "
                    "OR lower(trim(COALESCE(subject,''))) IN ('pj','pk') "
                    "GROUP BY year_label, subject ORDER BY year_label, subject"
                )
            ]
            report["rpt_subject_counts"] = [
                {"subject": row[0], "rows": row[1]}
                for row in con.execute(
                    "SELECT subject, COUNT(*) FROM rpt_entries GROUP BY subject ORDER BY subject"
                )
            ]
        return report

def main():
    results = {}
    with tempfile.TemporaryDirectory(prefix="pjpk-db-discovery-") as temp:
        for stem in STEMS:
            parts = (ROOT / (stem + ".part1"), ROOT / (stem + ".part2"))
            if not all(part.is_file() for part in parts):
                results[stem] = {"status": "parts_missing"}
                continue
            target = Path(temp) / stem
            with target.open("wb") as output:
                for part in parts:
                    with part.open("rb") as source:
                        while True:
                            block = source.read(1024 * 1024)
                            if not block:
                                break
                            output.write(block)
            report = inspect_db(target)
            if report.get("db_integrity") != "ok":
                raise SystemExit(f"SQLite integrity failed for {stem}: {report}")
            if report.get("tables_have_rpt_entries") and report.get("tables_have_rpt_entry_standards"):
                report["exact_label_coverage"] = audit(str(target))
            results[stem] = report
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("NOTE: Discovery is read-only. Do not activate a DB merely because it contains PJPK-labelled rows; exact SK/SP verification is still required.")

if __name__ == "__main__":
    main()
