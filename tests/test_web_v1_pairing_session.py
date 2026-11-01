import sqlite3
import unittest

from web_v1_browser_binding import create_browser_binding
from web_v1_pairing_challenges import new_pairing_challenge
from web_v1_pairing_store import initialize_pairing_store, register_pairing, confirm_pairing
from web_v1_pairing_session import finish_verified_pairing
from web_v1_sessions import verify_session_ticket


class PairingSessionTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        initialize_pairing_store(self.db)
        self.token, self.digest, self.expiry = new_pairing_challenge(now=1000)
        register_pairing(self.db, self.digest, self.expiry)
        self.secret = "isolated-test-secret-not-for-production-12345"
        self.browser_secret, self.browser_signature = create_browser_binding(self.digest, self.secret)

    def tearDown(self):
        self.db.close()

    def test_verified_account_gets_one_session_only(self):
        self.assertTrue(confirm_pairing(self.db, self.token, 123, now=1001))
        lookup = lambda uid: {"telegram_user_id": uid} if uid == 123 else None
        ticket = finish_verified_pairing(self.db, self.digest, self.browser_secret, self.browser_signature, self.secret, lookup, self.secret, now=1002)
        self.assertEqual(verify_session_ticket(ticket, self.secret, now=1003), 123)
        self.assertIsNone(finish_verified_pairing(self.db, self.digest, self.browser_secret, self.browser_signature, self.secret, lookup, self.secret, now=1003))

    def test_mismatched_browser_binding_cannot_consume(self):
        self.assertTrue(confirm_pairing(self.db, self.token, 123, now=1001))
        lookup = lambda uid: {"telegram_user_id": uid}
        self.assertIsNone(finish_verified_pairing(self.db, self.digest, "wrong", self.browser_signature, self.secret, lookup, self.secret, now=1002))
        self.assertIsNotNone(finish_verified_pairing(self.db, self.digest, self.browser_secret, self.browser_signature, self.secret, lookup, self.secret, now=1002))

    def test_unknown_account_is_rejected(self):
        self.assertTrue(confirm_pairing(self.db, self.token, 123, now=1001))
        self.assertIsNone(finish_verified_pairing(self.db, self.digest, self.browser_secret, self.browser_signature, self.secret, lambda uid: None, self.secret, now=1002))
        self.assertIsNone(finish_verified_pairing(self.db, self.digest, self.browser_secret, self.browser_signature, self.secret, lambda uid: {"telegram_user_id": uid}, self.secret, now=1003))


    def test_lookup_failure_consumes_challenge_and_fails_closed(self):
        self.assertTrue(confirm_pairing(self.db, self.token, 123, now=1001))
        def broken_lookup(uid):
            raise RuntimeError("database unavailable")
        self.assertIsNone(finish_verified_pairing(self.db, self.digest, self.browser_secret, self.browser_signature, self.secret, broken_lookup, self.secret, now=1002))
        self.assertIsNone(finish_verified_pairing(self.db, self.digest, self.browser_secret, self.browser_signature, self.secret, lambda uid: {"telegram_user_id": uid}, self.secret, now=1003))

    def test_boolean_identity_cannot_impersonate_numeric_id(self):
        self.assertTrue(confirm_pairing(self.db, self.token, 1, now=1001))
        self.assertIsNone(finish_verified_pairing(self.db, self.digest, self.browser_secret, self.browser_signature, self.secret, lambda uid: {"telegram_user_id": True}, self.secret, now=1002))


if __name__ == "__main__":
    unittest.main()
