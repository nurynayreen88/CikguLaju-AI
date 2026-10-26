"""Audit English Year 3 coverage separately from curriculum readiness.

Run: python tools/audit_english_y3_coverage.py
Exit 1 if lessons are missing, duplicated or malformed. Drafts are reported,
not counted as verified, and must never be published as completed RPH.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "rph_standalone" / "english" / "year3"
EXPECTED = set(range(1, 161))
SKSP = re.compile(r"\*\*(?:Main|Complementary) SK/SP:\*\*\s*\d+\.\d+\s*/\s*\d+\.\d+\.\d+", re.I)
UNVERIFIED = re.compile(r"UNVERIFIED|Pending (?:official|source|SOW)|Teacher.s Book.*pending|Teacher.s Book.*verification|QA:.*draft|QA:.*preliminary", re.I)


def audit():
    found = {}
    duplicates = []
    for path in sorted(FOLDER.glob("lesson_*.md")):
        match = re.fullmatch(r"lesson_(\d{3})\.md", path.name)
        if not match:
            continue
        n = int(match.group(1))
        if n in found:
            duplicates.append(n)
        found[n] = path
    missing = sorted(EXPECTED - set(found))
    extra = sorted(set(found) - EXPECTED)
    malformed, drafts, ready = [], [], []
    for number, path in sorted(found.items()):
        body = path.read_text(encoding="utf-8")
        if (not re.search(r"\bLesson\s*0*" + str(number) + r"\b", body, re.I)
                or "Assessment / PBD" not in body or "Closure" not in body):
            malformed.append(number)
        elif UNVERIFIED.search(body) or len(SKSP.findall(body)) < 2:
            drafts.append(number)
        else:
            ready.append(number)
    print(f"Coverage: {len(set(found) & EXPECTED)}/160")
    print(f"Candidate files (not independently verified): {len(ready)}")
    print(f"Unverified drafts: {len(drafts)}")
    print("Missing:", missing)
    print("Unexpected:", extra)
    print("Duplicates:", duplicates)
    print("Malformed:", malformed)
    return not (missing or extra or duplicates or malformed)


if __name__ == "__main__":
    raise SystemExit(0 if audit() else 1)
