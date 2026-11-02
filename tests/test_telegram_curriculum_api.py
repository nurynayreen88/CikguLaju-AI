"""Regression checks for read-only Telegram curriculum API."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from web.telegram_curriculum_api import create_curriculum_blueprint


class CurriculumApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "master.db"
        with sqlite3.connect(self.db) as con:
            con.execute("""CREATE TABLE rpt_entries (
                id INTEGER PRIMARY KEY, sequence_no INTEGER, unit_title TEXT,
                topic TEXT, subtopic TEXT, skill_focus TEXT, year_label TEXT,
                subject TEXT, verified INTEGER, notes TEXT)""")
            con.execute("""INSERT INTO rpt_entries VALUES
                (1,1,'Unit A','Topic A','Subtopic A','Reading','Tahun 2',
                'Bahasa Inggeris',1,'')""")
        self.app = Flask(__name__)
        self.app.register_blueprint(create_curriculum_blueprint(lambda: str(self.db)))
        self.client = self.app.test_client()
        self.token = "a" * 48
        self.env = patch.dict(os.environ, {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": self.token})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def get(self, endpoint, **params):
        return self.client.get("/internal/curriculum/v1/" + endpoint,
                               query_string=params,
                               headers={"Authorization": "Bearer " + self.token})

    def test_unauthorized(self):
        response = self.client.get("/internal/curriculum/v1/subjects?year=2")
        self.assertEqual(response.status_code, 401)

    def test_verified_subjects_units_and_lessons(self):
        subjects = self.get("subjects", year=2)
        self.assertEqual(subjects.status_code, 200)
        self.assertEqual(subjects.json["source"], "telegram-runtime-v1")
        code = next(x["value"] for x in subjects.json["items"]
                    if x["label"] == "Bahasa Inggeris")
        units = self.get("units", year=2, subject=code)
        self.assertEqual(units.json["items"][0]["value"], "Unit A")
        lessons = self.get("lessons", year=2, subject=code, unit="Unit A")
        self.assertEqual(lessons.json["items"][0]["value"], "1")

    def test_unapproved_materials_not_exposed(self):
        self.assertEqual(self.get("approved-materials", year=2).status_code, 503)

    def test_invalid_year(self):
        self.assertEqual(self.get("subjects", year=99).status_code, 400)

    def test_no_database_writes(self):
        self.get("subjects", year=2)
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM rpt_entries").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
