"""Simulate FIVE DSKP-checked Y3 title fixes on a temporary v25.68 copy.

This is *not* a migration, deploy, teacher sign-off, or a runtime fallback.
Never opens production DB or writes any source .part files. Explicitly rolls
back its transaction, then deletes the throwaway copied SQLite database.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "audits/sains_y3_23_source_candidate_ledger_20261106.json"
PART_PREFIX = "CikguLaju_Curriculum_Master_v25_68_SCIENCE_MATH_UPLOAD_READY.db"
# Observed read-only checkpoint SHA in CI #42177830409; no upstream manifest.
OBSERVED_HISTORICAL_SHA = "79845954db3f8a7c9e9b83ac1eb13477b64a92d0b9c12cfcd5ddd799b0f3f53b"


def replay_temp_only():
    ledger = json.loads(LEDGER.read_text("utf-8"))
    proposals = [r for r in ledger["records"] if not r["original_title_matches_dskp"]]
    if ledger["status"] != "DRAF_SOURCE_CROSSCHECK_ONLY_NOT_DB_EDIT" or len(proposals) != 5:
        raise RuntimeError("Unsafe or altered review ledger")
    expected_ids = {282+1, 282+4, 282+10, 282+19, 282+20}
    # 002=283, 005=286, 011=292, 020=301, 021=302.
    assert expected_ids == {283, 286, 292, 301, 302}
    if {r["historical_row_id"] for r in proposals} != expected_ids:
        raise ValueError("Unexpected title repair targets")
    with tempfile.TemporaryDirectory(prefix="cikgulaju_sains_y3_sim_") as td:
        target = Path(td) / "staging_simulation_NOT_production.db"
        h = hashlib.sha256()
        parts = [ROOT / (PART_PREFIX + f".part{i:02d}") for i in range(3)]
        with target.open("wb") as dst:
            for part in parts:
                with part.open("rb") as src:
                    for chunk in iter(lambda: src.read(1024*1024), b""):
                        dst.write(chunk)
                        h.update(chunk)
        if h.hexdigest() != OBSERVED_HISTORICAL_SHA:
            raise ValueError("Historical DB parts changed; stop patch simulation")
        with sqlite3.connect(target) as db:
            db.row_factory = sqlite3.Row
            if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("Historical DB corrupt")
            original = {int(r["id"]): dict(r) for r in db.execute(
                "SELECT * FROM verified_pdp_sequence WHERE subject='Sains'")}
            if len(original) != 385:
                raise ValueError("Unexpected Sains historical inventory")
            db.execute("BEGIN IMMEDIATE")
            changed = []
            try:
                for p in proposals:
                    cursor = db.execute(
                        """UPDATE verified_pdp_sequence SET pdp_title=?
                           WHERE id=? AND year_label='Tahun 3' AND subject='Sains'
                           AND pdp_sequence_code=? AND sp_code=?
                           AND pdp_title=?
                           AND verification_status='PDP_BOUNDARY_QA_PENDING'""",
                        (p["candidate_pdp_title"], p["historical_row_id"],
                         p["pdp_code"], p["sp_code"], p["original_pdp_title"]))
                    if cursor.rowcount != 1:
                        raise ValueError("Source row/expected title mismatch for " + p["pdp_code"])
                    changed.append(p["historical_row_id"])
                after = {int(r["id"]): dict(r) for r in db.execute(
                    "SELECT * FROM verified_pdp_sequence WHERE subject='Sains'")}
                if original.keys() != after.keys() or len(changed) != 5:
                    raise ValueError("Unexpected row count change")
                differences = {}
                for rid in original:
                    keys_changed = {k for k in original[rid]
                                    if original[rid][k] != after[rid][k]}
                    if keys_changed:
                        differences[rid] = keys_changed
                if differences != {rid: {"pdp_title"} for rid in expected_ids}:
                    raise ValueError("Unexpected field changed: " + repr(differences))
            finally:
                db.rollback()
            restored = {int(r["id"]): dict(r) for r in db.execute(
                "SELECT * FROM verified_pdp_sequence WHERE subject='Sains'")}
            if restored != original or db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("Rollback/integrity check failed")
    return {
        "checkpoint": "historical v25.68 test copy only",
        "simulated_title_replacements": len(expected_ids),
        "simulated_row_ids": sorted(expected_ids),
        "allowed_columns_changed": ["pdp_title"],
        "sk_sp_and_verification_status_untouched": True,
        "rolled_back_and_deleted_temporary_copy": True,
        "source_database_or_user_runtime_modified": False,
        "academic_release_status": "HOLD",
    }


if __name__ == "__main__":
    print(json.dumps(replay_temp_only(), indent=2, ensure_ascii=False))
