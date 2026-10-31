"""Read-only verified RPT/PdP navigation; never infers lessons from weeks.

Uses the exact rpt_entries schema inspected in the main app.py source.
This is a candidate navigation dataset, NOT proof of standalone RPH completeness.
No import of production app.py and no database mutations.
"""
import sqlite3
from pathlib import Path
from web_v1_verified_topics import SUBJECTS


class VerifiedPdpCatalog:
    def __init__(self, database_path):
        self.database_path = Path(database_path)

    def list_pdp(self, *, year, subject_code, limit=500):
        if type(year) is not int or not 1 <= year <= 6:
            raise ValueError("invalid year")
        if subject_code not in SUBJECTS:
            raise ValueError("invalid subject")
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("invalid limit")
        if not self.database_path.is_file():
            raise FileNotFoundError("curriculum database unavailable")
        uri = self.database_path.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=2) as con:
            con.execute("PRAGMA query_only=ON")
            rows = con.execute(
                """SELECT id, sequence_no, unit_title, topic, subtopic, skill_focus
                   FROM rpt_entries
                   WHERE year_label=? AND subject=? AND verified=1
                     AND lower(COALESCE(notes,'')) NOT LIKE '%superseded%'
                   ORDER BY sequence_no, id LIMIT ?""",
                (f"Tahun {year}", SUBJECTS[subject_code], limit),
            ).fetchall()
        return [
            {"id": r[0], "pdp_no": r[1], "unit_title": r[2],
             "topic": r[3], "subtopic": r[4], "skill_focus": r[5]}
            for r in rows
        ]
