"""Read-only Sains T1-T6 source inventory; NEVER a FINAL READY certification.

Inspects the *shipped* v26.00 SQLite parts (hash checked), not production
credentials or writable database paths. Targets of 92/92/103/88/116/96 are
working master planning figures, not assumed facts about DB coverage.
Run: python tools/audit_sains_v26_readonly_20261106.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKING_TARGETS = {1: 92, 2: 92, 3: 103, 4: 88, 5: 116, 6: 96}
EXCLUDED = {"REJECT_NON_SK", "SOURCE_NONCORE", "REJECTED"}


def verify_and_rebuild(temp: Path, root: Path = ROOT) -> Path:
    """Build a temporary copy only; verify every part and full DB digest."""
    manifest = json.loads((root / "v26_00_manifest.json").read_text("utf-8"))
    if manifest.get("source") != "CikguLaju_Curriculum_Master_v26_00.db":
        raise ValueError("Unexpected master source")
    parts = manifest.get("parts")
    if not isinstance(parts, list) or len(parts) != 3:
        raise ValueError("Unexpected master part manifest")
    target = temp / "sains_master_readonly.db"
    combined = hashlib.sha256()
    with target.open("wb") as dst:
        for part in parts:
            src = root / part["file"]
            if src.parent != root or src.stat().st_size != part["size"]:
                raise ValueError("Missing/changed database part: " + str(src.name))
            digest = hashlib.sha256()
            with src.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    combined.update(chunk)
                    digest.update(chunk)
                    dst.write(chunk)
            if digest.hexdigest() != part["sha256"]:
                raise ValueError("Part SHA mismatch: " + src.name)
    if target.stat().st_size != manifest["size"]:
        raise ValueError("DB size mismatch")
    if combined.hexdigest() != manifest["sha256"]:
        raise ValueError("DB SHA mismatch")
    return target


def summarize_rows(rows: list[dict]) -> dict:
    """Count unique lesson IDs; multiple SP rows in one PdP count ONCE."""
    report = {}
    for year in WORKING_TARGETS:
        year_rows = [r for r in rows if str(r.get("year_label") or "").strip() == f"Tahun {year}"]
        groups = defaultdict(list)
        missing_code = 0
        for r in year_rows:
            code = str(r.get("pdp_sequence_code") or "").strip()
            if code:
                groups[code].append(r)
            else:
                missing_code += 1

        missing_sksp = []
        conflicting_units = []
        missing_page = 0
        statuses = Counter()
        noncontiguous = False
        sequence_numbers = set()
        for code, entries in groups.items():
            units = {
                (str(e.get("unit_code") or "").strip(),
                 str(e.get("unit_title") or "").strip())
                for e in entries
            }
            if len(units) > 1:
                conflicting_units.append(code)
            seen = set()
            has_page = False
            for e in entries:
                statuses[str(e.get("verification_status") or "").strip() or "(empty)"] += 1
                sk, sp = (str(e.get(k) or "").strip() for k in ("sk_code", "sp_code"))
                if sk and sp:
                    seen.add((sk, sp))
                if str(e.get("textbook_ref") or "").strip():
                    has_page = True
                number = str(e.get("source_sequence_no") or "").strip()
                if number.isdigit():
                    sequence_numbers.add(int(number))
            if not seen:
                missing_sksp.append(code)
            if not has_page:
                missing_page += 1

        if sequence_numbers:
            noncontiguous = sorted(sequence_numbers) != list(
                range(min(sequence_numbers), max(sequence_numbers) + 1)
            )
        count = len(groups)
        report[str(year)] = {
            "working_master_target_unverified": WORKING_TARGETS[year],
            "db_rows": len(year_rows),
            "db_distinct_pdp": count,
            "difference_from_working_target": count - WORKING_TARGETS[year],
            "missing_pdp_code_rows": missing_code,
            "groups_without_sksp": len(missing_sksp),
            "groups_with_conflicting_units": len(conflicting_units),
            "groups_without_textbook_ref": missing_page,
            "verification_status_row_counts": dict(sorted(statuses.items())),
            "source_sequence_number_count": len(sequence_numbers),
            "source_sequence_number_gaps": noncontiguous,
            "sample_blocking_codes": sorted(set(missing_sksp + conflicting_units))[:10],
        }
    return report


def audit(conn: sqlite3.Connection) -> dict:
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise ValueError("Database integrity check failed")
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    required = {"verified_pdp_sequence"}
    if not required <= tables:
        return {"source": "v26.00", "release_decision": "HOLD",
                "reason": "verified_pdp_sequence absent", "tables": sorted(
                    t for t in tables if "rpt" in t.lower() or "pdp" in t.lower())}
    cols = {r[1] for r in conn.execute("PRAGMA table_info(verified_pdp_sequence)")}
    required_cols = {"year_label", "subject", "pdp_sequence_code", "sk_code", "sp_code"}
    if not required_cols <= cols:
        return {"source": "v26.00", "release_decision": "HOLD",
                "reason": "verified_pdp_sequence schema differs",
                "missing_columns": sorted(required_cols - cols)}
    rows = [dict(r) for r in conn.execute(
        """SELECT * FROM verified_pdp_sequence
           WHERE lower(trim(subject)) IN ('sains', 'science')"""
    )]
    active = [r for r in rows
              if str(r.get("verification_status") or "").strip().upper() not in EXCLUDED]
    yearly = summarize_rows(active)
    rejected = len(rows) - len(active)
    # RPT weeks cannot stand in for individual lesson identities.
    decision = "HOLD"
    reasons = ["No per-PdP DSKP/textbook/content audit or Word/PDF print test yet"]
    if sum(y["db_distinct_pdp"] for y in yearly.values()) != sum(WORKING_TARGETS.values()):
        reasons.append("DB unique PdP count differs from unverified 587 working target")
    if any(y["missing_pdp_code_rows"] or y["groups_without_sksp"] or
           y["groups_with_conflicting_units"] for y in yearly.values()):
        reasons.append("Sequence structure requires source-level review")
    if any(y["groups_without_textbook_ref"] for y in yearly.values()):
        reasons.append("Some source PdP lack explicit textbook reference")
    return {
        "source": "v26.00 hashed parts (read-only temporary copy)",
        "release_decision": decision,
        "reasons": reasons,
        "rejected_rows_excluded": rejected,
        "yearly": yearly,
        "working_master_total_unverified": sum(WORKING_TARGETS.values()),
        "db_distinct_pdp_total": sum(y["db_distinct_pdp"] for y in yearly.values()),
        "rpt_2027_science_dir_in_main": (ROOT / "rpt_2027" / "sains").exists(),
        "note": "This only inventories the static DB. Telegram runtime, RPH quality, KP2027 and live Web downloads remain untested.",
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="cikgulaju_sains_audit_") as tmp:
        db = verify_and_rebuild(Path(tmp))
        # immutable, query_only, mode=ro ensures no DB migrations or WAL writes.
        with sqlite3.connect(db.resolve().as_uri() + "?mode=ro&immutable=1",
                             uri=True) as conn:
            result = audit(conn)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
