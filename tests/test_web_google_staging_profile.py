"""Read-only staging Google account summary must not leak or forge identities."""
import json
import unittest
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from web.google_account_store import (
    google_staging_account_profile, GoogleAccountUnavailable,
)

UID = "2c2f5000-87e6-4e96-8200-676dc5ef1c19"
CONF = {"supabase_url": "https://abcdefghijklmnopqrst.supabase.co",
        "staging_service_key": "independent-staging-only-service-key"}


class FakeResponse:
    def __init__(self, data, status=200):
        self.data = json.dumps(data).encode()
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _max_size):
        return self.data


class GoogleStagingProfileTest(unittest.TestCase):
    def test_signed_account_is_only_lookup_key(self):
        rows = [{"id": UID, "display_name": "Cikgu Ujian",
                 "google_trial_remaining": 10}]
        with patch("web.google_account_store.urlopen",
                   return_value=FakeResponse(rows)) as read:
            value = google_staging_account_profile(CONF, UID)
        self.assertEqual(value["trial_remaining"], 10)
        self.assertEqual(value["display_name"], "Cikgu Ujian")
        called_url = read.call_args.args[0].full_url
        parsed = urlsplit(called_url)
        self.assertEqual(parsed.netloc, "abcdefghijklmnopqrst.supabase.co")
        self.assertEqual(parse_qs(parsed.query)["id"], ["eq." + UID])
        self.assertNotIn("email", called_url)
        self.assertNotIn("telegram_user_id", called_url)

    def test_forged_ids_never_read_db(self):
        for invalid in ("teacher@example.com", UID.upper(), "invalid", "", None):
            with self.subTest(value=invalid):
                with patch("web.google_account_store.urlopen") as read:
                    with self.assertRaises(GoogleAccountUnavailable):
                        google_staging_account_profile(CONF, invalid)
                    read.assert_not_called()

    def test_no_service_key_denies_profile(self):
        with patch("web.google_account_store.urlopen") as read:
            with self.assertRaises(GoogleAccountUnavailable):
                google_staging_account_profile(
                    {"supabase_url": CONF["supabase_url"],
                     "staging_service_key": ""}, UID)
            read.assert_not_called()

    def test_account_mismatch_or_bad_credits_denied(self):
        bad_records = [
            [], [{"id": "11111111-1111-4111-8111-111111111111",
                  "display_name": "Wrong", "google_trial_remaining": 10}],
            [{"id": UID, "display_name": "Cikgu", "google_trial_remaining": 11}],
            [{"id": UID, "display_name": "Cikgu", "google_trial_remaining": -1}],
            [{"id": UID, "display_name": "Cikgu", "google_trial_remaining": "10"}],
            [{"id": UID, "display_name": "Cikgu", "google_trial_remaining": True}],
        ]
        for row in bad_records:
            with self.subTest(row=row), patch(
                    "web.google_account_store.urlopen",
                    return_value=FakeResponse(row)):
                with self.assertRaises(GoogleAccountUnavailable):
                    google_staging_account_profile(CONF, UID)

    def test_profile_does_not_mutate_db(self):
        with patch("web.google_account_store.urlopen", return_value=FakeResponse(
                [{"id": UID, "display_name": None, "google_trial_remaining": 0}])) as read:
            data = google_staging_account_profile(CONF, UID)
        self.assertEqual(data, {"display_name": "Guru CikguLaju",
                                "trial_remaining": 0})
        self.assertEqual(read.call_args.args[0].get_method(), "GET")


if __name__ == "__main__":
    unittest.main()
