"""Smoke tests for the isolated English catalog web preview."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from cikgulaju_web_v1 import register_web_v1
from web.english_catalog_http import create_english_catalog_blueprint


class EnglishCatalogTests(unittest.TestCase):
    def test_opt_in_registration(self):
        app = Flask(__name__)
        self.assertFalse(register_web_v1(app))
        self.assertTrue(register_web_v1(app, enabled=True, catalog_only=True))
        response = app.test_client().get("/web/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "catalog-preview")

    def test_full_web_refused(self):
        app = Flask(__name__)
        with self.assertRaises(RuntimeError):
            register_web_v1(app, enabled=True)

    def test_catalog_exposes_only_existing_canonical_lessons(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            year = root / "year1"
            year.mkdir()
            (year / "lesson_001.md").write_text("draft", encoding="utf-8")
            (year / "lesson_2.md").write_text("legacy", encoding="utf-8")
            app = Flask(__name__)
            app.register_blueprint(create_english_catalog_blueprint(root))
            client = app.test_client()
            self.assertEqual(client.get("/api/web/catalog/english/1").status_code, 503)
            with patch("web_v1_telegram_auth_routes._config", return_value={"CIKGULAJU_WEB_SESSION_SECRET": "test-secret"}), patch("web_v1_sessions.verify_session_ticket", return_value=123), patch("web_v1_telegram_auth_routes._lookup", return_value={"telegram_user_id": 123}):
                client.set_cookie("cikgulaju_web_v1_session", "test-ticket")
                response = client.get("/api/web/catalog/english/1")
                self.assertEqual(client.get("/api/web/catalog/english/4").status_code, 404)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["count"], 1)
            self.assertEqual(response.json["lessons"][0]["lesson_no"], 1)
            self.assertEqual(response.headers["Cache-Control"], "no-store, private")


if __name__ == "__main__":
    unittest.main()
