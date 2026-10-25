"""Audit English Year 3 RPH coverage and SOW mapping without fabricating data.

Run: python tools/audit_english_y3_coverage.py
Exit 0 when all 160 standalone lessons exist and have SK/SP metadata.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "rph_standalone" / "english" / "year3"
EXPECTED = set(range(1, 161))


def audit():
    found = {}
    for path in sorted(FOLDER.glob("lesson_*.md")):
        match = re.fullmatch(r"lesson_(\d{3})\.md", path.name)
        if match:
            found[int(match.group(1))] = path
    missing = sorted(EXPECTED - set(found))
    extra = sorted(set(found) - EXPECTED)
    malformed = []
    for number, path in found.items():
        text = path.read_text(encoding="utf-8")
        if (f"Lesson {number}" not in text or
                not re.search(r"\*\*Main SK/SP:\*\*\s*\d+\.\d+\s*/\s*\d+\.\d+\.\d+", text) or
                not re.search(r"\*\*Complementary SK/SP:\*\*\s*\d+\.\d+\s*/\s*\d+\.\d+\.\d+", text) or
                "Assessment / PBD" not in text or "Closure" not in text):
            malformed.append(number)
    print(f"Year 3 RPH: {len(found & {}) if False else len(found)}/160")
    print("Missing:", missing)
    print("Unexpected:", extra)
    print("Malformed:", sorted(malformed))
    return not (missing or extra or malformed)


if __name__ == "__main__":
    raise SystemExit(0 if audit() else 1)
