import sqlite3
import unittest

from web_v1_bot_pairing_bridge import confirm_web_pairing_from_bot_update
from web_v1_pairing_challenges import new_pairing_challenge
from web_v1_pairing_store import initialize_pairing_store, register_pairing, consume_pairing


class BotPairingBridgeTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        initialize_pairing_store(self.db)
        self.token, self.digest, expiry = new_pairing_challenge(now=1000)
        register_pairing(self.db, self.digest, expiry)

    def tearDown(self):
        self.db.close()

    def message(self, **changes):
        value = {"from": {"id": 123}, "chat": {"id": 123, "type": "private"},
                 "text": "/start web_" + self.token}
        value.update(changes)
        return value

    def test_private_authenticated_update_confirms_once(self):
        self.assertTrue(confirm_web_pairing_from_bot_update(self.db, self.message(), now=1001))
        self.assertFalse(confirm_web_pairing_from_bot_update(self.db, self.message(), now=1002))
        self.assertEqual(consume_pairing(self.db, self.digest, now=1003), 123)

    def test_group_and_wrong_sender_rejected(self):
        self.assertFalse(confirm_web_pairing_from_bot_update(
            self.db, self.message(chat={"id": -100, "type": "supergroup"}), now=1001))
        self.assertFalse(confirm_web_pairing_from_bot_update(
            self.db, self.message(chat={"id": 999, "type": "private"}), now=1001))

    def test_untrusted_or_malformed_payload_rejected(self):
        self.assertFalse(confirm_web_pairing_from_bot_update(self.db, self.message(text="/start hello"), now=1001))
        self.assertFalse(confirm_web_pairing_from_bot_update(
            self.db, self.message(**{"from": {"id": True}}), now=1001))
        self.assertFalse(confirm_web_pairing_from_bot_update(
            self.db, self.message(text="/start@OtherBot web_" + self.token),
            expected_bot_username="CikguLajuBot", now=1001))

    def test_expired_challenge_rejected(self):
        self.assertFalse(confirm_web_pairing_from_bot_update(self.db, self.message(), now=2000))


if __name__ == "__main__":
    unittest.main()
