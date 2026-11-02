"""Verified-schema, read-only curriculum topic discovery for the Web V1 staging app.

Source: app.py (main), curriculum_topics schema. Not a standalone lesson catalog.
No production app import, database mutation, or HTTP route registration.
"""
import sqlite3
from pathlib import Path

SUBJECTS = {
    "ENGLISH": "Bahasa Inggeris",
    "BM": "Bahasa Melayu",
    "MATH": "Matematik",
    "SCIENCE": "Sains",
    "PI": "Pendidikan Islam",
    "PJPK": "PJPK",
}


class VerifiedTopicCatalog:
    def __init__(self, database_path):
        self.database_path = Path(database_path)

    def list_topics(self, *, year, subject_code):
        if type(year) is not int or year not in range(1, 7):
            raise ValueError("year must be 1..6")
        if subject_code not in SUBJECTS:
            raise ValueError("unsupported subject")
        if not self.database_path.is_file():
            raise FileNotFoundError("curriculum database unavailable")
        uri = self.database_path.resolve().as_uri() + "?mode=ro"
        # Query-only and read-only URI prevent accidental writes or database creation.
        with sqlite3.connect(uri, uri=True, timeout=2) as con:
            con.execute("PRAGMA query_only=ON")
            rows = con.execute(
                """SELECT id, year_label, subject, topic, subtopic
                   FROM curriculum_topics
                   WHERE year_label=? AND subject=?
                   ORDER BY topic, subtopic, id LIMIT 1000""",
                (f"Tahun {year}", SUBJECTS[subject_code]),
            ).fetchall()
        return [
            {"id": row[0], "year_label": row[1], "subject": row[2],
             "topic": row[3], "subtopic": row[4]}
            for row in rows
        ]
