"""Read-only English Year 4 release audit. Never marks a lesson READY.

Run: python rph_standalone/english/year4/audit_standalone_release.py
Optional: --json report.json --csv report.csv
"""
import argparse
import csv
import json
import re
from pathlib import Path

from standalone_renderer_adapter import adapt_year4_standalone, year4_release_blockers

ROOT = Path(__file__).resolve().parent
TEACHER_SELECTED = {80, 96, 112, 128, 144, 160}
AUDIO_DISC_UNVERIFIED = {139, 145, 147}
SOURCE_AUDIO_REVIEW = {123, 135, 139, 145, 147, 150, 152, 155, 156}


def audit(root=ROOT):
    records = []
    for number in range(1, 161):
        path = root / f"lesson_{number:03d}.md"
        if not path.exists():
            records.append({"lesson": number, "file": str(path.name),
                            "blockers": ["missing_lesson_file"], "approval": "PENDING"})
            continue
        source = path.read_text(encoding="utf-8")
        adapted = adapt_year4_standalone(source)
        blockers = year4_release_blockers(source)
        required = ("TOPIC", "MAIN LEARNING STANDARD", "COMPLEMENTARY LEARNING STANDARD",
                    "SET INDUCTION", "MAIN ACTIVITIES", "CLOSURE", "ASSESSMENT")
        for label in required:
            match = re.search(
                r"(?ms)^" + re.escape(label) +
                r":\\n(.*?)(?=^[A-Z][A-Z ]+:\\n|\\Z)", adapted
            )
            code = label.lower().replace(" ", "_")
            if not match:
                blockers.append("renderer_missing_" + code)
            elif not match.group(1).strip():
                blockers.append("renderer_empty_" + code)
        for label in ("Activity 1", "Activity 2"):
            if label not in adapted:
                blockers.append("renderer_missing_" + label.lower().replace(" ", "_"))
        if number in TEACHER_SELECTED and "teacher_selected_main_sp" not in blockers:
            blockers.append("review_teacher_selected_main_sp")
        if number in TEACHER_SELECTED and "teacher_selected_complementary_sp" not in blockers:
            blockers.append("review_teacher_selected_complementary_sp")
        if number in AUDIO_DISC_UNVERIFIED and "audio_disc_unverified" not in blockers:
            blockers.append("review_audio_disc_mapping")
        if number in SOURCE_AUDIO_REVIEW:
            blockers.append("manual_source_audio_review")
        # Manual approval is a separate gate for EVERY lesson, including zero-blocker ones.
        records.append({"lesson": number, "file": path.name,
                        "blockers": sorted(set(blockers)), "approval": "PENDING"})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()
    records = audit()
    summary = {"lessons_expected": 160,
               "files_found": sum("missing_lesson_file" not in r["blockers"] for r in records),
               "lessons_with_automated_or_known_gates": sum(bool(r["blockers"]) for r in records),
               "manual_approvals_verified": 0,
               "release_ready": False,
               "records": records}
    if args.json:
        args.json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=["lesson", "file", "blockers", "approval"])
            writer.writeheader()
            for record in records:
                writer.writerow({**record, "blockers": ";".join(record["blockers"])})
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
