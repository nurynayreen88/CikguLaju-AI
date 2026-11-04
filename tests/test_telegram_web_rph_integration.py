"""In-process end-to-end contract: Web HTTP adapter -> Telegram Flask API -> verified RPT -> RPH."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from web.telegram_curriculum_api import create_curriculum_blueprint
from web.authoritative_http_source import AuthoritativeHttpCurriculumSource
from web.authoritative_curriculum_source import CurriculumKey, SharedSourceUnavailable


class FlaskResponseAdapter:
    def __init__(self, response):
        self.status_code = response.status_code
        self.response = response
    def json(self):
        return self.response.get_json()


class FlaskTransport:
    def __init__(self, client):
        self.client = client
    def get(self, url, *, params, headers, timeout, allow_redirects):
        assert not allow_redirects
        assert url.endswith("/internal/curriculum/v1/approved-materials")
        return FlaskResponseAdapter(self.client.get(
            "/internal/curriculum/v1/approved-materials",
            query_string=params, headers=headers))


class BridgeEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "active.db"
        with sqlite3.connect(self.db) as con:
            con.execute("CREATE TABLE rpt_entries (id INTEGER, sequence_no INTEGER, "
                        "year_label TEXT, subject TEXT, verified INTEGER, notes TEXT)")
            con.executemany("INSERT INTO rpt_entries VALUES (?,?,?,?,?,?)", [
                (907, 12, "Tahun 2", "Bahasa Inggeris", 1, ""),
                (908, 13, "Tahun 2", "Bahasa Inggeris", 0, ""),
            ])
        app = Flask(__name__)
        app.register_blueprint(create_curriculum_blueprint(lambda: self.db))
        self.client = app.test_client()
        self.source = AuthoritativeHttpCurriculumSource(
            "https://telegram.example", "x" * 40,
            transport=FlaskTransport(self.client))

    @patch("web.telegram_english_rph_bridge.load_english_rph", return_value="# Lesson 12")
    def test_web_adapter_receives_exact_verified_rph(self, reader):
        with patch.dict(os.environ, {"CIKGULAJU_CURRICULUM_API_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "x" * 40}):
            items = self.source.get_approved_materials(CurriculumKey(2, "ENGLISH", "907"))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "RPH English Tahun 2 Lesson 12")
        self.assertFalse(items[0]["download_enabled"])
        reader.assert_called_once_with(2, 12)

    @patch("web.telegram_english_rph_bridge.load_english_rph")
    def test_unverified_rpt_is_not_exposed(self, reader):
        with patch.dict(os.environ, {"CIKGULAJU_CURRICULUM_API_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "x" * 40}):
            items = self.source.get_approved_materials(CurriculumKey(2, "ENGLISH", "908"))
        self.assertEqual(items, [])
        reader.assert_not_called()

    def test_wrong_service_token_fails_closed(self):
        with patch.dict(os.environ, {"CIKGULAJU_CURRICULUM_API_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "y" * 40}):
            with self.assertRaises(SharedSourceUnavailable):
                self.source.get_approved_materials(CurriculumKey(2, "ENGLISH", "907"))


if __name__ == "__main__":
    unittest.main()
