"""Read-only audit of active original PI RPT source; never reads 696 archive."""
import re
import sqlite3
from tools.bm_native_v26_navigation_audit import database


def main():
    temp, path = database()
    try:
        with sqlite3.connect(path.resolve().as_uri()+"?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT id, year_label, sequence_no, activity_note FROM rpt_entries WHERE id = 1275 AND subject = 'Pendidikan Islam' AND verified=1").fetchone()
            assert row is not None, "Active PI sample row 1275 missing"
            print("ACTIVE RPT 1275 YEAR", row["year_label"], "PdP", row["sequence_no"])
            note = str(row["activity_note"] or "")
            print("SOURCE_ACTIVITY_NOTE_REPR", repr(note))
            print("SOURCE_NOTE_LENGTH", len(note))
            orphan = re.compile(r"(?m)(?<=[^\\s])\\s+2\\.(?=\\s*$)")
            print("SAMPLE_TRAILING_TWO_MATCH", bool(orphan.search(note)))
            matches = []
            for entry in db.execute("SELECT id,activity_note FROM rpt_entries WHERE subject='Pendidikan Islam' AND verified=1"):
                activity = str(entry["activity_note"] or "")
                if orphan.search(activity):
                    matches.append(entry["id"])
            print("ACTIVE_PI_TRAILING_2_ROWS", len(matches), "IDS", matches[:20])
    finally:
        temp.cleanup()


if __name__ == "__main__":
    main()
