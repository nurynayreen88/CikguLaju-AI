"""Read-only integrity checks for English Year 4 standalone RPH assets.

Run from repository root:
    python scripts/validate_english_year4_standalone.py

No database access, no generated files, and no changes to source material.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rph_standalone" / "english" / "year4"
SPECIAL = {16, 32, 48, 64, 80, 96, 112, 128, 144, 160}
SP_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
SK_PATTERN = re.compile(r"^\d+\.\d+$")


def check() -> list[str]:
    errors: list[str] = []
    source = BASE / "sow_verified_160.csv"
    if not source.is_file():
        return [f"Missing SOW mapping: {source}"]
    with source.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 160:
        errors.append(f"Expected 160 SOW rows, found {len(rows)}")
    seen: set[int] = set()
    for row in rows:
        raw = row.get("lesson_no", "")
        try:
            number = int(raw)
        except (TypeError, ValueError):
            errors.append(f"Invalid lesson number: {raw!r}")
            continue
        if number in seen:
            errors.append(f"Duplicate lesson {number}")
        seen.add(number)
        if not 1 <= number <= 160:
            errors.append(f"Lesson number outside 1..160: {number}")
        lesson = BASE / f"lesson_{number:03d}.md"
        if not lesson.is_file():
            errors.append(f"Missing standalone RPH: {lesson.name}")
        else:
            text = lesson.read_text(encoding="utf-8")
            if not re.search(r"\bDRAFT\b|\bNOT READY FOR RELEASE\b|\bPENDING\b", text, re.IGNORECASE):
                errors.append(f"Lesson {number:03d}: release gate not explicit")
        # Structural checks do not imply pedagogical, audio, or Word/PDF approval.
        if lesson.is_file():
            if not re.search(r"\\*\\*Duration:\\*\\*\\s*60 minutes", text, re.IGNORECASE):
                errors.append(f"Lesson {number:03d}: expected 60-minute duration")
            if not re.search(r"\\bPBD\\b|\\bassessment\\b", text, re.IGNORECASE):
                errors.append(f"Lesson {number:03d}: PBD/assessment section missing")
            if not re.search(r"\\bTeacher:\\*\\*|\\*\\*Teacher\\*\\*:", text, re.IGNORECASE):
                errors.append(f"Lesson {number:03d}: teacher actions missing")
            if not re.search(r"\\bPupils:\\*\\*|\\*\\*Pupils\\*\\*:", text, re.IGNORECASE):
                errors.append(f"Lesson {number:03d}: pupil actions missing")
        sk = (row.get("main_cs") or "").strip()
        sp = (row.get("main_ls") or "").strip()
        if number in SPECIAL:
            if sk or sp:
                errors.append(f"Lesson {number:03d}: teacher-selected SK/SP must remain blank")
        elif not SK_PATTERN.fullmatch(sk) or not SP_PATTERN.fullmatch(sp):
            errors.append(f"Lesson {number:03d}: invalid SK/SP format: {sk!r}/{sp!r}")
        elif not sp.startswith(sk + "."):
            errors.append(f"Lesson {number:03d}: SK/SP mismatch: {sk}/{sp}")
    missing = set(range(1, 161)) - seen
    if missing:
        errors.append(f"Missing SOW rows: {sorted(missing)}")
    return errors


if __name__ == "__main__":
    problems = check()
    for problem in problems:
        print("FAIL:", problem)
    if problems:
        print(f"FAILED: {len(problems)} integrity issues")
        sys.exit(1)
    print("PASS: 160 SOW rows, 160 lesson files, draft gates and SK/SP structure")
