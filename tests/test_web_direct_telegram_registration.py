"""Direct Web signup: verified identity only, no duplicate trials or account resets."""
import unittest
from unittest.mock import patch
from web.direct_telegram_registration import ensure_verified_web_user

CONF = {"account_backend": "supabase", "supabase_url": "https://example.supabase.co",
        "supabase_key": "test-server-key-which-never-goes-to-browser"}


class WebDirectSignupTests(unittest.TestCase):
    @patch("web.direct_telegram_registration._rest")
    def test_new_account_uses_server_verified_id_and_database_trial_default(self, rest):
        rest.side_effect = [[{"telegram_user_id": 24680}], []]
        created = ensure_verified_web_user(CONF, 24680, {
            "id": 99999, "first_name": "Guru", "username": "cikgu"
        })
        self.assertTrue(created)
        args, kwargs = rest.call_args_list[0]
        self.assertEqual(args[:3], (CONF, "POST", "cikgulaju_users"))
        self.assertEqual(kwargs["payload"]["telegram_user_id"], 24680)
        self.assertNotIn("trial_remaining", kwargs["payload"])
        self.assertNotIn("credits", kwargs["payload"])
        self.assertIn("ignore-duplicates", kwargs["prefer"])
        self.assertEqual(rest.call_args_list[1].args[2], "web_direct_signups")

    @patch("web.direct_telegram_registration._rest", return_value=[])
    def test_existing_account_is_not_overwritten_or_recredited(self, rest):
        self.assertFalse(ensure_verified_web_user(CONF, 24680, {"first_name": "Updated"}))
        self.assertEqual(rest.call_count, 1)

    @patch("web.direct_telegram_registration._rest")
    def test_invalid_verified_id_never_calls_backend(self, rest):
        with self.assertRaises(ValueError):
            ensure_verified_web_user(CONF, 0, {})
        rest.assert_not_called()

    @patch("web.direct_telegram_registration._rest")
    def test_non_supabase_account_backend_is_never_created(self, rest):
        with self.assertRaises(RuntimeError):
            ensure_verified_web_user({"account_backend": "sqlite"}, 24680, {})
        rest.assert_not_called()


if __name__ == "__main__":
    unittest.main()
