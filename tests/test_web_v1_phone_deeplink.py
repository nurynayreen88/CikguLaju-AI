import unittest

from web_v1_pairing_challenges import new_pairing_challenge
from web_v1_phone_deeplink import phone_pairing_link


class PhoneDeeplinkTests(unittest.TestCase):
    def test_link_opens_correct_bot_without_session_secret(self):
        token, digest, expiry = new_pairing_challenge(now=1000)
        url = phone_pairing_link("@CikguLajuBot", token)
        self.assertEqual(url, "https://t.me/CikguLajuBot?start=web_" + token)
        self.assertNotIn(digest, url)

    def test_bad_bot_name_rejected(self):
        token, _, _ = new_pairing_challenge(now=1000)
        for name in ("", "bad bot", "x", "bad/name", "https://evil.test"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                phone_pairing_link(name, token)

    def test_bad_challenge_rejected(self):
        with self.assertRaises(ValueError):
            phone_pairing_link("CikguLajuBot", "not-a-challenge")


if __name__ == "__main__":
    unittest.main()
