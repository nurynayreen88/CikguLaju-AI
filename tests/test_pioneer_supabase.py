import unittest
from pioneer_supabase import has_pioneer, grant_pioneer, effective_access

class PioneerSupabaseTests(unittest.TestCase):
    def test_existing_subscription_unchanged(self):
        def request(method, path, **kwargs): return []
        original = {"active": False, "days_left": 0}
        self.assertIs(effective_access(request, 42, original), original)

    def test_lifetime_access(self):
        def request(method, path, **kwargs): return [{"entitlement": "PIONEER_LIFETIME"}]
        access = effective_access(request, 42, {"active": False, "access_until": "2020-01-01"})
        self.assertTrue(access["active"])
        self.assertEqual(access["status"], "pioneer")
        self.assertIsNone(access["access_until"])

    def test_admin_verification_required(self):
        with self.assertRaises(ValueError):
            grant_pioneer(lambda *a, **k: None, 42, "receipt-1", 7, False)

    def test_approved_grant(self):
        calls = []
        def request(method, path, **kwargs):
            calls.append((method, path, kwargs))
            return [{"entitlement": "PIONEER_LIFETIME"}]
        grant_pioneer(request, 42, "receipt-1", 7, True)
        self.assertEqual(calls[0][2]["json"]["approved_by"], 7)

if __name__ == "__main__":
    unittest.main()
