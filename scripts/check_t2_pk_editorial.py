"""Read-only editorial QA for the 18 T2 PK staging records; never authorizes release."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "docs/pjpk/T2_PK_11_REMAINING_EDITORIAL_STAGING_20261024.json",
    ROOT / "docs/pjpk/T2_PK_7_COMPLETE_RPH_EDITORIAL_STAGING_20261024.json",
]
REQUIRED = ("id", "year", "subject", "topic", "objective", "materials",
            "induction", "activities", "reinforcement", "closure", "assessment",
            "teacher_fields", "status", "production_ready")
LOCKS = ("sk_text_verified", "sp_text_verified", "textbook_verified",
         "rpt_exact_slot_verified", "rph_runtime_verified", "a4_review_verified")
TEACHER = ("date", "day", "class", "time", "duration_minutes", "reflection")

def audit():
    errors, records = [], []
    for path in FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.get("records")
        if not isinstance(rows, list):
            errors.append(f"{path.name}: records must be a list")
            continue
        records.extend(rows)
    ids = [r.get("id") for r in records]
    if len(records) != 18:
        errors.append(f"Expected 18 records, got {len(records)}")
    if len(set(ids)) != len(ids):
        errors.append("Duplicate IDs")
    for r in records:
        ident = r.get("id", "?")
        for key in REQUIRED:
            if key not in r or r[key] is None or (isinstance(r[key], str) and not r[key].strip()):
                errors.append(f"{ident}: missing {key}")
        if r.get("year") != "Tahun 2" or r.get("subject") != "Pendidikan Kesihatan":
            errors.append(f"{ident}: unexpected subject/year")
        acts = r.get("activities")
        if not isinstance(acts, list) or len(acts) != 2 or any(
            not isinstance(a, dict) or not str(a.get("heading", "")).strip()
            or not str(a.get("body", "")).strip() for a in acts
        ):
            errors.append(f"{ident}: incomplete activity pair")
        fields = r.get("teacher_fields")
        if not isinstance(fields, dict) or any(k not in fields for k in TEACHER):
            errors.append(f"{ident}: teacher fields missing")
        if r.get("status") != "editorial_staging_only" or r.get("production_ready") is not False:
            errors.append(f"{ident}: unsafe release state")
        if any(r.get(k) is not False for k in LOCKS):
            errors.append(f"{ident}: verification lock not false")
        if not isinstance(r.get("sp"), list):
            errors.append(f"{ident}: sp must be list")
    return errors, len(records), len(set(ids))

if __name__ == "__main__":
    errors, count, unique = audit()
    print(f"T2 PK editorial records: {count}; unique IDs: {unique}; errors: {len(errors)}")
    for error in errors:
        print("FAIL:", error, file=sys.stderr)
    if errors:
        raise SystemExit(1)
    print("PASS: static editorial checks only. RPT, source, bot runtime and A4 release gates remain blocked.")
