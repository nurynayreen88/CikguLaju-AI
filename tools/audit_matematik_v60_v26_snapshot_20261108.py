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
            required = {"year_label", "subject", "pdp_sequence_code",
                        "source_sequence_no", "sk_code", "sp_code"}
            if not required <= cols:
                raise RuntimeError("Required native mapping columns missing: "
                                   + repr(sorted(required - cols)))
            rows = [dict(row) for row in conn.execute(
                """SELECT * FROM verified_pdp_sequence
                   WHERE lower(trim(subject)) IN ('matematik','mathematics','math')"""
            )]
            filtered = [row for row in rows
                        if str(row.get("verification_status") or "").strip().upper()
                        not in REJECTED]
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
                    0, "Static native PdP and v60 mapping does not reconcile 585/585")
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
