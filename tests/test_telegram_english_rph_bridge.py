import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from web.telegram_english_rph_bridge import verified_english_rph_metadata


class TelegramRphBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "master.db"
        with sqlite3.connect(self.db) as con:
            con.execute("CREATE TABLE rpt_entries (id INTEGER, sequence_no INTEGER, "
                        "year_label TEXT, subject TEXT, verified INTEGER, notes TEXT)")
            con.executemany("INSERT INTO rpt_entries VALUES (?,?,?,?,?,?)", [
                (93, 12, "Tahun 2", "Bahasa Inggeris", 1, ""),
                (94, 13, "Tahun 2", "Bahasa Inggeris", 0, ""),
                (95, 14, "Tahun 2", "Bahasa Inggeris", 1, "superseded"),
                (96, 15, "Tahun 3", "Bahasa Inggeris", 1, ""),
            ])

    @patch("web.telegram_english_rph_bridge.load_english_rph", return_value="# Lesson 12")
    def test_uses_sequence_number_not_database_id(self, reader):
        items = verified_english_rph_metadata(self.db, 2, 93)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "RPH English Tahun 2 Lesson 12")
        self.assertFalse(items[0]["download_enabled"])
        reader.assert_called_once_with(2, 12)

    @patch("web.telegram_english_rph_bridge.load_english_rph")
    def test_unverified_superseded_wrong_year_not_exposed(self, reader):
        for row_id in (94, 95, 96, 999):
            self.assertEqual(verified_english_rph_metadata(self.db, 2, row_id), [])
        reader.assert_not_called()

    @patch("web.telegram_english_rph_bridge.load_english_rph")
    def test_duplicate_verified_sequence_is_rejected(self, reader):
        with sqlite3.connect(self.db) as con:
            con.execute("INSERT INTO rpt_entries VALUES (?,?,?,?,?,?)",
                        (120, 12, "Tahun 2", "Bahasa Inggeris", 1, ""))
        self.assertEqual(verified_english_rph_metadata(self.db, 2, 93), [])
        reader.assert_not_called()

    def test_http_route_returns_verified_source_and_metadata(self):
        import os
        from flask import Flask
        from web.telegram_curriculum_api import create_curriculum_blueprint
        app = Flask(__name__)
        app.register_blueprint(create_curriculum_blueprint(lambda: self.db))
        with patch.dict(os.environ, {"CIKGULAJU_CURRICULUM_API_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "x" * 40}), \
             patch("web.telegram_english_rph_bridge.load_english_rph", return_value="# Lesson 12"):
            response = app.test_client().get(
                "/internal/curriculum/v1/approved-materials?year=2&subject=ENGLISH&lesson=93",
                headers={"Authorization": "Bearer " + "x" * 40},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["source"], "telegram-runtime-v1")
        self.assertEqual(response.json["items"][0]["title"], "RPH English Tahun 2 Lesson 12")

    def test_http_route_requires_bearer_token(self):
        import os
        from flask import Flask
        from web.telegram_curriculum_api import create_curriculum_blueprint
        app = Flask(__name__)
        app.register_blueprint(create_curriculum_blueprint(lambda: self.db))
        with patch.dict(os.environ, {"CIKGULAJU_CURRICULUM_API_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "x" * 40}):
            response = app.test_client().get(
                "/internal/curriculum/v1/approved-materials?year=2&subject=ENGLISH&lesson=93")
        self.assertEqual(response.status_code, 401)

    def test_http_route_rejects_invalid_selections(self):
        import os
        from flask import Flask
        from web.telegram_curriculum_api import create_curriculum_blueprint
        app = Flask(__name__)
        app.register_blueprint(create_curriculum_blueprint(lambda: self.db))
        with patch.dict(os.environ, {"CIKGULAJU_CURRICULUM_API_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "x" * 40}):
            client = app.test_client()
            for query in ("year=2&subject=ENGLISH&lesson=0",
                          "year=2&subject=UNKNOWN&lesson=93",
                          "year=2&subject=ENGLISH&lesson=93&lesson=94",
                          "year=2&subject=ENGLISH&lesson=-1"):
                response = client.get(
                    "/internal/curriculum/v1/approved-materials?" + query,
                    headers={"Authorization": "Bearer " + "x" * 40})
                self.assertEqual(response.status_code, 400, query)

    @patch("web.telegram_english_rph_bridge.load_english_rph", return_value=None)
    def test_missing_rph_not_exposed(self, reader):
        self.assertEqual(verified_english_rph_metadata(self.db, 2, 93), [])


if __name__ == "__main__":
    unittest.main()
