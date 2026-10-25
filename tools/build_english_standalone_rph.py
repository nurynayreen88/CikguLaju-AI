"""Read-only source-locked English standalone RPH builder.

Produces draft records only for lessons with verified Teacher's Book guidance.
Never modifies existing curriculum databases or claims unverified lessons ready.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "english_y1y2_sow_master_320.json"
GUIDES = sorted((ROOT / "data").glob("teacher_book_guidance_y1_batch*.json"))

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
            if guide.get("verification_status") != "VERIFIED_TB_SCAN":
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
                "objective_source": guide["aims"],
                "success_evidence": guide["checking_feedback"],
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
                "source": "VERIFIED_TB_SCAN",
                "status": "DRAFT_PENDING_ACTIVITY_AND_A4_QA"
            })
    return sorted(records, key=lambda r: (r["year"], r["lesson_no"]))

if __name__ == "__main__":
    output = ROOT / "output" / "english_standalone_verified_drafts.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    records = build()
    output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Drafts: {len(records)}; output: {output}")
