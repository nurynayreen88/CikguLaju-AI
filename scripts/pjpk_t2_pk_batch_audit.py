"""Audit all 18 T2 PK editorial RPH against the immutable source-gate inventory.

Run: python scripts/pjpk_t2_pk_batch_audit.py SOURCE_GATE.csv
This is a read-only editorial coverage audit, NOT a production approval.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    ROOT / "docs/pjpk/T2_PK_7_COMPLETE_RPH_EDITORIAL_STAGING_20261024.json",
    ROOT / "docs/pjpk/T2_PK_11_REMAINING_EDITORIAL_STAGING_20261024.json",
)
SECTIONS = ("objective", "materials", "induction", "reinforcement", "closure", "assessment")
FLAGS = ("production_ready", "sk_text_verified", "textbook_verified",
         "rpt_exact_slot_verified", "rph_runtime_verified", "a4_review_verified")


def audit(source_gate):
    with open(source_gate, newline="", encoding="utf-8-sig") as fh:
        source = list(csv.DictReader(fh))
    expected = {int(r["entry_id"]): r for r in source
                if r["year_label"] == "Tahun 2" and r["subject"] == "Pendidikan Kesihatan"
                and r["entry_kind"] == "PDP_CANDIDATE"}
    errors = []
    records = []
    for path in FILES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        records.extend(payload["records"])
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)):
        errors.append("duplicate editorial entry IDs")
    if set(ids) != set(expected):
        errors.append(f"coverage mismatch missing={sorted(set(expected)-set(ids))} extra={sorted(set(ids)-set(expected))}")
    for record in records:
        ident = record["id"]
        src = expected.get(ident)
        if src and (record["topic"] != src["topic"] or record["year"] != src["year_label"]
                    or record["subject"] != src["subject"]):
            errors.append(f"{ident}: source identity mismatch")
        for field in SECTIONS:
            if not isinstance(record.get(field), str) or not record[field].strip():
                errors.append(f"{ident}: missing {field}")
        activities = record.get("activities")
        if not isinstance(activities, list) or len(activities) != 2 or any(
            not isinstance(a, dict) or not a.get("heading") or not a.get("body") for a in activities
        ):
            errors.append(f"{ident}: incomplete activities")
        if record.get("status") != "editorial_staging_only":
            errors.append(f"{ident}: unexpected status")
        if any(record.get(flag) is not False for flag in FLAGS):
            errors.append(f"{ident}: unapproved release flag")
        if src and src["production_ready"] != "0":
            errors.append(f"{ident}: source gate unexpectedly ready")
        if record.get("sp") and not record.get("sp_text_verified") is False:
            errors.append(f"{ident}: SP not clearly marked pending verification")
    return records, expected, errors


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/pjpk_t2_pk_batch_audit.py SOURCE_GATE.csv")
    records, expected, errors = audit(sys.argv[1])
    print(f"T2 PK source candidates={len(expected)} editorial drafts={len(records)}")
    for error in errors:
        print("BLOCK:", error, file=sys.stderr)
    if errors:
        raise SystemExit(1)
    print("PASS: editorial coverage and staging safety; curriculum/runtime approval still pending")
