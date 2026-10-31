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

def audit():
    report = {}
    for year in (2, 3):
        folder = ROOT / f"year{year}"
        missing_files, with_reference, without_reference, needs_page = [], [], [], []
        for lesson in range(1, 161):
            file = folder / f"lesson_{lesson:03d}.md"
            if not file.is_file():
                missing_files.append(lesson)
                continue
            content = file.read_text(encoding="utf-8")
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
        }
    return report

def review_rows(report):
    """Generate a review queue, not invented Workbook mappings."""
    for year in (2, 3):
        data = report[f"year{year}"]
        missing = set(data["missing_files"])
        referenced = set(data["with_workbook_reference"])
        page_missing = set(data["reference_without_page"])
        for lesson in range(1, 161):
            status = ("missing_file" if lesson in missing else
                      "reference_missing_page" if lesson in page_missing else
                      "reference_present" if lesson in referenced else
                      "needs_source_verification")
            yield {"year": year, "lesson": lesson, "status": status,
                   "verified_workbook_page": "", "verified_activity": "",
                   "source_evidence": ""}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-csv", help="Write a review queue CSV; never edits RPH files")
    args = parser.parse_args()
    report = audit()
    for year in (2, 3):
        item = report[f"year{year}"]
        print(f"Year {year}: {len(item['with_workbook_reference'])} references; "
              f"{len(item['without_workbook_reference'])} without; "
              f"{len(item['missing_files'])} missing files; "
              f"{len(item['reference_without_page'])} references missing page")
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
