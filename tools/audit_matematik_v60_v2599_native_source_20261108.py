"""Pre-release Maths v60 mapping audit against Telegram's exact v25.99 DB.

Telegram's app.py _sm2542_rows(year, "Matematik") reads
verified_pdp_sequence_v2 from CikguLaju_Curriculum_Master_v25_99_MATH...
NOT verified_pdp_sequence from the separate v26.00 science master.

Reassemble to an isolated temporary file; SHA256-verify the *whole* database;
read-only SQLite; report actual PdP code / Lesson / SK / SP conflicts.
Never edit source, user data, or existing DBs. This does NOT approve textbooks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from web.matematik_v60_native_coverage import audit_native_mapping
from web.matematik_v60_crosswalk_candidates import make_all_candidates

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "CikguLaju_v25_99_MATH_T1_T6_GIT_SPLIT_MANIFEST.json"
TABLE = "verified_pdp_sequence_v2"
SKIPPED = ("REJECT_NON_SK", "SOURCE_NONCORE", "REJECTED")


def verified_temp_database(folder: Path, root: Path = ROOT) -> Path:
    manifest = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    stem = "CikguLaju_Curriculum_Master_v25_99_MATH_T1_T6_CANONICAL"
    if (manifest.get("source_name") != stem + ".db"
            or manifest.get("source_sha256") !=
               "74f1e139ae6e7f64379ee3fb103334f450c683152186b03368bb02dfe3b8c821"
            or manifest.get("source_size") != 28024832
            or len(manifest.get("parts", [])) != 3):
        raise ValueError("Unknown Maths source snapshot manifest")

    h = hashlib.sha256()
    target = folder / "math_v25_99_audit_readonly.db"
    with target.open("xb") as out:
        for index, part in enumerate(manifest["parts"]):
            filename = f"{stem}.part{index:02d}"
            if part.get("file") != filename:
                raise ValueError("Out-of-order Maths DB source parts")
            source = root / filename
            if source.stat().st_size != part["size"]:
                raise ValueError(f"Maths source part size mismatch: {filename}")
            with source.open("rb") as fh:
                for block in iter(lambda: fh.read(1024 * 1024), b""):
                    h.update(block)
                    out.write(block)
    if target.stat().st_size != manifest["source_size"] or h.hexdigest() != manifest["source_sha256"]:
        raise ValueError("Maths v25.99 original database digest mismatch")
    return target


def audit_snapshot(root: Path = ROOT) -> dict:
    with tempfile.TemporaryDirectory(prefix="math_v60_v2599_") as tmp:
        db = verified_temp_database(Path(tmp), root=root)
        with sqlite3.connect(db.as_uri() + "?mode=ro&immutable=1", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA query_only=ON")
            if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("Maths v25.99 source SQLite corrupt")
            tables = {row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if TABLE not in tables:
                raise ValueError("Real Telegram Maths sequence table is missing")
            cols = {row[1] for row in conn.execute(f"PRAGMA table_info({TABLE})")}
            required = {"year_label", "subject", "pdp_sequence_code",
                        "source_sequence_no", "sk_code", "sp_code", "verification_status"}
            if not required <= cols:
                raise ValueError("Maths native sequence missing columns " +
                                 repr(sorted(required - cols)))
            # EXACT WHERE and ORDER BY rules from app.py _sm2542_rows.
            rows_by_year = {}
            for year in range(2, 7):
                selected = conn.execute(f"""
                    SELECT * FROM {TABLE}
                    WHERE year_label=? AND subject=?
                      AND COALESCE(pdp_sequence_code,'')<>''
                      AND COALESCE(verification_status,'')
                          NOT IN ('REJECT_NON_SK','SOURCE_NONCORE','REJECTED')
                    ORDER BY COALESCE(source_sequence_no,9999), id
                """, (f"Tahun {year}", "Matematik")).fetchall()
                rows_by_year[year] = [dict(row) for row in selected]
            runtime = SimpleNamespace(
                CIKGULAJU_MATH_V2599_SOURCE_VERIFIED=True,
                _sm2542_rows=lambda year, subject:
                    rows_by_year[int(year.split()[-1])] if subject == "Matematik" else [],
            )
            with patch.dict("os.environ", {
                "CIKGULAJU_ENV": "staging",
                "CIKGULAJU_MATEMATIK_V60_STAGING_ENABLED": "1",
            }):
                report = audit_native_mapping(runtime)
            crosswalk = make_all_candidates(rows_by_year)
            report["crosswalk_status_counts"] = crosswalk["status_counts"]
            report["candidate_crosswalk"] = crosswalk

    report["audited_source"] = "Telegram Maths actual v25.99 SHA-verified SQLite"
    report["table"] = TABLE
    report["source_sha256"] = "74f1e139ae6e7f64379ee3fb103334f450c683152186b03368bb02dfe3b8c821"
    report["total_native_rows"] = sum(len(x) for x in rows_by_year.values())
    report["release_decision"] = "HOLD"
    report["release_reasons"] = [
        "Academic validation of textbook and activity book item/page refs incomplete",
        "Authenticated live Web-to-Telegram Word/PDF + subscription/credit E2E not verified",
    ]
    if not report["mapping_ready"]:
        report["release_reasons"].insert(
            0, "Actual native v25.99 Lesson/PdP to v60 mapping is not 585/585")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="Write new JSON audit; refuse overwrite")
    parser.add_argument("--require-mapping", action="store_true",
                        help="Explicit mapping-only gate; fail if not 585/585")
    parser.add_argument("--require-release", action="store_true",
                        help="Strict FINAL READY gate: source, academic, E2E must all be signed")
    args = parser.parse_args()
    result = audit_snapshot()
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        destination = Path(args.output)
        with destination.open("x", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)
    if args.require_mapping and not result["mapping_ready"]:
        raise SystemExit("MAPPING HOLD: Telegram Maths native and v60 identifiers differ")
    if args.require_release and not (
        result["mapping_ready"]
        and result.get("academic_signoff") is True
        and result.get("runtime_e2e_passed") is True
        and result.get("release_decision") == "READY"
    ):
        raise SystemExit("RELEASE HOLD: academic, native mapping and E2E signoff incomplete")


if __name__ == "__main__":
    main()
