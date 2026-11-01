import unittest

from web_v1_browser_binding import create_browser_binding, verify_browser_binding


class BrowserBindingTests(unittest.TestCase):
    def setUp(self):
        self.hash = "a" * 64
        self.key = "isolated-signing-key-12345678901234567890"

    def test_correct_browser_can_prove_ownership(self):
        browser_secret, signature = create_browser_binding(self.hash, self.key)
        self.assertTrue(verify_browser_binding(self.hash, browser_secret, signature, self.key))

    def test_qr_token_alone_is_not_browser_proof(self):
        browser_secret, signature = create_browser_binding(self.hash, self.key)
        self.assertFalse(verify_browser_binding(self.hash, "wrong", signature, self.key))
        self.assertFalse(verify_browser_binding("b" * 64, browser_secret, signature, self.key))
        self.assertFalse(verify_browser_binding(self.hash, browser_secret, signature, "different-secret-12345678901234567890"))

    def test_each_browser_binding_is_unique(self):
        first, _ = create_browser_binding(self.hash, self.key)
        second, _ = create_browser_binding(self.hash, self.key)
        self.assertNotEqual(first, second)

    def test_invalid_signing_secret_rejected(self):
        with self.assertRaises(ValueError):
            create_browser_binding(self.hash, "short")


if __name__ == "__main__":
    unittest.main()
