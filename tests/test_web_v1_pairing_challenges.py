import unittest

from web_v1_pairing_challenges import (
    challenge_storage_key, new_pairing_challenge, valid_pairing_confirmation,
)


class PairingChallengeTests(unittest.TestCase):
    def test_valid_short_lived_challenge(self):
        token, digest, expires = new_pairing_challenge(now=1000)
        self.assertEqual(expires, 1180)
        self.assertNotEqual(token, digest)
        self.assertEqual(challenge_storage_key(token), digest)
        self.assertTrue(valid_pairing_confirmation(token, digest, expires, 123, now=1000))

    def test_expiry_and_wrong_token_rejected(self):
        token, digest, expires = new_pairing_challenge(now=1000)
        self.assertFalse(valid_pairing_confirmation(token, digest, expires, 123, now=expires))
        other, _, _ = new_pairing_challenge(now=1000)
        self.assertFalse(valid_pairing_confirmation(other, digest, expires, 123, now=1001))

    def test_malformed_and_unauthenticated_rejected(self):
        token, digest, expires = new_pairing_challenge(now=1000)
        self.assertFalse(valid_pairing_confirmation("invalid!", digest, expires, 123, now=1000))
        self.assertFalse(valid_pairing_confirmation(token, digest, expires, 0, now=1000))
        self.assertFalse(valid_pairing_confirmation(token, digest, expires, True, now=1000))
        self.assertIsNone(challenge_storage_key(None))

    def test_lifetime_limits(self):
        for ttl in (0, 29, 301, True):
            with self.subTest(ttl=ttl):
                with self.assertRaises(ValueError):
                    new_pairing_challenge(now=1000, ttl_seconds=ttl)


if __name__ == "__main__":
    unittest.main()
