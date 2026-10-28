import unittest

from rph_trial_reservations import reserve, commit, release


class FakeRPC:
    def __init__(self):
        self.calls = []

    def __call__(self, method, path, json):
        self.calls.append((method, path, json))
        name = path.split("/")[-1]
        if name.endswith("release_rph_trial"):
            return [{"ok": True, "reservation_status": "released"}]
        return [{"ok": True, "remaining": 4, "reservation_status": "committed" if "commit" in name else "reserved"}]


class ReservationClientTests(unittest.TestCase):
    def test_reserve(self):
        rpc = FakeRPC()
        result = reserve(rpc, 123, "rph-test-123")
        self.assertTrue(result.ok)
        self.assertEqual(result.remaining, 4)
        self.assertEqual(rpc.calls[0][1], "rpc/cikgulaju_reserve_rph_trial")
        self.assertEqual(rpc.calls[0][2]["p_request_id"], "rph-test-123")

    def test_commit(self):
        rpc = FakeRPC()
        self.assertEqual(commit(rpc, 123, "rph-test-123").status, "committed")

    def test_release(self):
        rpc = FakeRPC()
        self.assertEqual(release(rpc, 123, "rph-test-123").status, "released")

    def test_reject_short_id(self):
        with self.assertRaises(ValueError):
            reserve(FakeRPC(), 123, "short")

    def test_reject_malformed_response(self):
        with self.assertRaises(RuntimeError):
            reserve(lambda *a, **k: [], 123, "rph-test-123")


if __name__ == "__main__":
    unittest.main()
