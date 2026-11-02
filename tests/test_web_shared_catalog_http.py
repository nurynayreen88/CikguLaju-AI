"""Shared-source catalog HTTP guard tests; no production database access."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.run_web_v1_preview import app
from web_v1_telegram_auth_routes import COOKIE


class SharedCatalogHttpTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.set_cookie(COOKIE, "test-session")

    def test_unverified_source_blocks_catalog(self):
        with patch("web_v1_telegram_auth_routes._config",
                   return_value={"CIKGULAJU_WEB_SESSION_SECRET": "test"}), \
             patch("web_v1_sessions.verify_session_ticket", return_value=123), \
             patch("web_v1_telegram_auth_routes._lookup",
                   return_value={"telegram_user_id": 123}), \
             patch.dict(os.environ, {"CIKGULAJU_WEB_PREVIEW_DB": "/tmp/preview-only.sqlite",
                                     "CIKGULAJU_SHARED_CATALOG_DB": ""}):
            response = self.client.get("/api/options?year=2&kind=subjects")
        self.assertEqual(response.status_code, 503)
        self.assertIn("shared catalog", response.get_json()["error"])

    def test_status_does_not_disclose_database_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "catalog.sqlite"
            path.write_bytes(b"fixture")
            with patch.dict(os.environ, {
                "CIKGULAJU_WEB_PREVIEW_DB": str(path),
                "CIKGULAJU_SHARED_CATALOG_DB": str(path)}):
                response = self.client.get("/api/source/status")
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.get_json()["shared_source_verified"])
            self.assertNotIn(str(path), response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
