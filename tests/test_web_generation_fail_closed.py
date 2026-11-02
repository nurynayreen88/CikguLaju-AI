"""Regression: authenticated Web users cannot bypass shared quota accounting.

Run: python -m unittest tests.test_web_generation_fail_closed
No network, Telegram bot, or production database required.
"""
import unittest
from unittest.mock import patch

from tools.run_web_v1_preview import app
from web_v1_telegram_auth_routes import COOKIE


class GenerationFailClosedTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.set_cookie(COOKIE, "test-session")

    def test_both_routes_reject_authenticated_unmetered_generation(self):
        config = {"CIKGULAJU_WEB_SESSION_SECRET": "test-only-secret"}
        account = {"telegram_user_id": 12345, "authenticated": True,
                   "free_remaining": 5}
        with patch("web_v1_telegram_auth_routes._config", return_value=config), \
             patch("web_v1_sessions.verify_session_ticket", return_value=12345), \
             patch("web_v1_telegram_auth_routes._lookup", return_value=account), \
             patch.dict("os.environ", {"CIKGULAJU_ENV": "staging",
                                      "CIKGULAJU_WEB_RPH_STAGING_ENABLED": "1"}):
            for url, payload in (
                ("/api/generate", {"lesson_id": 1, "format": "pdf"}),
                ("/api/web/english/rph", {"year": 2, "lesson_no": 1, "format": "docx"}),
            ):
                with self.subTest(url=url):
                    response = self.client.post(url, json=payload)
                    self.assertEqual(response.status_code, 503)
                    self.assertEqual(response.mimetype, "application/json")
                    self.assertIn("delivery not enabled", response.get_json()["error"].lower())


if __name__ == "__main__":
    unittest.main()
