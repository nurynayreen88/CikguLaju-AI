"""Check actual English standalone lesson source readiness without modifying it.

This is intentionally stricter than mere file existence: QA-pending drafts
must never be advertised as release-ready Web downloads.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "rph_standalone" / "english"


def inspect_standalone(year, lesson_no):
    if type(year) is not int or year not in (2, 3):
        raise ValueError("unsupported standalone year")
    if type(lesson_no) is not int or not 1 <= lesson_no <= 160:
        raise ValueError("invalid lesson")
    path = ROOT / ("year%d" % year) / ("lesson_%03d.md" % lesson_no)
    if not path.is_file():
        return {"exists": False, "ready": False, "reason": "source_missing"}
    source = path.read_text(encoding="utf-8")
    qa = re.search(r"(?im)^\*\*QA(?: status)?\s*:\*\*\s*(.+)$", source)
    status = qa.group(1).strip() if qa else ""
    # Explicitly reject pending, draft and negative release statements.
    blocked = bool(re.search(r"(?i)\b(pending|draft|do not publish|not ready|belum|menunggu)\b", status))
    ready = bool(re.search(r"(?i)\b(ready for release|release approved)\b", status)) and not blocked
    return {"exists": True, "ready": ready,
            "reason": "approved" if ready else "qa_not_release_approved",
            "qa_status": status}
