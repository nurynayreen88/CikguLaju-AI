"""Read-only release-readiness audit for English standalone Year 1–3.

Usage: python -m web.audit_english_standalone
Counts files and QA markers without printing lesson text. No file mutations.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english"
QA_LINE = re.compile(r"(?im)^\*\*(QA(?: status)?):\*\*\s*(.*)$")


def audit(root=ROOT):
    report = {}
    for year in (1, 2, 3):
        directory = Path(root) / f"year{year}"
        counts = {"files": 0, "release_ready": 0, "not_ready": 0,
                  "draft_or_pending": 0, "missing_qa": 0, "read_errors": 0}
        for lesson_no in range(1, 161):
            path = directory / f"lesson_{lesson_no:03d}.md"
            if not path.is_file():
                continue
            counts["files"] += 1
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                counts["read_errors"] += 1
                continue
            matches = QA_LINE.findall(content)
            if len(matches) != 1:
                counts["missing_qa"] += 1
            else:
                status = matches[0][1].strip().upper()
                if status == "READY FOR RELEASE":
                    counts["release_ready"] += 1
                elif "NOT READY FOR RELEASE" in status:
                    counts["not_ready"] += 1
                else:
                    counts["draft_or_pending"] += 1
        counts["missing_lessons"] = 160 - counts["files"]
        report[f"year{year}"] = counts
    return report


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
