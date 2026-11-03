"""Read-only audit of all 160 Year 4 standalone RPH Markdown files.

This is a gate, not a claim of SOW, book, or audio verification.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone/english/year4"


def audit():
    findings = []
    for n in range(1, 161):
        path = ROOT / f"lesson_{n:03d}.md"
        if not path.is_file():
            findings.append({"lesson": n, "issue": "MISSING_FILE"})
            continue
        text = path.read_text(encoding="utf-8")
        checks = {
            "heading": bool(re.search(r"(?im)^# .*lesson\s*0*" + str(n) + r"\b", text)),
            "induction": bool(re.search(r"(?im)^##\s*set\s*induction", text)),
            "activity": bool(re.search(r"(?im)^##\s*activity\s*\d", text)),
            "closure": bool(re.search(r"(?im)^##\s*closure", text)),
            "assessment": bool(re.search(r"(?im)(?:\bPBD\b|assessment)", text)),
            "teacher_action": bool(re.search(r"(?i)(?:\*\*Teacher(?: action)?:\*\*)", text)),
            "pupil_action": bool(re.search(r"(?i)(?:\*\*Pupils?:\*\*|\*\*Pupil action:\*\*)", text)),
        }
        for label, passed in checks.items():
            if not passed:
                findings.append({"lesson": n, "issue": "MISSING_" + label.upper()})
        if re.search(r"(?im)^\*\*Status:\*\*.*\bDRAFT\b", text):
            findings.append({"lesson": n, "issue": "DRAFT_STATUS"})
        if re.search(r"(?im)^\*\*(?:QA status|Internal review):", text):
            findings.append({"lesson": n, "issue": "INTERNAL_QA_NOTE"})
        if "Teacher-selected DSKP SP" in text:
            findings.append({"lesson": n, "issue": "TEACHER_SELECTED_SP_REQUIRES_CONTEXT"})
    return findings


if __name__ == "__main__":
    results = audit()
    print(json.dumps({"total_lessons": 160, "findings": results}, ensure_ascii=False, indent=2))
