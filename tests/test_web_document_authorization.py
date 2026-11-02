"""Verify that document authorization cannot bypass trial accounting."""
import unittest
from web.rph_delivery_quota import authorize_rendered_document


class DocumentAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def debit(url, key, uid, reference):
            self.calls.append((uid, reference))
            return {"ok": True, "remaining": 4}
        self.debit = debit
        self.account = {"authenticated": True, "telegram_user_id": 123,
                        "free_remaining": 5}

    def authorize(self, account=None, document=b"doc"):
        return authorize_rendered_document(
            self.account if account is None else account,
            123, document, "https://example.supabase.co", "secret", debit=self.debit)

    def test_free_user_charged_once(self):
        result = self.authorize()
        self.assertTrue(result["allowed"])
        self.assertEqual(result["remaining"], 4)
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(self.calls[0][1].startswith("web-rph:"))

    def test_lifetime_does_not_charge(self):
        result = self.authorize({**self.account, "rakan_pembangun": True})
        self.assertTrue(result["allowed"])
        self.assertEqual(self.calls, [])

    def test_no_credits_no_charge(self):
        result = self.authorize({**self.account, "free_remaining": 0})
        self.assertFalse(result["allowed"])
        self.assertEqual(self.calls, [])

    def test_wrong_identity_or_empty_document_rejected(self):
        for account, document in (({**self.account, "telegram_user_id": 999}, b"doc"),
                                  (self.account, b""),
                                  ({"authenticated": False, **{"telegram_user_id": 123}}, b"doc")):
            with self.subTest(account=account, document=document):
                with self.assertRaises(ValueError):
                    self.authorize(account, document)
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
