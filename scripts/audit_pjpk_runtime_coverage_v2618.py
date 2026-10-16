"""Read-only audit of PJPK SK/SP coverage in the bundled runtime DB.

Reassembles only into a temporary directory on the CI runner. Never writes to
or replaces the repository/runtime database. Coverage gaps are reported, not
papered over with invented mappings.
"""
import json
import sqlite3
import tempfile
from pathlib import Path

from audit_pjpk_coverage_v2670 import audit

ROOT = Path(__file__).resolve().parents[1]
DB_STEM = "CikguLaju_Curriculum_Master_v25_93_PI_ENGLISH_Y1_Y4.db"
PARTS = (ROOT / (DB_STEM + ".part1"), ROOT / (DB_STEM + ".part2"))

def main():
    if not all(part.is_file() for part in PARTS):
        raise SystemExit("Runtime DB parts missing; cannot audit real PJPK coverage.")
    with tempfile.TemporaryDirectory(prefix="pjpk-runtime-audit-") as temp:
        target = Path(temp) / DB_STEM
        with target.open("wb") as output:
            for part in PARTS:
                with part.open("rb") as source:
                    while True:
                        block = source.read(1024 * 1024)
                        if not block:
                            break
                        output.write(block)
        with sqlite3.connect(target.as_uri() + "?mode=ro", uri=True) as con:
            integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise SystemExit("Bundled runtime DB integrity failed: " + str(integrity))
        report = audit(str(target))
        if "error" in report:
            raise SystemExit(json.dumps(report, ensure_ascii=False))
        print(json.dumps({"db_integrity": integrity, "coverage": report}, ensure_ascii=False, indent=2))
        print("NOTE: This is an audit only; it does not change or approve any curriculum mapping.")

if __name__ == "__main__":
    main()
