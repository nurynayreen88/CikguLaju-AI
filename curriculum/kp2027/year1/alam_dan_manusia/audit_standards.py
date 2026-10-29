"""Fail-closed audit for KP2027 Year 1 Alam dan Manusia standards.

Usage: python curriculum/kp2027/year1/alam_dan_manusia/audit_standards.py path/to/standards.json
Does not write to any database or mark content ready.
"""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

REQUIRED = ("curriculum", "year", "subject", "unit", "lesson",
            "standard_code", "standard_text", "source_url", "source_page",
            "verification_status")


def audit(records):
    errors = []
    if not isinstance(records, list) or not records:
        return ["Expected a non-empty list of sourced standards"]
    seen = set()
    for i, row in enumerate(records, 1):
        prefix = f"record {i}"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: expected object")
            continue
        missing = [key for key in REQUIRED if key not in row]
        if missing:
            errors.append(f"{prefix}: missing {', '.join(missing)}")
            continue
        if row["curriculum"] != "KP2027" or type(row["year"]) is not int or row["year"] != 1 or row["subject"] != "Alam dan Manusia":
            errors.append(f"{prefix}: wrong curriculum/year/subject")
        for key in ("unit", "standard_code", "standard_text"):
            if not isinstance(row[key], str) or not row[key].strip():
                errors.append(f"{prefix}: empty {key}")
        if type(row["lesson"]) is not int or row["lesson"] < 1:
            errors.append(f"{prefix}: invalid lesson")
        if type(row["source_page"]) is not int or row["source_page"] < 1:
            errors.append(f"{prefix}: invalid source_page")
        url = row["source_url"]
        if not isinstance(url, str) or urlparse(url).scheme not in ("https", "http") or not urlparse(url).netloc:
            errors.append(f"{prefix}: invalid source_url")
        if row["verification_status"] not in ("pending", "verified", "approved"):
            errors.append(f"{prefix}: invalid verification_status")
        if row["verification_status"] == "approved" and not (row.get("approved_by") and row.get("approved_at")):
            errors.append(f"{prefix}: approved without reviewer/date")
        # Malformed JSON fields can be lists/dicts; never crash during audit.
        identity = (row["unit"], row["lesson"], row["standard_code"])
        if all(isinstance(v, (str, int)) for v in identity):
            if identity in seen:
                errors.append(f"{prefix}: duplicate unit/lesson/standard")
            seen.add(identity)
        else:
            errors.append(f"{prefix}: invalid identity fields")
    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: audit_standards.py standards.json", file=sys.stderr)
        return 2
    try:
        records = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"Cannot read JSON: {exc}", file=sys.stderr)
        return 2
    errors = audit(records)
    if errors:
        print("NOT READY: " + "; ".join(errors))
        return 1
    pending = sum(r["verification_status"] != "approved" for r in records)
    if pending:
        print(f"NOT READY: {pending} records await manual approval")
        return 1
    print(f"VALIDATED: {len(records)} approved records; source authenticity still requires human verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
