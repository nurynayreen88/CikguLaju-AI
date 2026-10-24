"""Read-only validation of complete PJPK editorial RPH JSON against evidence overlay.

This module never imports the production app or writes to the database.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "docs/pjpk/T5_PK_3_COMPLETE_RPH_STAGING_20261024.json"
OVERLAY_PATH = ROOT / "docs/pjpk/T5_PK_3_VERIFIED_EVIDENCE_OVERLAY_20261024.csv"
TEXT_FIELDS = ("unit", "topic", "objective", "materials", "assessment", "induction",
               "reinforcement", "closure", "source")
TEACHER_FIELDS = ("date", "day", "class", "time", "duration_minutes", "reflection")
GATES = ("rpt_exact_slot_verified", "rph_runtime_verified", "a4_review_verified")

def audit(json_path=JSON_PATH, overlay_path=OVERLAY_PATH):
    payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
    with open(overlay_path, newline="", encoding="utf-8-sig") as fh:
        overlay_rows = list(csv.DictReader(fh))
    overlay = {int(r["entry_id"]): r for r in overlay_rows}
    errors = []
    rows = payload.get("records", [])
    ids = [r.get("id") for r in rows]
    if payload.get("schema_version") != 1:
        errors.append("Unsupported schema version")
    if len(ids) != len(set(ids)) or len(overlay) != len(overlay_rows):
        errors.append("Duplicate IDs")
    if set(ids) != set(overlay) or len(ids) != 3:
        errors.append("RPH and evidence ID sets do not match")
    for row in rows:
        ident = row.get("id")
        if ident not in overlay:
            continue
        source = overlay[ident]
        if row.get("year") != source["year_label"] or row.get("subject") != source["subject"]:
            errors.append(f"{ident}: year or subject mismatch")
        for field, source_field in (("unit", "unit_title"), ("topic", "topic"),
                                    ("sk", "dskp_sk"), ("dskp_page", "verified_dskp_printed_page"),
                                    ("textbook_pages", "verified_textbook_printed_pages")):
            if row.get(field) != source[source_field]:
                errors.append(f"{ident}: {field} mismatch")
        if row.get("sp") != source["dskp_sp"].split(";"):
            errors.append(f"{ident}: SP mismatch")
        for field in TEXT_FIELDS:
            if not isinstance(row.get(field), str) or not row[field].strip():
                errors.append(f"{ident}: missing {field}")
        activities = row.get("activities")
        if not isinstance(activities, list) or len(activities) < 2:
            errors.append(f"{ident}: fewer than two complete activities")
        else:
            for index, activity in enumerate(activities, 1):
                if (not isinstance(activity, dict)
                    or not str(activity.get("heading", "")).startswith(f"Aktiviti {index} ")
                    or len(str(activity.get("body", "")).strip()) < 70):
                    errors.append(f"{ident}: incomplete activity {index}")
        fields = row.get("teacher_fields")
        if not isinstance(fields, dict) or set(fields) != set(TEACHER_FIELDS):
            errors.append(f"{ident}: teacher fields invalid")
        elif any(value is not None for value in fields.values()):
            errors.append(f"{ident}: unverified teacher details prefilled")
        if row.get("status") != "editorial_staging_only":
            errors.append(f"{ident}: status must remain editorial staging")
        for gate in GATES:
            if row.get(gate) is not False or source[gate] != "0":
                errors.append(f"{ident}: {gate} not yet verified")
        if row.get("production_ready") is not False or source["production_ready"] != "0":
            errors.append(f"{ident}: premature production release")
    return rows, errors

if __name__ == "__main__":
    rows, errors = audit()
    print(f"Structured editorial RPH: {len(rows)}; errors: {len(errors)}")
    for error in errors:
        print("BLOCK:", error)
    raise SystemExit(1 if errors else 0)
