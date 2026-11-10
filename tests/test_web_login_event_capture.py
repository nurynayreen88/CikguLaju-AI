"""No-network regression tests for verified-only Web login event capture."""
import json
import unittest
from web.web_login_analytics import record_verified_web_login, _NoRedirect


class FakeResponse:
    def __init__(self, status=201):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, status=201):
        self.status = status
        self.requests = []

    def open(self, req, timeout=None):
        self.requests.append((req, timeout))
        return FakeResponse(self.status)


def config(key=None):
    return {
        "account_backend": "supabase",
        "supabase_url": "https://example.supabase.co",
        "supabase_key": key or "x" * 40,
    }


class WebLoginEventTests(unittest.TestCase):
    def test_verified_web_login_persists_only_verified_id(self):
        opener = FakeOpener()
        self.assertTrue(record_verified_web_login(config(), 123456789, opener=opener))
        self.assertEqual(len(opener.requests), 1)
        req, timeout = opener.requests[0]
        self.assertEqual(req.full_url, "https://example.supabase.co/rest/v1/web_login_events")
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(json.loads(req.data), {"telegram_user_id": 123456789, "source": "web"})
        self.assertEqual(req.get_header("Authorization"), "Bearer " + "x" * 40)
        self.assertEqual(req.get_header("Prefer"), "return=minimal")
        self.assertEqual(timeout, 3)

    def test_opaque_supabase_secret_is_not_sent_as_bearer(self):
        opener = FakeOpener()
        key = "sb_secret_" + "x" * 40
        self.assertTrue(record_verified_web_login(config(key), 10, opener=opener))
        req = opener.requests[0][0]
        self.assertIsNone(req.get_header("Authorization"))
        self.assertEqual(req.get_header("Apikey"), key)

    def test_unverified_or_invalid_user_ids_never_trigger_network(self):
        for value in (None, "123", 0, -3, True, 10**18):
            opener = FakeOpener()
            with self.subTest(value=value), self.assertRaises(ValueError):
                record_verified_web_login(config(), value, opener=opener)
            self.assertEqual(opener.requests, [])

    def test_sqlite_mode_records_nothing(self):
        opener = FakeOpener()
        self.assertFalse(record_verified_web_login({"account_backend": "sqlite"}, 99, opener=opener))
        self.assertEqual(opener.requests, [])

    def test_non_https_or_untrusted_origin_rejected(self):
        for url in ("http://example.supabase.co", "https://user:pass@example.supabase.co",
                    "https://example.supabase.co/evil", "https://example.supabase.co?x=1",
                    "https://example.supabase.co:8443"):
            conf = config()
            conf["supabase_url"] = url
            opener = FakeOpener()
            with self.subTest(url=url), self.assertRaises(ValueError):
                record_verified_web_login(conf, 99, opener=opener)
            self.assertFalse(opener.requests)

    def test_backend_error_never_claims_success(self):
        with self.assertRaises(RuntimeError):
            record_verified_web_login(config(), 99, opener=FakeOpener(status=500))

    def test_redirects_are_blocked_before_credentials_follow_location(self):
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 302, "Found", {},
                                                         "https://example.org"))


if __name__ == "__main__":
    unittest.main()
