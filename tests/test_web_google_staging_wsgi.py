"""Standalone WSGI staging must not expose any legacy production route."""
import os
import unittest
from unittest.mock import patch

from tools.run_google_payments_staging import app

STAGING="https://staging.example.test"
SECRET="standalone-staging-security-secret-at-least-32-chars"


class StandaloneStagingApp(unittest.TestCase):
    def setUp(self):
        self.environment=patch.dict(os.environ,{
            "CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED":"1",
            "CIKGULAJU_GOOGLE_STAGING_SUPABASE_URL":"https://abcdefghijklmnopqrst.supabase.co",
            "CIKGULAJU_GOOGLE_STAGING_PROJECT_REF":"abcdefghijklmnopqrst",
            "CIKGULAJU_GOOGLE_PRODUCTION_PROJECT_REF":"productionref1234567",
            "CIKGULAJU_GOOGLE_STAGING_SUPABASE_PUBLISHABLE_KEY":"sb_publishable_local_staging_test",
            "CIKGULAJU_GOOGLE_STAGING_SUPABASE_SERVICE_ROLE_KEY":"staging-role-key-test-not-real",
            "CIKGULAJU_WEB_SESSION_SECRET":SECRET,
            "CIKGULAJU_GOOGLE_STAGING_ORIGIN":STAGING,
            "CIKGULAJU_GOOGLE_STAGING_ALLOWED_HOST":"staging.example.test",
            "CIKGULAJU_GOOGLE_STAGING_ADMIN_TELEGRAM_IDS":"123456789",
            "CIKGULAJU_GOOGLE_STAGING_ADMIN_BOT_TOKEN":"123456789:staging-bot-token-test-placeholder",
            "CIKGULAJU_GOOGLE_STAGING_ADMIN_BOT_USERNAME":"CikguStagingBot",
        })
        self.environment.start()
        self.client=app.test_client()

    def tearDown(self):
        self.environment.stop()

    def test_ready_but_no_real_money_or_rph(self):
        response=self.client.get("/readyz",base_url=STAGING)
        self.assertEqual(response.status_code,200)
        self.assertFalse(response.json["real_payments_enabled"])
        self.assertFalse(response.json["rph_generator_enabled"])
        self.assertTrue(response.json["no_telegram_production_account_dependency"])

    def test_legacy_api_routes_not_imported(self):
        for route in (
            "/api/auth/telegram/widget",
            "/api/auth/telegram/session",
            "/api/web/teacher/profile",
            "/api/web/referral",
            "/api/web/rph/hari-ini",
        ):
            response=self.client.get(route,base_url=STAGING)
            self.assertEqual(response.status_code,404,route)

    def test_readiness_is_off_when_feature_disabled(self):
        with patch.dict(os.environ,{"CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED":"0"}):
            response=self.client.get("/readyz",base_url=STAGING)
        self.assertEqual(response.status_code,503)

    def test_public_entry_is_only_staging_google(self):
        self.assertEqual(
            self.client.get("/",base_url=STAGING).location,
            "/google-staging-login")


if __name__=="__main__":
    unittest.main()
