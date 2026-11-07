import unittest
from web.provider_neutral_payment import (
    verified_payment_actor, validate_payment_plan,
    can_resubmit_payment, payment_review_action,
)

ACCOUNT = "d77d02c0-06ca-41d4-875e-15b4efda6bb4"


class ProviderNeutralPaymentTests(unittest.TestCase):
    def test_google_user_requires_no_telegram_id(self):
        actor = verified_payment_actor(ACCOUNT, "google")
        self.assertEqual(actor.account_id, ACCOUNT)
        self.assertEqual(actor.provider, "google")

    def test_rejects_legacy_chat_id_and_unknown_provider(self):
        for account, provider in [("12345678", "telegram"), (ACCOUNT, "email"),
                                  ("", "google"), (ACCOUNT.upper(), "google")]:
            with self.assertRaises(ValueError):
                verified_payment_actor(account, provider)

    def test_price_is_approved_server_catalog_only(self):
        catalog = {"rakan_pembangun": {"enabled": True, "amount_sen": 1000},
                   "monthly": {"enabled": False, "amount_sen": 1000}}
        self.assertEqual(validate_payment_plan("rakan_pembangun", catalog),
                         ("rakan_pembangun", 1000))
        for code in ("monthly", "annual", "unknown"):
            with self.assertRaises(ValueError):
                validate_payment_plan(code, catalog)
        with self.assertRaises(ValueError):
            validate_payment_plan("rakan_pembangun",
                                  {"rakan_pembangun": {"enabled": True, "amount_sen": "1000"}})

    def test_rejected_receipt_can_be_resubmitted_not_overwritten(self):
        self.assertTrue(can_resubmit_payment("rejected"))
        self.assertTrue(can_resubmit_payment(None))
        self.assertFalse(can_resubmit_payment("pending"))
        self.assertFalse(can_resubmit_payment("approved"))

    def test_review_needs_verified_admin(self):
        for action in ("approve", "reject"):
            self.assertEqual(payment_review_action(action, admin_verified=True), action)
            with self.assertRaises(PermissionError):
                payment_review_action(action, admin_verified=False)
        with self.assertRaises(PermissionError):
            payment_review_action("approve_and_add_credits", admin_verified=True)


if __name__ == "__main__":
    unittest.main()
