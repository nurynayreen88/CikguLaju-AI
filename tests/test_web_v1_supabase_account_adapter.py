"""Isolated, read-only contract tests: no Supabase network or account writes."""
import json
import unittest
from unittest.mock import patch
from urllib.parse import urlparse, parse_qs

from web_v1_supabase_account_adapter import lookup_existing_supabase_account
from web_v1_entitlements import display_trusted_account


class _Response:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, *args):
        return json.dumps(self.payload).encode()


class SupabaseAccountParityTests(unittest.TestCase):
    def _lookup(self, pioneer=False, trial=5):
        def fake_urlopen(request, timeout):
            parsed = urlparse(request.full_url)
            table = parsed.path.split('/')[-1]
            filters = parse_qs(parsed.query)
            self.assertEqual(filters['telegram_user_id'], ['eq.42'])
            if table == 'cikgulaju_users':
                return _Response([{'telegram_user_id': 42, 'trial_remaining': trial}])
            if table == 'pioneer_entitlements':
                return _Response([{'entitlement': 'PIONEER_LIFETIME', 'revoked_at': None}] if pioneer else [])
            if table == 'subscriptions':
                return _Response([])
            raise AssertionError('unexpected table: ' + table)
        with patch('web_v1_supabase_account_adapter.urlopen', side_effect=fake_urlopen):
            return lookup_existing_supabase_account('https://example.supabase.co', 'test-secret', 42)

    def test_actual_pioneer_entitlement_is_lifetime(self):
        account = self._lookup(pioneer=True)
        self.assertTrue(account['rakan_pembangun'])
        self.assertEqual(display_trusted_account(account)['access'], 'Tanpa had seumur hidup')

    def test_trial_balance_is_displayed_without_invented_denominator(self):
        account = self._lookup(trial=5)
        self.assertFalse(account['rakan_pembangun'])
        self.assertEqual(display_trusted_account(account)['access'], '5 janaan percuma berbaki')

    def test_zero_balance_is_not_lifetime(self):
        account = self._lookup(trial=0)
        self.assertFalse(account['rakan_pembangun'])
        self.assertEqual(account['free_remaining'], 0)


    def test_new_secret_key_uses_apikey_without_bearer(self):
        """Supabase sb_secret_ is opaque: never send as a JWT bearer."""
        called = []
        def fake_urlopen(request, timeout):
            headers = {key.lower(): value for key, value in request.header_items()}
            self.assertEqual(headers.get("apikey"), "sb_secret_test_only_key")
            self.assertNotIn("authorization", headers)
            table = urlparse(request.full_url).path.split("/")[-1]
            called.append(table)
            if table == "cikgulaju_users":
                return _Response([{"telegram_user_id": 42, "trial_remaining": 8}])
            if table == "pioneer_entitlements":
                return _Response([{"entitlement": "rakan_pembangun",
                                   "revoked_at": None}])
            if table == "subscriptions":
                return _Response([])
            raise AssertionError("Unexpected table: " + table)
        with patch("web_v1_supabase_account_adapter.urlopen",
                   side_effect=fake_urlopen):
            result = lookup_existing_supabase_account(
                "https://example.supabase.co", "sb_secret_test_only_key", 42)
        self.assertEqual(called, ["cikgulaju_users",
                                  "pioneer_entitlements", "subscriptions"])
        self.assertEqual(result["free_remaining"], 8)
        self.assertTrue(result["rakan_pembangun"])

    def test_legacy_service_role_jwt_keeps_bearer(self):
        """Current production legacy auth must behave identically."""
        def fake_urlopen(request, timeout):
            headers = {key.lower(): value for key, value in request.header_items()}
            self.assertEqual(headers.get("apikey"), "legacy-service-role-jwt")
            self.assertEqual(headers.get("authorization"),
                             "Bearer legacy-service-role-jwt")
            table = urlparse(request.full_url).path.split("/")[-1]
            if table == "cikgulaju_users":
                return _Response([{"telegram_user_id": 42, "trial_remaining": 10}])
            return _Response([])
        with patch("web_v1_supabase_account_adapter.urlopen",
                   side_effect=fake_urlopen):
            result = lookup_existing_supabase_account(
                "https://example.supabase.co", "legacy-service-role-jwt", 42)
        self.assertEqual(result["free_remaining"], 10)
        self.assertFalse(result["rakan_pembangun"])


if __name__ == '__main__':
    unittest.main()
