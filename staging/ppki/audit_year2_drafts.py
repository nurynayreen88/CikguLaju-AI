"""Read-only preflight for the new PPKI Year 2 lesson banks.

Do not route these draft records to production. The existing Pengurusan
Kehidupan renderer expects a single SP string and a subject-specific
heading; these new banks intentionally support multiple standards.
"""
import json
from pathlib import Path
from collections import defaultdict

BANKS = (
    "bahasa_melayu_tahun2_tema1_draft.json",
    "bahasa_melayu_tahun2_tema2_6_draft.json",
    "english_year2_all_units_draft.json",
    "matematik_tahun2_all_units_draft.json",
    "pendidikan_islam_tahun2_draft.json",
    "pendidikan_jasmani_tahun2_draft.json",
    "pendidikan_moral_tahun2_draft.json",
    "pendidikan_seni_kreatif_tahun2_draft.json",
)
REQUIRED = ("title", "textbook_page", "objective", "success_criterion",
            "materials", "induction", "guided", "practice", "support",
            "assessment", "closure", "reflection_criterion")


def audit(root=Path(__file__).parent):
    grouped = defaultdict(list)
    for name in BANKS:
        doc = json.loads((root / name).read_text(encoding="utf-8"))
        if doc["year"] != 2 or doc["status"] != "DALAM_SEMAKAN":
            raise ValueError(f"Unexpected draft identity: {name}")
        for lesson in doc["lessons"]:
            grouped[doc["subject_id"]].append(lesson)
    report = {}
    for subject, lessons in grouped.items():
        problems = []
        expected = [f"{i:03d}" for i in range(1, len(lessons) + 1)]
        if [l["pdp"] for l in lessons] != expected:
            problems.append("Non-contiguous sequence")
        if len({l["title"] for l in lessons}) != len(lessons):
            problems.append("Duplicate title")
        for lesson in lessons:
            prefix = lesson["pdp"]
            for field in REQUIRED:
                if not str(lesson.get(field) or "").strip():
                    problems.append(f"{prefix}: missing {field}")
            if not lesson.get("sp"):
                problems.append(f"{prefix}: missing SP")
            if lesson.get("status") == "KONFLIK_PENOMBORAN_DSKP":
                problems.append(f"{prefix}: unresolved source numbering")
            if lesson["success_criterion"] != lesson["reflection_criterion"]:
                problems.append(f"{prefix}: reflection mismatch")
        report[subject] = {
            "lessons": len(lessons), "issues": problems,
            "release_ready": False,
            "release_blockers": [
                "Full SK and SP wording not yet independently verified for every lesson",
                "Textbook/activity-book alignment and annual timing need review",
                "Native Word/PDF output and RPT A/B dates not tested",
            ],
        }
    return report


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
