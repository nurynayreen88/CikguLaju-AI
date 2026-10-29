#!/usr/bin/env python3
"""Read-only release-gate audit for English Year 3 standalone RPH."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
EXPECTED = set(range(1, 161))
errors = []
warnings = []
files = sorted(ROOT.glob("lesson_[0-9][0-9][0-9].md"))
actual = {int(p.stem.split("_")[1]) for p in files}
for n in sorted(EXPECTED - actual):
    errors.append(f"Missing Lesson {n:03d}")
for n in sorted(actual - EXPECTED):
    errors.append(f"Unexpected Lesson {n:03d}")
for path in files:
    n = int(path.stem.split("_")[1])
    text = path.read_text(encoding="utf-8")
    if not re.search(r"\*\*Duration:\*\*\s*60 minutes", text):
        errors.append(f"{n:03d}: duration is not 60 minutes")
    for field in ("Unit", "Main SK/SP", "Complementary SK/SP", "References", "QA"):
        if not re.search(rf"\*\*{re.escape(field)}:\*\*\s*\S", text):
            errors.append(f"{n:03d}: missing {field}")
    headings = re.findall(r"^##\s+(.+)$", text, flags=re.MULTILINE)
    expected = ("Set Induction", "Activity 1", "Activity 2", "PBD", "Closure")
    if not any("Set Induction" in h for h in headings):
        errors.append(f"{n:03d}: missing Set Induction")
    for section in ("Activity 1", "Activity 2", "Closure"):
        if not any(section in h for h in headings):
            errors.append(f"{n:03d}: missing {section}")
    if not any("PBD" in h or "Assessment" in h for h in headings):
        errors.append(f"{n:03d}: missing PBD section")
    minutes = [int(x) for x in re.findall(r"^##\s+[^\n]*\((\d+) minutes\)", text, flags=re.MULTILINE)]
    if len(minutes) != 5 or sum(minutes) != 60:
        errors.append(f"{n:03d}: section durations {minutes} do not total five sections / 60 minutes")
    if "NOT READY FOR RELEASE" in text:
        warnings.append(f"{n:03d}: release gate remains blocked")
    if "Teacher's Book" not in text:
        warnings.append(f"{n:03d}: Teacher's Book reference missing")
print(f"English Year 3: {len(files)}/160 files | {len(errors)} structural errors | {len(warnings)} release warnings")
for issue in errors:
    print("ERROR:", issue)
for issue in warnings:
    print("WARN:", issue)
if errors:
    sys.exit(1)
if warnings:
    print("Structural checks passed; release NOT approved until source verification and Word/PDF output tests.")
    sys.exit(2)
print("Structural checks passed. Manual source and output verification still required.")
