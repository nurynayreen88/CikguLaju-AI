"""Read-only audit of English Year 2/3 standalone Workbook references.

Run: python tools/audit_english_workbook_coverage.py
No changes to lesson content, databases, or rendering.
"""
from pathlib import Path
import json
import re
import csv
import argparse

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english"
PATTERN = re.compile(r"\b(?:Workbook|Activity Book)\b", re.IGNORECASE)
PAGE = re.compile(r"\b(?:Workbook|Activity Book)\s*(?:p\.|page)\s*\d+", re.IGNORECASE)
UNVERIFIED_NOTE = re.compile(r"(?im)^- \*\*Workbook:\*\* no verified page mapping\b")

def audit():
    report = {}
    for year in (2, 3):
        folder = ROOT / f"year{year}"
        missing_files, with_reference, without_reference, needs_page, unverified_notes = [], [], [], [], []
        for lesson in range(1, 161):
            file = folder / f"lesson_{lesson:03d}.md"
            if not file.is_file():
                missing_files.append(lesson)
                continue
            content = file.read_text(encoding="utf-8")
            if UNVERIFIED_NOTE.search(content):
                unverified_notes.append(lesson)
            if PATTERN.search(content):
                with_reference.append(lesson)
                if not PAGE.search(content):
                    needs_page.append(lesson)
            else:
                without_reference.append(lesson)
        report[f"year{year}"] = {
            "expected": 160,
            "missing_files": missing_files,
            "with_workbook_reference": with_reference,
            "without_workbook_reference": without_reference,
            "reference_without_page": needs_page,
            "unverified_mapping_note": unverified_notes,
        }
    return report

def validate_review_csv(csv_path):
    """Validate human-verified mapping rows without editing lesson plans."""
    issues = []
    verified = []
    seen = set()
    with Path(csv_path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"year", "lesson", "status", "verified_workbook_page",
                    "verified_activity", "source_evidence"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError("Missing required review CSV columns")
        for row_no, row in enumerate(reader, 2):
            try:
                year, lesson = int(row["year"]), int(row["lesson"])
            except (ValueError, TypeError):
                issues.append(f"Row {row_no}: invalid year or lesson")
                continue
            key = (year, lesson)
            if year not in (2, 3) or not 1 <= lesson <= 160 or key in seen:
                issues.append(f"Row {row_no}: out-of-range or duplicate lesson")
                continue
            seen.add(key)
            page = (row["verified_workbook_page"] or "").strip()
            activity = (row["verified_activity"] or "").strip()
            evidence = (row["source_evidence"] or "").strip()
            if not any((page, activity, evidence)):
                continue
            if not (page.isdigit() and int(page) > 0 and activity and evidence):
                issues.append(f"Row {row_no}: page, activity and source evidence all required")
                continue
            verified.append({"year": year, "lesson": lesson,
                             "page": int(page), "activity": activity,
                             "evidence": evidence})
    return verified, issues


def review_rows(report):
    """Generate a review queue, not invented Workbook mappings."""
    for year in (2, 3):
        data = report[f"year{year}"]
        missing = set(data["missing_files"])
        referenced = set(data["with_workbook_reference"])
        page_missing = set(data["reference_without_page"])
        unverified = set(data["unverified_mapping_note"])
        for lesson in range(1, 161):
            status = ("missing_file" if lesson in missing else
                      "unverified_mapping_note" if lesson in unverified else
                      "reference_missing_page" if lesson in page_missing else
                      "reference_present" if lesson in referenced else
                      "needs_source_verification")
            yield {"year": year, "lesson": lesson, "status": status,
                   "verified_workbook_page": "", "verified_activity": "",
                   "source_evidence": ""}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-csv", help="Write a review queue CSV; never edits RPH files")
    parser.add_argument("--validate-csv", help="Validate completed review CSV without editing RPH files")
    args = parser.parse_args()
    report = audit()
    if args.validate_csv:
        verified, issues = validate_review_csv(args.validate_csv)
        print(f"Verified mapping rows: {len(verified)}; issues: {len(issues)}")
        for issue in issues:
            print(issue)
        if issues:
            raise SystemExit(1)
    for year in (2, 3):
        item = report[f"year{year}"]
        print(f"Year {year}: {len(item['with_workbook_reference'])} references; "
              f"{len(item['without_workbook_reference'])} without; "
              f"{len(item['missing_files'])} missing files; "
              f"{len(item['reference_without_page'])} references missing page; "
              f"{len(item['unverified_mapping_note'])} explicit unverified notes")
    if args.review_csv:
        destination = Path(args.review_csv)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8-sig") as output:
            writer = csv.DictWriter(output, fieldnames=[
                "year", "lesson", "status", "verified_workbook_page",
                "verified_activity", "source_evidence"])
            writer.writeheader()
            writer.writerows(review_rows(report))
        print(f"Review queue: {destination}")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
