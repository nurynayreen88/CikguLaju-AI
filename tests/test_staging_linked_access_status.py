"""Read-only shared staging entitlements, verified by either login provider.

No production account lookups or mutations. The staging entitlement state
must remain explicitly separate from Telegram production subscriptions.
"""
import unittest
from unittest.mock import patch
from flask import Flask, jsonify

from web.google_web_catalog_staging import bp
from web.provider_neutral_web_identity import (
    from_verified_google_account, from_verified_linked_telegram_account
)

ACCOUNT = "1a267083-8511-4587-a585-857fe35f4a14"
CFG = {"supabase_url": "https://isolated.supabase.co",
       "secret": "x" * 48}
PROFILE = {"account_id": ACCOUNT, "trial_remaining": 8, "display_name": "Guru"}
GOOGLE = from_verified_google_account(ACCOUNT, PROFILE)
TELEGRAM = from_verified_linked_telegram_account(123456789, ACCOUNT, PROFILE)


class StagingAccessStatusTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(bp)
        self.client = app.test_client()

    def test_same_account_and_plans_under_both_provider_sessions(self):
        for actor in (GOOGLE, TELEGRAM):
            with (self.subTest(provider=actor.provider),
                patch("web.google_web_catalog_staging._actor",
                      return_value=(actor, None)),
                patch("web.google_web_catalog_staging._enabled_config",
                      return_value=CFG),
                patch("web.google_web_catalog_staging.google_staging_account_profile",
                      return_value=PROFILE),
                patch("web.google_payment_store.web_payment_access",
                      return_value={
                          "payment_access_active": True,
                          "active_plans": [{"plan_code": "rakan_pembangun",
                                            "valid_until": None}]}),
            ):
                result = self.client.get("/api/google-staging/web/access/status")
                self.assertEqual(result.status_code, 200, result.json)
                self.assertEqual(result.json["auth_provider"], actor.provider)
                self.assertEqual(result.json["trial_remaining"], 8)
                self.assertTrue(result.json["staging_payment_access_active"])
                self.assertEqual(result.json["staging_active_plans"][0]["plan_code"],
                                 "rakan_pembangun")
                self.assertFalse(result.json["production_entitlements_synced"])
                self.assertFalse(result.json["real_payments_enabled"])
                self.assertEqual(result.headers["Cache-Control"], "no-store, private")

    def test_no_staging_entitlements_not_a_production_denial(self):
        with (patch("web.google_web_catalog_staging._actor",
                    return_value=(TELEGRAM, None)),
              patch("web.google_web_catalog_staging._enabled_config",
                    return_value=CFG),
              patch("web.google_web_catalog_staging.google_staging_account_profile",
                    return_value=PROFILE),
              patch("web.google_payment_store.web_payment_access",
                    return_value={"payment_access_active": False, "active_plans": []})):
            result = self.client.get("/api/google-staging/web/access/status")
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.json["staging_payment_access_active"])
        self.assertFalse(result.json["production_entitlements_synced"])
        self.assertEqual(result.json["trial_remaining"], 8)

    def test_unauthenticated_and_conflict_never_expose_paid_access(self):
        for code in (401, 403):
            with patch("web.google_web_catalog_staging._actor",
                       return_value=(None, ({"error": "Denied"}, code))):
                self.assertEqual(self.client.get(
                    "/api/google-staging/web/access/status").status_code, code)

    def test_rejects_browser_query_and_bad_backend(self):
        with (patch("web.google_web_catalog_staging._actor",
                    return_value=(GOOGLE, None)),
              patch("web.google_web_catalog_staging._enabled_config",
                    return_value=CFG),
              patch("web.google_web_catalog_staging.google_staging_account_profile",
                    return_value=PROFILE),
              patch("web.google_payment_store.web_payment_access",
                    return_value={"payment_access_active": True,
                                  "active_plans": [{"plan_code": "malicious",
                                                    "valid_until": None}]})):
            self.assertEqual(self.client.get(
                "/api/google-staging/web/access/status?account_id=" + ACCOUNT).status_code, 400)
            self.assertEqual(self.client.get(
                "/api/google-staging/web/access/status").status_code, 503)


if __name__ == "__main__":
    unittest.main()
