"""PJPK v26.18 isolated release preflight; never imports the Flask app or writes to the main DB."""
from pathlib import Path
import ast
import sqlite3
import pjpk_t3_safe_preview_adapter as adapter

base = Path(__file__).resolve().parent
for name in ("app.py", "pjpk_t3_safe_preview_adapter.py", "rebuild_pjpk_candidate.py"):
    ast.parse((base / name).read_text(encoding="utf-8-sig"), filename=name)
db = base / "pjpk_candidate.db"
if not db.is_file():
    raise SystemExit("Candidate DB missing. First run: python rebuild_pjpk_candidate.py")
with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as con:
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("SELECT COUNT(*) FROM pjpk_t3_43_editorial_gate WHERE production_status='BLOCKED' AND teacher_review='PENDING_TEACHER_REVIEW'").fetchone()[0] == 43
total = 0
for subject, count in (("PJ", 33), ("PK", 10)):
    options = adapter.list_options(db, subject)
    assert len(options) == count, (subject, len(options))
    for option in options:
        key = option["key"]
        result = adapter.generate_preview(db, subject, key)
        assert result["status"] == "PREVIEW_ONLY"
        assert result["production_allowed"] is False
        assert result["teacher_review"] == "PENDING_TEACHER_REVIEW"
        assert result["sp"] and len(result["phases"]) == 5
        try:
            adapter.generate_preview(db, subject, key, mode="production")
        except adapter.PreviewBlocked:
            pass
        else:
            raise AssertionError(f"Production unexpectedly allowed: {subject} {key}")
        total += 1
assert total == 43
print("PASS: syntax, read-only SQLite integrity, 43 editorial gates, 43 previews, 43 production blocks")
