"""No external services or real credits used by these unit tests."""
import unittest
from web.rph_delivery_quota import charge_rendered_rph


class DeliveryQuotaTests(unittest.TestCase):
    def test_successful_render_charges_once_with_uuid4_reference(self):
        calls = []
        def debit(url, key, uid, reference):
            calls.append((uid, reference))
            return {"ok": True, "remaining": 3}
        result = charge_rendered_rph(123, b"docx bytes", "https://db", "key", debit=debit)
        self.assertTrue(result["allowed"])
        self.assertEqual(result["remaining"], 3)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], 123)
        self.assertTrue(calls[0][1].startswith("web-rph:"))
        self.assertEqual(calls[0][1], result["reference"])

    def test_empty_render_never_charges(self):
        calls = []
        with self.assertRaises(ValueError):
            charge_rendered_rph(123, b"", "https://db", "key",
                                debit=lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_exhausted_trial_never_allows_download(self):
        result = charge_rendered_rph(
            123, b"document", "https://db", "key",
            debit=lambda *args: {"ok": False, "remaining": 0})
        self.assertEqual(result, {"allowed": False, "remaining": 0, "reference": None})


if __name__ == "__main__":
    unittest.main()
