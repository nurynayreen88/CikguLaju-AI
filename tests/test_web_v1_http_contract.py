"""HTTP contract tests: a disposable DB and no generation or production access."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.run_web_v1_preview import app


class WebDropdownHttpContract(unittest.TestCase):
    def test_read_only_chain_and_disabled_generation(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "fixture.sqlite"
            with sqlite3.connect(db) as con:
                con.execute("""CREATE TABLE rpt_entries (
                    id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
                    verified INTEGER, notes TEXT, sequence_no INTEGER,
                    unit_title TEXT, topic TEXT, subtopic TEXT, skill_focus TEXT)""")
                con.execute("""INSERT INTO rpt_entries VALUES
                    (1,'Tahun 3','Bahasa Inggeris',1,'',1,'Welcome','Greetings','Hello','Speaking')""")
            with patch.dict(os.environ, {"CIKGULAJU_WEB_PREVIEW_DB": str(db)}):
                client = app.test_client()
                subjects = client.get("/api/options?kind=subjects&year=3")
                self.assertEqual(subjects.status_code, 200)
                self.assertEqual([x["value"] for x in subjects.get_json()], ["ENGLISH"])
                units = client.get("/api/options?kind=units&year=3&subject=ENGLISH")
                self.assertEqual(units.status_code, 200)
                self.assertEqual([x["value"] for x in units.get_json()], ["Welcome"])
                pdp = client.get("/api/options?kind=pdp&year=3&subject=ENGLISH&unit=Welcome")
                self.assertEqual(pdp.status_code, 200)
                self.assertEqual([x["value"] for x in pdp.get_json()], ["1"])
                self.assertFalse(pdp.get_json()[0]["standalone_rph_verified"])
                self.assertEqual(client.post("/api/generate", json={"pdp_id": 1}).status_code, 503)
                self.assertEqual(client.get("/api/materials/download/1").status_code, 503)
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("SELECT COUNT(*) FROM rpt_entries").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
