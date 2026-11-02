"""Integration hook contract tests; never import the Telegram production app."""
import os
import unittest
from unittest.mock import patch
from flask import Flask
from web.register_curriculum_api import register_if_enabled


class CurriculumRegistrationTests(unittest.TestCase):
    def test_disabled_does_not_register_routes(self):
        app = Flask(__name__)
        with patch.dict(os.environ, {"CIKGULAJU_CURRICULUM_API_ENABLED": "0"}):
            self.assertFalse(register_if_enabled(app, lambda: "/missing"))
        self.assertNotIn("telegram_curriculum_v1", app.blueprints)

    def test_enabled_without_token_refuses_registration(self):
        app = Flask(__name__)
        with patch.dict(os.environ, {"CIKGULAJU_CURRICULUM_API_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": ""}):
            self.assertFalse(register_if_enabled(app, lambda: "/missing"))
        self.assertNotIn("telegram_curriculum_v1", app.blueprints)

    def test_enabled_registers_without_touching_existing_routes(self):
        app = Flask(__name__)
        @app.post("/webhook")
        def webhook():
            return {"ok": True}
        with patch.dict(os.environ, {"CIKGULAJU_CURRICULUM_API_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "t" * 32}):
            self.assertTrue(register_if_enabled(app, lambda: "/missing"))
        self.assertIn("telegram_curriculum_v1", app.blueprints)
        self.assertEqual(app.test_client().post("/webhook").status_code, 200)


if __name__ == "__main__":
    unittest.main()
