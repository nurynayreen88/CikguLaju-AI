"""Audit 480 standalone English RPH files; distinguish coverage from Teacher's Book verification.

Run at repository root: python tools/audit_english_y1_y2_y3.py
Writes reports/english_y1_y2_y3_audit.json and prints counts.
Never modifies lesson files. Exits 1 unless all 480 are verified.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "rph_standalone" / "english"
OUT = ROOT / "reports" / "english_y1_y2_y3_audit.json"
UNVERIFIED = re.compile(
    r"not verified|unverified|pending|preliminary|provisional|"
    r"SOW_MAPPED_ONLY|teacher-developed|teacher.s book.*(?:verify|review)|"
    r"\bDRAFT\b|proposed", re.I
)
SKSP = re.compile(r"\*\*(?:Main|Complementary) SK/SP[^\n]*?:\*\*\s*\d+\.\d+\s*/\s*\d+\.\d+\.\d+", re.I)
ACTIVITY = re.compile(r"^##\s+Activity\s*1\b", re.I | re.M)
TEACHER_BOOK_EVIDENCE = re.compile(r"\*\*(?:Teacher.s Book (?:page|reference|steps)|TB page):\*\*\s*(?!not verified|pending|unknown)\S+", re.I)

def run():
    result = {"scope": "English Years 1-3, Lessons 1-160", "method": "Static file audit; Teacher's Book fidelity still requires human/source comparison", "years": {}}
    for year in (1, 2, 3):
        folder = BASE / f"year{year}"
        counts = {"present": 0, "missing": [], "unverified": [], "missing_sksp": [], "missing_activity": [], "missing_tb_evidence": [], "candidate_only": []}
        for n in range(1, 161):
            p = folder / f"lesson_{n:03d}.md"
            if not p.is_file():
                counts["missing"].append(n)
                continue
            counts["present"] += 1
            body = p.read_text(encoding="utf-8")
            if UNVERIFIED.search(body):
                counts["unverified"].append(n)
            if len(SKSP.findall(body)) < 2:
                counts["missing_sksp"].append(n)
            if not ACTIVITY.search(body):
                counts["missing_activity"].append(n)
            if not TEACHER_BOOK_EVIDENCE.search(body):
                counts["missing_tb_evidence"].append(n)
            if n not in counts["unverified"] and n not in counts["missing_sksp"] and n not in counts["missing_activity"] and n not in counts["missing_tb_evidence"]:
                counts["candidate_only"].append(n)
        counts["verified"] = 0  # Static inspection alone cannot certify fidelity.
        result["years"][str(year)] = counts
        print(f"Year {year}: {counts['present']}/160 present; {len(counts['unverified'])} explicitly unverified; {len(counts['missing_tb_evidence'])} without explicit TB evidence; 0 source-verified by this audit")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return all(x["present"] == 160 and not x["unverified"] and not x["missing_sksp"] and not x["missing_activity"] and not x["missing_tb_evidence"] for x in result["years"].values()) and False

if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)
