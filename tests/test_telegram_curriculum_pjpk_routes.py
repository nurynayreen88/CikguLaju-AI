"""Isolated Flask contract tests for PJ/PK; never import production app.py."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from web.telegram_curriculum_api import create_curriculum_blueprint


class CurriculumPJPKRoutesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "fixture.sqlite"
        with sqlite3.connect(self.db) as conn:
            conn.execute("""CREATE TABLE rpt_entries (
                id INTEGER PRIMARY KEY, sequence_no INTEGER, unit_title TEXT,
                topic TEXT, subtopic TEXT, skill_focus TEXT, year_label TEXT,
                subject TEXT, verified INTEGER, notes TEXT)""")
            conn.executemany(
                "INSERT INTO rpt_entries VALUES (?, ?, 'Unit A', 'Topic', 'Lesson', '', 'Tahun 2', 'PJPK', 1, '')",
                [(1, 1), (2, 2)])
            conn.execute("CREATE TABLE web_v1_pjpk_map (rpt_entry_id INTEGER, component TEXT, verified INTEGER)")
            conn.executemany("INSERT INTO web_v1_pjpk_map VALUES (?, ?, 1)", [(1, "PJ"), (2, "PK")])
        app = Flask(__name__)
        app.register_blueprint(create_curriculum_blueprint(lambda: str(self.db)))
        self.client = app.test_client()
        self.headers = {"Authorization": "Bearer " + "t" * 32}
        env = patch.dict(os.environ, {
            "CIKGULAJU_CURRICULUM_API_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "t" * 32,
        })
        env.start()
        self.addCleanup(env.stop)

    def get(self, endpoint, **params):
        return self.client.get("/internal/curriculum/v1/" + endpoint,
                               query_string=params, headers=self.headers)

    def test_pj_and_pk_lessons_never_mix(self):
        for component, expected in (("PJ", "1"), ("PK", "2")):
            response = self.get("lessons", year=2, subject="PJPK", unit="Unit A", component=component)
            self.assertEqual(response.status_code, 200)
            self.assertEqual([r["value"] for r in response.json["items"]], [expected])

    def test_missing_component_is_rejected(self):
        response = self.get("units", year=2, subject="PJPK")
        self.assertEqual(response.status_code, 400)

    def test_invalid_extra_parameter_is_rejected(self):
        response = self.get("units", year=2, subject="PJPK", component="PJ", extra="x")
        self.assertEqual(response.status_code, 400)

    def test_no_token_is_rejected(self):
        response = self.client.get("/internal/curriculum/v1/subjects?year=2")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
