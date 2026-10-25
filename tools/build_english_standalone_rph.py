"""Read-only source-locked English standalone RPH builder.

Produces draft records only for lessons with verified Teacher's Book guidance.
Never modifies existing curriculum databases or claims unverified lessons ready.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "english_y1y2_sow_master_320.json"
GUIDES = sorted((ROOT / "data").glob("teacher_book_guidance_y1_batch*.json"))
ACCEPTED = {"VERIFIED_TB_SCAN", "SOURCE_ALIGNED_GUIDANCE", "VERIFIED_MAPPING_GUIDANCE"}

def activity_quality(guide):
    """Report missing components without fabricating Teacher's Book instructions."""
    required = ("warm_up", "student_book_procedure", "checking_feedback", "ending_lesson")
    missing = [field for field in required if not guide.get(field)]
    vague = [field for field in ("student_book_procedure", "workbook_procedure")
             if any(s in guide.get(field, "").lower() for s in
                    ("verified wb activity linked", "textbook reading/task", "work through sb"))]
    return {"missing_phases": missing, "needs_specificity_review": vague,
            "ready_for_teacher_review": not missing and not vague
            and guide.get("verification_status") == "VERIFIED_TB_SCAN"}

def build():
    sow = json.loads(SOURCE.read_text(encoding="utf-8"))
    lessons = {(year, int(row[0])): row for year, rows in sow.items() for row in rows}
    records = []
    seen = set()
    for file in GUIDES:
        for guide in json.loads(file.read_text(encoding="utf-8")).get("guidance", []):
            key = (guide["year"], int(guide["lesson_no"]))
            if key in seen:
                raise ValueError(f"Duplicate lesson: {key}")
            seen.add(key)
            if guide.get("verification_status") not in ACCEPTED:
                continue
            if key not in lessons:
                raise ValueError(f"Missing SOW lesson: {key}")
            row = lessons[key]
            if str(row[2]).casefold().strip() != str(guide["unit"]).casefold().strip():
                raise ValueError(f"Unit mismatch: {key}")
            records.append({
                "year": key[0], "lesson_no": key[1], "lesson_name": row[1],
                "unit": row[2], "main_sk": row[3], "main_sp": row[4],
                "complementary_sk": row[5], "complementary_sp": row[6],
                "objective_source": guide.get("aims", ""),
                "success_evidence": guide.get("checking_feedback", ""),
                "activities": [
                    {"phase": phase, "procedure": guide[field], "source_field": field}
                    for phase, field in (
                        ("Set Induction", "warm_up"),
                        ("Activity 1", "student_book_procedure"),
                        ("Activity 2", "workbook_procedure"),
                        ("Assessment", "checking_feedback"),
                        ("Closure", "ending_lesson")
                    ) if guide.get(field)
                ],
                "student_book_pages": guide.get("sb_pages", []),
                "teacher_book_pages": guide.get("tb_pages", []),
                "audio": guide.get("audio_procedure", ""),
                "activity_quality": activity_quality(guide),
                "source": guide["verification_status"],
                "requires_teacher_book_confirmation": guide["verification_status"] != "VERIFIED_TB_SCAN",
                "status": "DRAFT_PENDING_ACTIVITY_AND_A4_QA"
            })
    return sorted(records, key=lambda r: (r["year"], r["lesson_no"]))

if __name__ == "__main__":
    output = ROOT / "output" / "english_standalone_verified_drafts.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    records = build()
    output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "total": len(records),
        "verified_tb_scan": sum(r["source"] == "VERIFIED_TB_SCAN" for r in records),
        "mapped_guidance": sum(r["source"] != "VERIFIED_TB_SCAN" for r in records),
        "ready_for_teacher_review": sum(r["activity_quality"]["ready_for_teacher_review"] for r in records),
        "missing_phases": sum(bool(r["activity_quality"]["missing_phases"]) for r in records),
        "specificity_review": sum(bool(r["activity_quality"]["needs_specificity_review"]) for r in records),
    }
    report = ROOT / "output" / "english_standalone_activity_audit.json"
    report.write_text(json.dumps({"summary": summary, "lessons": [
        {"year": r["year"], "lesson_no": r["lesson_no"], "unit": r["unit"],
         "source": r["source"], **r["activity_quality"]} for r in records
    ]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    print(f"Drafts: {output}; audit: {report}")
