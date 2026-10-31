"""Read-only audit of English Year 2/3 standalone Workbook references.

Run: python tools/audit_english_workbook_coverage.py
No changes to lesson content, databases, or rendering.
"""
from pathlib import Path
import json
import re

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

if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
