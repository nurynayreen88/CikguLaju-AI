"""Isolated optional Telegram WSGI tests without importing real app.py."""
import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch
from flask import Flask


class OptionalWsgiTests(unittest.TestCase):
    def load_entry(self, enabled, active):
        fake = types.ModuleType("app")
        fake.app = Flask("telegram_stub")
        fake.DB_PATH = "/missing-master.db"
        fake.CIKGULAJU_DB_V2600_ACTIVE = active
        @fake.app.post("/webhook")
        def webhook():
            return {"ok": True}
        env = {"CIKGULAJU_CURRICULUM_API_ENABLED": "1" if enabled else "0",
               "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "t" * 32}
        with patch.dict(sys.modules, {"app": fake}), patch.dict(os.environ, env):
            sys.modules.pop("tools.run_telegram_with_curriculum_api", None)
            entry = importlib.import_module("tools.run_telegram_with_curriculum_api")
        return entry

    def test_disabled_preserves_webhook(self):
        entry = self.load_entry(False, True)
        self.assertEqual(entry.app.test_client().post("/webhook").status_code, 200)
        self.assertNotIn("telegram_curriculum_v1", entry.app.blueprints)

    def test_enabled_missing_master_returns_503(self):
        entry = self.load_entry(True, True)
        self.assertIn("telegram_curriculum_v1", entry.app.blueprints)
        with patch.dict(os.environ, {"CIKGULAJU_CURRICULUM_API_ENABLED": "1",
                                      "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "t" * 32}):
            response = entry.app.test_client().get(
                "/internal/curriculum/v1/subjects?year=2",
                headers={"Authorization": "Bearer " + "t" * 32})
        self.assertEqual(response.status_code, 503)

    def test_fallback_master_request_returns_503(self):
        entry = self.load_entry(True, False)
        with patch.dict(os.environ, {"CIKGULAJU_CURRICULUM_API_ENABLED": "1",
                                      "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "t" * 32}):
            response = entry.app.test_client().get(
                "/internal/curriculum/v1/subjects?year=2",
                headers={"Authorization": "Bearer " + "t" * 32})
        self.assertEqual(response.status_code, 503)

    def test_missing_api_token_does_not_break_webhook(self):
        fake = types.ModuleType("app")
        fake.app = Flask("telegram_missing_token_stub")
        fake.DB_PATH = "/missing-master.db"
        fake.CIKGULAJU_DB_V2600_ACTIVE = True

        @fake.app.post("/webhook")
        def webhook():
            return {"ok": True}

        with patch.dict(sys.modules, {"app": fake}), patch.dict(os.environ, {
            "CIKGULAJU_CURRICULUM_API_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": ""
        }):
            sys.modules.pop("tools.run_telegram_with_curriculum_api", None)
            entry = importlib.import_module("tools.run_telegram_with_curriculum_api")
        self.assertEqual(entry.app.test_client().post("/webhook").status_code, 200)
        self.assertNotIn("telegram_curriculum_v1", entry.app.blueprints)

    def test_fallback_master_is_not_served(self):
        entry = self.load_entry(True, False)
        self.assertIsNone(entry.active_master_database())
        self.assertIn("telegram_curriculum_v1", entry.app.blueprints)


if __name__ == "__main__":
    unittest.main()
