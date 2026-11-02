"""Verify local Web V1 cannot bypass the shared Telegram backend."""
import unittest
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch
from web_v1_verified_pdp import list_explicit_pjpk_entries
from tools.run_web_v1_preview import app


class SharedRoutesTests(unittest.TestCase):
    def test_readiness_is_truthful(self):
        client = app.test_client()
        response = client.get("/api/shared/status")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["shared_backend_connected"])
        self.assertFalse(response.json["generation_enabled"])

    def test_pjpk_unclassified_data_never_mixes(self):
        client = app.test_client()
        result = client.get("/api/options?kind=components&year=3&subject=PJPK")
        self.assertIn(result.status_code, (401, 503))

    def test_legacy_preview_keeps_pjpk_component_selection(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "web_v1_preview/index.html").read_text(encoding="utf-8")
        self.assertIn('id="pjpk-component-field" hidden', html)
        self.assertIn('value="PJ"', html)
        self.assertIn('value="PK"', html)

    def test_missing_pjpk_mapping_is_safe(self):
        with tempfile.TemporaryDirectory() as folder:
            db = str(Path(folder) / "preview.db")
            with sqlite3.connect(db) as con:
                con.execute("CREATE TABLE rpt_entries (id INTEGER)")
            self.assertEqual(list_explicit_pjpk_entries(db, 3, "PJ"), [])
            self.assertEqual(list_explicit_pjpk_entries(db, 3, "PK"), [])

    def test_pjpk_mapping_excludes_unverified_and_other_component(self):
        with tempfile.TemporaryDirectory() as folder:
            db = str(Path(folder) / "preview.db")
            with sqlite3.connect(db) as con:
                con.execute("CREATE TABLE rpt_entries (id INTEGER, sequence_no INTEGER, unit_title TEXT, topic TEXT, subtopic TEXT, year_label TEXT, subject TEXT, verified INTEGER, notes TEXT)")
                con.execute("CREATE TABLE web_v1_pjpk_map (rpt_entry_id INTEGER, component TEXT, verified INTEGER)")
                for entry_id in (1, 2, 3, 4):
                    con.execute("INSERT INTO rpt_entries VALUES (?,?,?,?,?,?,?,?,?)",
                                (entry_id, entry_id, "Unit A", "Topik", "Subtopik", "Tahun 3", "PJPK", 1, ""))
                for entry_id, component, verified in ((1, "PJ", 1), (2, "PK", 1), (3, "PJ", 0), (4, "PK", 0)):
                    con.execute("INSERT INTO web_v1_pjpk_map VALUES (?,?,?)", (entry_id, component, verified))
            self.assertEqual([r["id"] for r in list_explicit_pjpk_entries(db, 3, "PJ")], [1])
            self.assertEqual([r["id"] for r in list_explicit_pjpk_entries(db, 3, "PK")], [2])
            with patch.dict("os.environ", {"CIKGULAJU_WEB_PREVIEW_DB": db}):
                response = app.test_client().get("/api/options?kind=pdp&year=3&subject=PJPK&component=PJ&unit=Unit+A")
                self.assertIn(response.status_code, (401, 503))

    def test_conflicting_verified_classifications_are_hidden(self):
        with tempfile.TemporaryDirectory() as folder:
            db = str(Path(folder) / "preview.db")
            with sqlite3.connect(db) as con:
                con.execute("CREATE TABLE rpt_entries (id INTEGER, sequence_no INTEGER, unit_title TEXT, topic TEXT, subtopic TEXT, year_label TEXT, subject TEXT, verified INTEGER, notes TEXT)")
                con.execute("CREATE TABLE web_v1_pjpk_map (rpt_entry_id INTEGER, component TEXT, verified INTEGER)")
                con.execute("INSERT INTO rpt_entries VALUES (1,1,'Unit A','Topik','Subtopik','Tahun 3','PJPK',1,'')")
                con.executemany("INSERT INTO web_v1_pjpk_map VALUES (1,?,1)", [("PJ",), ("PK",)])
            self.assertEqual(list_explicit_pjpk_entries(db, 3, "PJ"), [])
            self.assertEqual(list_explicit_pjpk_entries(db, 3, "PK"), [])

    def test_generation_and_download_fail_closed(self):
        client = app.test_client()
        for method, path in (
            ("get", "/api/materials"),
            ("post", "/api/generate"),
            ("get", "/api/materials/download/any-file"),
        ):
            with self.subTest(path=path):
                self.assertEqual(getattr(client, method)(path).status_code, 503)


if __name__ == "__main__":
    unittest.main()
