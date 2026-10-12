"""PJPK v26.18 isolated staging smoke test. Does not import app.py or modify the production DB."""
from pathlib import Path
import sqlite3
import sys
import pjpk_t3_safe_preview_adapter as adapter

base = Path(__file__).resolve().parent
db = base / "pjpk_candidate.db"
if not db.is_file():
    raise SystemExit("Candidate DB missing. Run: python rebuild_pjpk_candidate.py")
with sqlite3.connect(db) as con:
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "DB integrity failed"
total = 0
for subject, expected in (("PJ", 33), ("PK", 10)):
    options = adapter.list_options(db, subject)
    assert len(options) == expected, (subject, len(options), expected)
    for option in options:
        preview = adapter.generate_preview(db, subject, option["key"])
        assert preview["production_allowed"] is False
        assert preview["status"] == "PREVIEW_ONLY"
        assert preview["sp"] and len(preview["phases"]) == 5
        try:
            adapter.generate_preview(db, subject, option["key"], mode="production")
        except adapter.PreviewBlocked:
            pass
        else:
            raise AssertionError("Production gate unexpectedly open: " + str(option))
        total += 1
print("PASS:", total, "editorial previews; production blocked for all.")
