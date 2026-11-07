"""Production status endpoint: no user data or writes, private token only."""
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch
from flask import Flask

from web.telegram_prod_paid_status_bridge import bp

TOKEN = "private-production-paid-bridge-" + "x" * 52
URL = "https://cikgulaju-web.onrender.com"
UID = 123456789
CFG = {"account_backend": "supabase",
       "supabase_url": "https://soxakntcanbycjoygrcx.supabase.co"}


class PrivateProductionPaidStatusTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(bp)
        self.client = app.test_client()
        self.path = "/internal/identity/v1/entitlements"

    def post(self, payload=None, token=TOKEN, host=URL):
        return self.client.post(self.path, base_url=host,
            headers={"Authorization": "Bearer " + token},
            json={"telegram_user_id": UID} if payload is None else payload)

    def test_disabled_by_default_and_weak_secret_never_query_production(self):
        with (patch.dict("os.environ", {"CIKGULAJU_PAID_BRIDGE_PRODUCTION_ENABLED": "0",
                                       "CIKGULAJU_PAID_BRIDGE_TOKEN": TOKEN}),
              patch("web_v1_telegram_auth_routes._lookup") as lookup):
            self.assertEqual(self.post().status_code, 503)
            lookup.assert_not_called()
        with patch.dict("os.environ", {"CIKGULAJU_PAID_BRIDGE_PRODUCTION_ENABLED": "1",
                                       "CIKGULAJU_PAID_BRIDGE_TOKEN": "weak"}):
            self.assertEqual(self.post().status_code, 503)

    def test_unauthorized_wrong_host_and_invalid_payload_blocked(self):
        with (patch.dict("os.environ", {"CIKGULAJU_PAID_BRIDGE_PRODUCTION_ENABLED": "1",
                                       "CIKGULAJU_PAID_BRIDGE_TOKEN": TOKEN}),
              patch("web_v1_telegram_auth_routes._lookup") as lookup):
            self.assertEqual(self.post(token="wrong").status_code, 401)
            self.assertEqual(self.post(host="https://attacker.example").status_code, 403)
            for body in ({}, {"telegram_user_id": "123456789"},
                         {"telegram_user_id": -1}, {"telegram_user_id": UID,
                                                    "account_id": "different"}):
                self.assertEqual(self.post(payload=body).status_code, 400)
            lookup.assert_not_called()

    def test_lifetime_paid_status_from_existing_registered_account(self):
        with (patch.dict("os.environ", {"CIKGULAJU_PAID_BRIDGE_PRODUCTION_ENABLED": "1",
                                       "CIKGULAJU_PAID_BRIDGE_TOKEN": TOKEN}),
              patch("web_v1_telegram_auth_routes._config", return_value=CFG),
              patch("web_v1_telegram_auth_routes._lookup", return_value={
                 "authenticated": True, "telegram_user_id": UID,
                 "rakan_pembangun": True, "vip_expires_at": None,
                 "free_remaining": 0, "username": "do-not-expose",
                 "payment_reference": "private-never-send"}) as lookup):
            response = self.post()
            self.assertEqual(response.status_code, 200, response.json)
            self.assertEqual(response.json["source"],
                             "cikgulaju-prod-entitlements-v1")
            self.assertTrue(response.json["rakan_pembangun_active"])
            self.assertFalse(response.json["subscription_active"])
            self.assertIsNone(response.json["subscription_expires_at"])
            self.assertNotIn("username", response.get_data(as_text=True))
            self.assertNotIn("payment_reference", response.get_data(as_text=True))
            self.assertEqual(response.headers["Cache-Control"], "no-store, private")
            lookup.assert_called_once_with(CFG, UID)

    def test_future_subscription_and_missing_account(self):
        expiry=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        with (patch.dict("os.environ", {"CIKGULAJU_PAID_BRIDGE_PRODUCTION_ENABLED": "1",
                                       "CIKGULAJU_PAID_BRIDGE_TOKEN": TOKEN}),
              patch("web_v1_telegram_auth_routes._config", return_value=CFG),
              patch("web_v1_telegram_auth_routes._lookup", return_value={
                  "authenticated": True, "telegram_user_id": UID,
                  "rakan_pembangun": False, "vip_expires_at": expiry})):
            r=self.post()
            self.assertEqual(r.status_code, 200)
            self.assertFalse(r.json["rakan_pembangun_active"])
            self.assertTrue(r.json["subscription_active"])
            self.assertEqual(r.json["subscription_expires_at"], expiry)
        with (patch.dict("os.environ", {"CIKGULAJU_PAID_BRIDGE_PRODUCTION_ENABLED": "1",
                                       "CIKGULAJU_PAID_BRIDGE_TOKEN": TOKEN}),
              patch("web_v1_telegram_auth_routes._config", return_value=CFG),
              patch("web_v1_telegram_auth_routes._lookup", return_value=None)):
            self.assertEqual(self.post().status_code, 404)

    def test_wrong_backend_or_inconsistent_identity_fails_closed(self):
        with (patch.dict("os.environ", {"CIKGULAJU_PAID_BRIDGE_PRODUCTION_ENABLED": "1",
                                       "CIKGULAJU_PAID_BRIDGE_TOKEN": TOKEN}),
              patch("web_v1_telegram_auth_routes._config", return_value={
                "account_backend": "supabase",
                "supabase_url": "https://eqrcjlnvcytkgazptbor.supabase.co"}),
              patch("web_v1_telegram_auth_routes._lookup") as lookup):
            self.assertEqual(self.post().status_code, 503)
            lookup.assert_not_called()
        with (patch.dict("os.environ", {"CIKGULAJU_PAID_BRIDGE_PRODUCTION_ENABLED": "1",
                                       "CIKGULAJU_PAID_BRIDGE_TOKEN": TOKEN}),
              patch("web_v1_telegram_auth_routes._config", return_value=CFG),
              patch("web_v1_telegram_auth_routes._lookup", return_value={
                "authenticated": True, "telegram_user_id": UID+1,
                "rakan_pembangun": True})):
            self.assertEqual(self.post().status_code, 503)


if __name__ == "__main__":
    unittest.main()
