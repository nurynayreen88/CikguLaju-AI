#!/usr/bin/env python3
"""Validate RPT 2027 source mapping CSV without modifying inputs or production DB."""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

REQUIRED = ("record_id", "subject", "year", "source_week", "source_domain",
            "unit_or_topic", "sk_codes", "sp_codes", "textbook_pages",
            "calendar_group", "calendar_2027_status", "review_status",
            "source_file_id", "notes")

def validate(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(REQUIRED) - set(reader.fieldnames or [])
        if missing:
            return [], [f"Missing columns: {sorted(missing)}"]
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            return rows, ["Malformed CSV row or unexpected column count"]
    errors = []
    ids = [r["record_id"] for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate record_id")
    for r in rows:
        key = r["record_id"]
        if not re.fullmatch(r"(PI|PJ)2-\d{3}", key):
            errors.append(f"{key}: invalid record ID")
        if r["year"] != "2":
            errors.append(f"{key}: year must be 2")
        if r["calendar_2027_status"] != "UNVERIFIED":
            errors.append(f"{key}: calendar must remain UNVERIFIED until verified")
        if r["review_status"] == "READY":
            errors.append(f"{key}: premature READY")
        if not r["source_file_id"].strip():
            errors.append(f"{key}: missing source file ID")
        if r["calendar_group"] not in ("UNASSIGNED", "A", "B"):
            errors.append(f"{key}: invalid calendar group")
        for code in filter(None, r["sp_codes"].split(";")):
            if not re.fullmatch(r"\d+\.\d+\.\d+", code.strip()):
                errors.append(f"{key}: malformed SP {code}")
    return rows, errors

def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "data/rpt_2027/year2_source_mapping_seed_20261028.csv")
    rows, errors = validate(path)
    print(f"Source rows: {len(rows)}")
    print(f"Subjects: {dict(Counter(r['subject'] for r in rows))}")
    print(f"Errors: {len(errors)}")
    for error in errors:
        print("ERROR:", error)
    return bool(errors)

if __name__ == "__main__":
    sys.exit(main())
