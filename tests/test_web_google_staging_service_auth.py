"""Validate Supabase's new sb_secret API key vs legacy JWT authorization."""

import unittest
from web.google_staging_service_auth import staging_service_headers


class SupabaseServiceHeaderTests(unittest.TestCase):
    def test_new_secret_key_never_sent_as_bearer(self):
        secret = "sb_secret_" + "x" * 40
        headers = staging_service_headers(secret)
        self.assertEqual(headers["apikey"], secret)
        self.assertNotIn("Authorization", headers)
        self.assertEqual(headers["Accept"], "application/json")

    def test_legacy_service_role_jwt_sent_as_bearer(self):
        legacy = "eyJhbGciOiJIUzI1NiJ9." + "e30." + "x" * 43
        headers = staging_service_headers(legacy)
        self.assertEqual(headers["apikey"], legacy)
        self.assertEqual(headers["Authorization"], "Bearer " + legacy)

    def test_public_key_cannot_authorize_privileged_requests(self):
        with self.assertRaises(ValueError):
            staging_service_headers("sb_publishable_" + "x" * 40)

    def test_empty_short_key_rejected(self):
        for key in ("", "not-a-key", None, 123):
            with self.subTest(key=key), self.assertRaises(ValueError):
                staging_service_headers(key)


if __name__ == "__main__":
    unittest.main()
