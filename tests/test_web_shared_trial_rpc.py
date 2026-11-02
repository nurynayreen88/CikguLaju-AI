"""Pure unit tests for the existing shared trial RPC adapter.

All network I/O is mocked; no production user balance is modified.
"""
import io
import json
import unittest
from unittest.mock import patch

from web.shared_trial_rpc import consume_successful_generation


class FakeResponse:
    def __init__(self, payload):
        self.stream = io.BytesIO(json.dumps(payload).encode("utf-8"))

    def __enter__(self):
        return self.stream

    def __exit__(self, *args):
        return False


class SharedTrialRPCTests(unittest.TestCase):
    def test_existing_rpc_contract(self):
        captured = {}

        def fake_open(req, timeout):
            captured["url"] = req.full_url
            captured["body"] = json.loads(req.data)
            captured["timeout"] = timeout
            return FakeResponse([{"ok": True, "remaining": 4}])

        with patch("web.shared_trial_rpc.urlopen", side_effect=fake_open):
            result = consume_successful_generation(
                "https://example.supabase.co", "server-only-key", 123,
                "web-rph:123e4567-e89b-42d3-a456-426614174000")
        self.assertEqual(result, {"ok": True, "remaining": 4})
        self.assertEqual(captured["url"], "https://example.supabase.co/rest/v1/rpc/cikgulaju_use_trial")
        self.assertEqual(captured["body"]["p_telegram_user_id"], 123)
        self.assertEqual(captured["body"]["p_reference_id"], "web-rph:123e4567-e89b-42d3-a456-426614174000")
        self.assertEqual(captured["timeout"], 8)

    def test_no_credit(self):
        with patch("web.shared_trial_rpc.urlopen",
                   return_value=FakeResponse([{"ok": False, "remaining": 0}])):
            result = consume_successful_generation(
                "https://example.supabase.co", "key", 123, "web-rph:123e4567-e89b-42d3-a456-426614174000")
        self.assertFalse(result["ok"])

    def test_invalid_input_never_calls_network(self):
        with patch("web.shared_trial_rpc.urlopen") as mocked:
            with self.assertRaises(ValueError):
                consume_successful_generation(
                    "https://example.supabase.co", "key", 123, "client-selected")
            mocked.assert_not_called()

    def test_invalid_response_fails_closed(self):
        with patch("web.shared_trial_rpc.urlopen",
                   return_value=FakeResponse([{"ok": "yes", "remaining": 4}])):
            with self.assertRaises(RuntimeError):
                consume_successful_generation(
                    "https://example.supabase.co", "key", 123, "web-rph:123e4567-e89b-42d3-a456-426614174000")


if __name__ == "__main__":
    unittest.main()
