import unittest
from pioneer_supabase import has_pioneer, grant_pioneer, effective_access, pioneer_availability

class PioneerSupabaseTests(unittest.TestCase):
    def test_lifetime_access(self):
        def request(method, path, **kwargs):
            return [{"entitlement":"PIONEER_LIFETIME"}] if "telegram_user_id" in path else 0
        result = effective_access(request, 42, {"active":False})
        self.assertTrue(result["active"])
        self.assertIsNone(result["access_until"])

    def test_unsubscribed_unchanged(self):
        original = {"active":False}
        def request(method, path, **kwargs): return []
        self.assertIs(effective_access(request, 42, original), original)

    def test_verification_required(self):
        with self.assertRaises(ValueError):
            grant_pioneer(lambda *a, **k: None, 42, "ref", 7, False)

    def test_atomic_rpc(self):
        calls = []
        def request(method, path, **kwargs):
            calls.append((method,path,kwargs))
            return {"approved":True,"count":1,"remaining":499}
        grant_pioneer(request, 42, "ref", 7, True)
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][1],"rpc/approve_pioneer_early_bird")
        self.assertEqual(calls[0][2]["json"]["p_telegram_user_id"],42)

    def test_quota(self):
        def request(method, path, **kwargs): return 499
        self.assertEqual(pioneer_availability(request),(499,1))

    def test_count_failure_closed(self):
        with self.assertRaises(RuntimeError):
            pioneer_availability(lambda *a, **k: [])

if __name__ == "__main__":
    unittest.main()
