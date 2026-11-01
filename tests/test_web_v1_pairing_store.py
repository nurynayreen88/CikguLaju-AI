import sqlite3
import unittest

from web_v1_pairing_challenges import new_pairing_challenge
from web_v1_pairing_store import (
    initialize_pairing_store, register_pairing, confirm_pairing, consume_pairing,
)


class PairingStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        initialize_pairing_store(self.db)
        self.token, self.digest, self.expires = new_pairing_challenge(now=1000)
        register_pairing(self.db, self.digest, self.expires)

    def tearDown(self):
        self.db.close()

    def test_confirm_once_consume_once(self):
        self.assertTrue(confirm_pairing(self.db, self.token, 123, now=1001))
        self.assertFalse(confirm_pairing(self.db, self.token, 456, now=1001))
        self.assertEqual(consume_pairing(self.db, self.digest, now=1002), 123)
        self.assertIsNone(consume_pairing(self.db, self.digest, now=1002))

    def test_cannot_consume_unconfirmed(self):
        self.assertIsNone(consume_pairing(self.db, self.digest, now=1001))

    def test_expired_pairing_cannot_confirm_or_consume(self):
        self.assertFalse(confirm_pairing(self.db, self.token, 123, now=self.expires))
        self.assertIsNone(consume_pairing(self.db, self.digest, now=self.expires))

    def test_invalid_telegram_identity_rejected(self):
        self.assertFalse(confirm_pairing(self.db, self.token, True, now=1001))
        self.assertFalse(confirm_pairing(self.db, self.token, 0, now=1001))


if __name__ == "__main__":
    unittest.main()
