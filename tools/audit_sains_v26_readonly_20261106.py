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


def profile_rows_without_sequence_code(conn: sqlite3.Connection) -> dict:
    """Report observed DB row facts only; DO NOT equate rows/weeks with PdP."""
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        """SELECT * FROM verified_pdp_sequence
           WHERE lower(trim(subject)) IN ('sains', 'science')
           ORDER BY id"""
    )]
    per_year = {}
    for year in WORKING_TARGETS:
        sample = [r for r in rows if str(r.get("year_label") or "").strip() == f"Tahun {year}"]
        statuses = Counter(str(r.get("verification_status") or "").strip() or "(empty)"
                           for r in sample)
        sources = Counter(str(r.get("source_kind") or "").strip() or "(empty)"
                          for r in sample)
        possible = {(str(r.get("week_no") or ""), str(r.get("unit_code") or ""),
                     str(r.get("unit_title") or ""), str(r.get("pdp_title") or ""))
                    for r in sample}
        per_year[str(year)] = {
            "db_source_rows_NOT_PDP": len(sample),
            "distinct_row_ids": len({r.get("id") for r in sample}),
            "distinct_week_unit_title_combinations_NOT_PDP": len(possible),
            "weak_sksp_rows": sum(not str(r.get("sk_code") or "").strip()
                                   or not str(r.get("sp_code") or "").strip()
                                   for r in sample),
            "rows_without_textbook_ref": sum(not str(r.get("textbook_ref") or "").strip()
                                             for r in sample),
            "status_counts": dict(statuses),
            "source_kind_counts": dict(sources),
            "first_two_rows": [
                {k: r.get(k) for k in (
                    "id", "week_no", "theme", "unit_code", "unit_title",
                    "pdp_title", "sk_code", "sp_code", "textbook_ref")}
                for r in sample[:2]
            ],
        }
    return {
        "yearly_raw_source_profile": per_year,
        "raw_source_rows_total_NOT_PDP": len(rows),
        "note": "Source rows, titles and weeks CANNOT certify number of distinct RPH/PdP. Resolve native Telegram sequence first.",
    }


def profile_science_candidate_tables(conn: sqlite3.Connection) -> dict:
    """Find other science sources without promoting RPT weeks to PdP identity."""
    preferred = (
        "rpt_entries", "rpt_entry_standards", "rpt_source_catalog",
        "rpt_subject_profiles", "pdp_flow_profile", "rpt_lesson_mapping_status",
        "curriculum_standards",
    )
    existing = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    out = {}
    for name in preferred:
        if name not in existing:
            continue
        cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{name}")')]
        info = {"columns": cols}
        if "subject" in cols:
            sql = f'SELECT * FROM "{name}" WHERE lower(trim(subject)) LIKE ? LIMIT 20001'
            found = [dict(r) for r in conn.execute(sql, ("%sains%",))]
            info["science_named_rows_UP_TO_20001"] = len(found)
            info["truncated"] = len(found) == 20001
            ycol = next((c for c in ("year_label", "grade", "year", "academic_year")
                         if c in cols), None)
            if ycol:
                info["year_value_counts"] = dict(Counter(str(r.get(ycol) or "")
                                                         for r in found))
            info["first_two_rows"] = [
                {key: r.get(key) for key in (
                    "id", "year_label", "grade", "week_no", "unit_code",
                    "unit_title", "topic", "pdp_title", "sk_code", "sp_code",
                    "textbook_ref", "verification_status")
                 if key in cols}
                for r in found[:2]
            ]
        out[name] = info
    return out


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
                "missing_columns": sorted(required_cols - cols),
                "raw_source_profile": profile_rows_without_sequence_code(conn),
                "candidate_science_tables": profile_science_candidate_tables(conn),
                "available_columns": sorted(cols),
                "related_tables": sorted(t for t in tables if any(
                    k in t.lower() for k in ("sci", "sains", "pdp", "rpt", "sequence")))}
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


def historical_v25_68_comparison(tmp: Path) -> dict:
    """Independent checkpoint comparison, NEVER a runtime fallback or migration."""
    stem = "CikguLaju_Curriculum_Master_v25_68_SCIENCE_MATH_UPLOAD_READY.db"
    parts = [ROOT / (stem + f".part{i:02d}") for i in range(3)]
    if not all(p.is_file() for p in parts):
        return {"status": "checkpoint_parts_missing"}
    dest = tmp / "v25_68_reference_only.db"
    h = hashlib.sha256()
    with dest.open("wb") as out:
        for part in parts:
            with part.open("rb") as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    h.update(block)
                    out.write(block)
    result = {
        "checkpoint": "v25.68 historical only, never use for current runtime",
        "size_bytes": dest.stat().st_size,
        "sha256_observed_NOT_authenticated_manifest": h.hexdigest(),
    }
    with sqlite3.connect(dest.resolve().as_uri() + "?mode=ro&immutable=1",
                         uri=True) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only=ON")
        result["quick_check"] = con.execute("PRAGMA quick_check").fetchone()[0]
        tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if "verified_pdp_sequence" not in tables:
            result["sequence_table_present"] = False
            return result
        cols = {r[1] for r in con.execute(
            "PRAGMA table_info(verified_pdp_sequence)")}
        result["sequence_columns"] = sorted(cols)
        if {"subject", "year_label"} <= cols:
            rows = [dict(r) for r in con.execute(
                """SELECT * FROM verified_pdp_sequence
                   WHERE lower(trim(subject)) IN ('sains', 'science')"""
            )]
            result["sains_source_rows_not_pdp"] = len(rows)
            result["sains_rows_without_sk_or_sp"] = sum(
                not str(r.get("sk_code") or "").strip()
                or not str(r.get("sp_code") or "").strip() for r in rows)
            result["sains_rows_without_textbook_ref"] = sum(
                not str(r.get("textbook_ref") or "").strip() for r in rows)
            result["verification_status_rows"] = dict(Counter(
                str(r.get("verification_status") or "").strip() or "(empty)"
                for r in rows))
            result["boundary_qa_pending_all_23"] = [
                {k: r.get(k) for k in ("id", "year_label", "pdp_sequence_code",
                  "source_sequence_no", "unit_code", "unit_title", "pdp_title",
                  "sk_code", "sp_code", "verification_status")}
                for r in rows if str(r.get("verification_status") or "").strip()
                == "PDP_BOUNDARY_QA_PENDING"
            ][:100]
            result["source_fields_population"] = {
                key: sum(bool(str(r.get(key) or "").strip()) for r in rows)
                for key in ("source_url", "activitybook_ref", "notes", "skill_metadata")
            }
            result["year_quality"] = {
                str(y): {
                    "source_rows": sum(str(r.get("year_label") or "").strip() == f"Tahun {y}" for r in rows),
                    "rows_without_sk_or_sp": sum(
                        str(r.get("year_label") or "").strip() == f"Tahun {y}"
                        and (not str(r.get("sk_code") or "").strip()
                             or not str(r.get("sp_code") or "").strip()) for r in rows),
                    "rows_without_textbook_ref": sum(
                        str(r.get("year_label") or "").strip() == f"Tahun {y}"
                        and not str(r.get("textbook_ref") or "").strip() for r in rows),
                } for y in WORKING_TARGETS
            }
            result["year_rows"] = dict(Counter(
                str(r.get("year_label") or "") for r in rows))
            if "pdp_sequence_code" in cols:
                result["unique_pdp_codes_by_year"] = {
                    str(y): len({str(r.get("pdp_sequence_code") or "").strip()
                                 for r in rows
                                 if str(r.get("year_label") or "").strip() == f"Tahun {y}"
                                 and str(r.get("pdp_sequence_code") or "").strip()})
                    for y in WORKING_TARGETS
                }
        else:
            result["source_column_mismatch"] = True
    return result


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="cikgulaju_sains_audit_") as tmp:
        db = verify_and_rebuild(Path(tmp))
        # immutable, query_only, mode=ro ensures no DB migrations or WAL writes.
        with sqlite3.connect(db.resolve().as_uri() + "?mode=ro&immutable=1",
                             uri=True) as conn:
            result = audit(conn)
        result["historical_v25_68_reference"] = historical_v25_68_comparison(Path(tmp))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
