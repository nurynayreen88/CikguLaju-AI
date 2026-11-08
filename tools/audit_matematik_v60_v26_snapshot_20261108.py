"""Audit Matematik v60 vs SHA-verified *static* v26.00 SQLite, read-only.

This is a preflight inventory, not a live Telegram/Web E2E test or academic
teacher sign-off. Never use a fallback DB and never mutate any original file.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.audit_sains_v26_readonly_20261106 import verify_and_rebuild
from web.matematik_v60_native_coverage import audit_native_mapping

REJECTED = {"REJECT_NON_SK", "SOURCE_NONCORE", "REJECTED"}


def audit_snapshot():
    with tempfile.TemporaryDirectory(prefix="math_v60_snapshot_") as tmp:
        db = verify_and_rebuild(Path(tmp))
        with sqlite3.connect(db.resolve().as_uri() + "?mode=ro&immutable=1", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA query_only=ON")
            if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise RuntimeError("Static DB v26.00 quick_check failed")
            cols = {row[1] for row in conn.execute(
                "PRAGMA table_info(verified_pdp_sequence)")}
            required = {"year_label", "subject", "sk_code", "sp_code"}
            if not required <= cols:
                raise RuntimeError("Required raw source columns missing: "
                                   + repr(sorted(required - cols)))
            rows = [dict(row) for row in conn.execute(
                """SELECT * FROM verified_pdp_sequence
                   WHERE lower(trim(subject)) IN ('matematik','mathematics','math')"""
            )]
            filtered = [row for row in rows
                        if str(row.get("verification_status") or "").strip().upper()
                        not in REJECTED]
            native_keys = {"pdp_sequence_code", "source_sequence_no"}
            if not native_keys <= cols:
                # The v26.00 SQLite *raw* source has no materialized native
                # Lesson/PdP identity: the Telegram runtime derives it.
                # Never invent one by row number/week/title. Report what is
                # actually in the snapshot and require runtime verification.
                by_year = {}
                for year in range(2, 7):
                    subset = [row for row in filtered
                              if row.get("year_label") == f"Tahun {year}"]
                    by_year[str(year)] = {
                        "source": 117,
                        "raw_source_rows_not_pdp": len(subset),
                        "raw_distinct_sksp": len({
                            (str(row.get("sk_code") or "").strip(),
                             str(row.get("sp_code") or "").strip())
                            for row in subset
                        }),
                        "rows_without_sksp": sum(
                            not str(row.get("sk_code") or "").strip()
                            or not str(row.get("sp_code") or "").strip()
                            for row in subset),
                        "rows_without_textbook_ref": sum(
                            not str(row.get("textbook_ref") or "").strip()
                            for row in subset),
                        "native_pdp": 0, "matched": 0, "unmatched": 117,
                        "conflicts": 0,
                        "note": "Raw source rows are NOT native Telegram PdP identifiers",
                    }
                report = {
                    "version": "v60",
                    "source_lessons": 585,
                    "matched": 0,
                    "mapping_ready": False,
                    "per_year": by_year,
                    "missing_native_identity_columns": sorted(native_keys - cols),
                    "source_table_columns": sorted(cols),
                    "mapping_requirement": (
                        "Audit real staging Telegram _sm2542_rows after native "
                        "sequence derivation; do not equate DB rows with lessons"),
                    "academic_signoff": False,
                    "runtime_e2e_passed": False,
                }
            else:
                runtime = SimpleNamespace(
                    CIKGULAJU_DB_V2600_ACTIVE=True,
                    _sm2542_rows=lambda year, subject: [
                        row for row in filtered
                        if row.get("year_label") == year
                    ])
                with patch.dict("os.environ", {
                    "CIKGULAJU_ENV": "staging",
                    "CIKGULAJU_MATEMATIK_V60_STAGING_ENABLED": "1",
                }):
                    report = audit_native_mapping(runtime)
            report["audit_origin"] = (
                "SHA-verified v26.00 repo snapshot; filtered verified_pdp_sequence; "
                "NOT live Render DB, NOT user-ready")
            report["static_source_rows"] = len(rows)
            report["excluded_source_rows"] = len(rows) - len(filtered)
            report["release_decision"] = "HOLD"
            report["release_reasons"] = [
                "Teacher-level Buku Teks/Buku Aktiviti signoff not complete",
                "Live Telegram/Web A4 Word/PDF + authentication/credits E2E missing",
            ]
            if not report["mapping_ready"]:
                report["release_reasons"].insert(
                    0, "Native Telegram derived PdP identity unavailable or "
                       "not uniquely reconciled to 585 v60 lessons")
            return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="Optional new audit JSON output")
    args = parser.parse_args()
    report = audit_snapshot()
    blob = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        path = Path(args.output)
        if path.exists():
            raise FileExistsError("Refusing to overwrite audit output")
        path.write_text(blob + "\n", encoding="utf-8")
    print(blob)


if __name__ == "__main__":
    main()
