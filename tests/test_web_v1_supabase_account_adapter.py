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


if __name__ == '__main__':
    unittest.main()
