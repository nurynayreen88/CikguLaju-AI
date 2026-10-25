"""Merge reviewed-source drafts with clearly labelled proposed phases.

Never overwrites source activities. Output remains pending pedagogical QA.
"""
import json
from pathlib import Path
from build_english_standalone_rph import build, ROOT

def merge_records(records):
    proposals = {}
    for path in sorted((ROOT / "data").glob("english_standalone_activity_proposals_y1_*.json")):
        for item in json.loads(path.read_text(encoding="utf-8")).get("proposals", []):
            key = (item.get("year", "Tahun 1"), int(item["lesson_no"]))
            if key in proposals:
                raise ValueError(f"Duplicate proposal {key}")
            if item.get("provenance") != "TEACHER_DEVELOPED_PROPOSAL_NOT_TB":
                raise ValueError(f"Missing provenance {key}")
            proposals[key] = item
    count = 0
    conflicts = []
    matched = set()
    for record in records:
        key = (record["year"], record["lesson_no"])
        existing = {a["phase"] for a in record["activities"]}
        proposal = proposals.get(key, {})
        if proposal:
            matched.add(key)
        for phase, field in (("Set Induction", "warm_up"), ("Closure", "ending_lesson")):
            if phase in existing and proposal.get(field):
                conflicts.append({"year": key[0], "lesson_no": key[1], "phase": phase})
            if phase not in existing and proposal.get(field):
                record["activities"].append({
                    "phase": phase, "procedure": proposal[field],
                    "provenance": "TEACHER_DEVELOPED_PROPOSAL_NOT_TB",
                    "review_status": "PENDING_PEDAGOGICAL_REVIEW"
                })
                count += 1
        record["activities"].sort(key=lambda a: ["Set Induction", "Activity 1", "Activity 2", "Assessment", "Closure"].index(a["phase"]))
        record["activity_quality"]["pending_proposal_review"] = any(a.get("review_status") == "PENDING_PEDAGOGICAL_REVIEW" for a in record["activities"])
        if record["activity_quality"]["pending_proposal_review"]:
            record["activity_quality"]["ready_for_teacher_review"] = False
        record["activity_quality"]["missing_phases"] = [
            field for phase, field in (("Set Induction", "warm_up"), ("Activity 1", "student_book_procedure"),
                                       ("Assessment", "checking_feedback"), ("Closure", "ending_lesson"))
            if phase not in {a["phase"] for a in record["activities"]}
        ]
    return records, {"proposed_phases_added": count,
                     "unmatched_proposals": sorted([list(k) for k in proposals if k not in matched]),
                     "conflicting_proposals": conflicts}


def main():
    records, stats = merge_records(build())
    output = ROOT / "output" / "english_standalone_supplemented_drafts.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"lessons": len(records), **stats, "output": str(output)}))

if __name__ == "__main__":
    main()
