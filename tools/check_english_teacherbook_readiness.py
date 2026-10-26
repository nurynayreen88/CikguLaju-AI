"""Audit English Years 1–3 without treating file coverage as Teacher's Book approval.

Run: python tools/check_english_teacherbook_readiness.py
Exit code 0: all 480 lesson files exist (not a content approval).
Exit code 1: missing files. JSON report includes draft counts.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rph_standalone" / "english"
OUT = ROOT / "reports" / "english_teacherbook_readiness.json"
DRAFT = re.compile(r"pending|unverified|not verified|preliminary|provisional|draft|proposed|SOW_MAPPED_ONLY", re.I)
TB_MARK = re.compile(r"^\*\*QA status:\*\*\s*TEACHER_BOOK_VERIFIED\b", re.I | re.M)

def audit():
    report = {"scope": "English Years 1-3, Lessons 1-160", "disclaimer": "Static checks do not verify Teacher's Book fidelity", "years": {}}
    for year in (1, 2, 3):
        data = {"present": 0, "missing": [], "explicit_draft": [], "no_teacherbook_attestation": [], "lacks_activity_1": [], "lacks_pbd": []}
        for lesson in range(1, 161):
            path = BASE / f"year{year}" / f"lesson_{lesson:03d}.md"
            if not path.is_file():
                data["missing"].append(lesson)
                continue
            data["present"] += 1
            body = path.read_text(encoding="utf-8")
            if DRAFT.search(body):
                data["explicit_draft"].append(lesson)
            if not TB_MARK.search(body):
                data["no_teacherbook_attestation"].append(lesson)
            if not re.search(r"^##\s+Activity\s*1\b", body, re.I | re.M):
                data["lacks_activity_1"].append(lesson)
            if not re.search(r"Assessment\s*/\s*PBD", body, re.I):
                data["lacks_pbd"].append(lesson)
        report["years"][str(year)] = data
        print(f"Year {year}: {data['present']}/160 files; {len(data['explicit_draft'])} explicit drafts; {len(data['no_teacherbook_attestation'])} lacking TB attestation")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return all(report["years"][str(y)]["present"] == 160 for y in (1, 2, 3))

if __name__ == "__main__":
    raise SystemExit(0 if audit() else 1)
