#!/usr/bin/env python3
"""Offline audit/export of existing standalone English RPH drafts.

This deliberately reuses the current generator's structured lesson output data,
without changing Telegram routes, database contents or deployment behaviour.
Usage: python tools/export_standalone_english_rph.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/english_standalone_rph_y1_structured_batch01.json"
OUTPUT = ROOT / "data/english_standalone_rph_y1_generator_audit_batch01.json"
REQUIRED = ("Set induction", "Activity 1", "Assessment", "Closure")

def export(source=SOURCE, output=OUTPUT):
    records = json.loads(source.read_text(encoding="utf-8"))["records"]
    results = []
    for record in records:
        stages = record["teaching_sequence"]
        present = {stage["stage"] for stage in stages}
        missing = [name for name in REQUIRED if name not in present]
        issues = list(record["quality"]["flags"])
        if missing:
            issues.append("Missing required stages: " + ", ".join(missing))
        if not record["standards"]["main"]["ls"]:
            issues.append("Missing main learning standard")
        if not record["references"]["student_book_pages"]:
            issues.append("Missing Student's Book reference")
        results.append({
            "lesson_id": record["id"],
            "lesson_no": record["lesson_no"],
            "unit": record["unit"],
            "lesson_label": record["lesson_label"],
            "generator_input": {
                "year": record["year"],
                "lesson_no": record["lesson_no"],
                "standards": record["standards"],
                "teaching_sequence": stages,
                "references": record["references"],
            },
            "audit_issues": sorted(set(issues)),
            "approval_status": "needs_pedagogical_review",
        })
    payload = {
        "purpose": "Audit-ready lesson-by-lesson structured generator inputs; not approved RPH PDFs",
        "count": len(results),
        "lessons": results,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload

if __name__ == "__main__":
    result = export()
    print("Exported", result["count"], "lesson records to", OUTPUT)
