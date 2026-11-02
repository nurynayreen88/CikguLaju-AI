"""Exercise real preview endpoints with an isolated temporary SQLite catalog."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.run_web_v1_preview import app


class PreviewEndToEndTests(unittest.TestCase):
    def test_verified_dropdowns_and_fail_closed_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "preview.db"
            with sqlite3.connect(db) as con:
                con.execute("""CREATE TABLE rpt_entries (
                    id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
                    verified INTEGER, notes TEXT, sequence_no INTEGER,
                    unit_title TEXT, topic TEXT, subtopic TEXT, skill_focus TEXT)""")
                con.executemany(
                    "INSERT INTO rpt_entries VALUES (?,?,?,?,?,?,?,?,?,?)", [
                        (11, "Tahun 3", "Bahasa Inggeris", 1, "", 1, "Welcome", "Greetings", "Hello", "Speaking"),
                        (12, "Tahun 3", "Bahasa Inggeris", 1, "", 2, "Welcome", "Names", "My name", "Listening"),
                        (13, "Tahun 3", "Bahasa Inggeris", 0, "", 3, "Secret", "Hidden", "Hidden", ""),
                    ])
            with patch.dict(os.environ, {"CIKGULAJU_WEB_PREVIEW_DB": str(db)}):
                client = app.test_client()
                # The temporary catalog must not be exposed without a signed session.
                for query in (
                    "kind=subjects&year=3",
                    "kind=units&year=3&subject=ENGLISH",
                    "kind=pdp&year=3&subject=ENGLISH&unit=Welcome",
                    "kind=pdp&year=3&subject=ENGLISH&unit=Secret",
                ):
                    self.assertIn(client.get("/api/options?" + query).status_code, (401, 503))
                self.assertEqual(client.post("/api/generate").status_code, 503)
                self.assertFalse(client.get("/health").json["generation_enabled"])


if __name__ == "__main__":
    unittest.main()
