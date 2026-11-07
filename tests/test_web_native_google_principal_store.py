"""Canonical Google and Telegram identities share one production account source.

All fixtures are fake: no connection to production or staging Supabase.
"""
import json
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from web_v1_canonical_sessions import (
    issue_google_principal_ticket, verify_google_principal_ticket,
)
from web_v1_sessions import verify_session_ticket
from web.native_google_principal_store import (
    PROD_SUPABASE, CanonicalAccountUnavailable,
    register_verified_google_principal, read_google_principal,
    canonical_rph_access,
)

UUID = "1a267083-8511-4587-a585-857fe35f4a14"
GOOGLE_SUBJECT = "2c2f5000-87e6-4e96-8200-676dc5ef1c19"
EMAIL = "teacher@example.com"
SECRET = "strong-isolated-uuid-session-secret-32-chars-minimum"
CFG = {"supabase_url": PROD_SUPABASE,
       "supabase_key": "sb_secret_test_only_private_key_32_characters"}
VERIFIED_IDENTITY = {
    "id": GOOGLE_SUBJECT, "email": "Teacher@Example.com",
    "email_confirmed_at": "2026-11-07T10:00:00Z",
    "identities": [{
        "provider": "google", "identity_data": {"email": "Teacher@Example.com"}
    }],
}


class Response:
    status = 200
    def __init__(self, body):
        self.payload = json.dumps(body).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, n):
        return self.payload[:n]


class CanonicalGooglePrincipalTests(unittest.TestCase):
    def test_google_ticket_is_not_legacy_telegram_session(self):
        ticket = issue_google_principal_ticket(UUID, SECRET, now=1000)
        self.assertEqual(verify_google_principal_ticket(ticket, SECRET, now=1200), UUID)
        self.assertIsNone(verify_session_ticket(ticket, SECRET, now=1200))
        self.assertIsNone(verify_google_principal_ticket(ticket, SECRET, now=44201))
        # Always change the signature byte. A random ticket can already end
        # with "a", making a fixed replacement a flaky no-op.
        changed = "a" if ticket[-1] != "a" else "b"
        self.assertIsNone(verify_google_principal_ticket(
            ticket[:-1] + changed, SECRET, now=1100))
        self.assertIsNone(verify_google_principal_ticket(ticket, SECRET+"wrong", now=1100))
        self.assertIsNone(verify_google_principal_ticket(ticket, SECRET, now=999))
        with self.assertRaises(ValueError):
            issue_google_principal_ticket(EMAIL, SECRET)

    def test_google_only_creates_uuid_principal_in_same_production_database(self):
        with patch("web.native_google_principal_store.urlopen",
                   return_value=Response(UUID)) as opener:
            pid = register_verified_google_principal(CFG, VERIFIED_IDENTITY)
        self.assertEqual(pid, UUID)
        req = opener.call_args.args[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.full_url,
                         PROD_SUPABASE+"/rest/v1/rpc/ensure_native_google_web_principal")
        self.assertEqual(json.loads(req.data), {
            "p_auth_subject": GOOGLE_SUBJECT, "p_verified_email": EMAIL,
        })
        self.assertNotIn("telegram_user_id", json.loads(req.data))
        self.assertNotIn("Authorization", dict(req.header_items()))
        self.assertIn("apikey", dict((x.lower(), y) for x,y in req.header_items()))

    def test_unverified_email_never_calls_account_rpc(self):
        for bad in (
            {**VERIFIED_IDENTITY, "email_confirmed_at": None},
            {**VERIFIED_IDENTITY, "email": "hijack@example.com"},
            {**VERIFIED_IDENTITY, "id": "bad-id"},
            {**VERIFIED_IDENTITY, "identities": [{"provider":"email"}]},
        ):
            with self.subTest(bad=bad), patch(
                    "web.native_google_principal_store.urlopen") as opener:
                with self.assertRaises(CanonicalAccountUnavailable):
                    register_verified_google_principal(CFG, bad)
                opener.assert_not_called()

    def test_staging_is_never_accepted_as_live_account_source(self):
        wrong = {**CFG, "supabase_url":
                 "https://eqrcjlnvcytkgazptbor.supabase.co"}
        with patch("web.native_google_principal_store.urlopen") as opener:
            with self.assertRaises(CanonicalAccountUnavailable):
                register_verified_google_principal(wrong, VERIFIED_IDENTITY)
            opener.assert_not_called()

    def test_google_principal_read_must_match_private_identity_binding(self):
        principal = {"id": UUID, "google_login_email":EMAIL,
                     "legacy_telegram_user_id": None,
                     "google_only_trial_remaining": 10}
        proof = {"principal_id":UUID,"auth_subject":GOOGLE_SUBJECT}
        with patch("web.native_google_principal_store.urlopen",
                   side_effect=[Response([principal]), Response([proof])]) as opener:
            result = read_google_principal(CFG, UUID)
        self.assertEqual(result["account_id"], UUID)
        self.assertEqual(result["login_id"], EMAIL)
        self.assertIsNone(result["legacy_telegram_user_id"])
        self.assertEqual(result["google_only_trial_remaining"], 10)
        calls = opener.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertIn("id=eq.", calls[0].args[0].full_url)
        self.assertIn("principal_id=eq.", calls[1].args[0].full_url)

        for invalid in ([], [{"principal_id":GOOGLE_SUBJECT,"auth_subject":GOOGLE_SUBJECT}]):
            with self.subTest(proof=invalid), patch(
                    "web.native_google_principal_store.urlopen",
                    side_effect=[Response([principal]), Response(invalid)]):
                with self.assertRaises(CanonicalAccountUnavailable):
                    read_google_principal(CFG, UUID)

    def test_google_only_trial_never_calls_telegram(self):
        p = {"account_id":UUID, "legacy_telegram_user_id":None,
             "google_only_trial_remaining":8}
        with patch("web_v1_supabase_account_adapter.lookup_existing_supabase_account") as legacy:
            result = canonical_rph_access(CFG, p)
            self.assertEqual(result["rph_access_mode"], "trial")
            self.assertEqual(result["rph_trial_remaining"], 8)
            legacy.assert_not_called()

    def test_linked_telegram_reads_only_original_prod_quota_and_entitlements(self):
        p = {"account_id":UUID, "legacy_telegram_user_id":123456789,
             "google_only_trial_remaining":None}
        acc = {"authenticated":True,"telegram_user_id":123456789,
               "rakan_pembangun":True,"free_remaining":8}
        with (patch("web_v1_supabase_account_adapter.lookup_existing_supabase_account",
                    return_value=acc) as lookup,
              patch("web.english_rpt_2027_http._has_paid_access",
                    return_value=True) as paid):
            result=canonical_rph_access(CFG,p)
        self.assertEqual(result["rph_access_mode"],"paid")
        self.assertEqual(result["rph_trial_remaining"],8)
        lookup.assert_called_once_with(PROD_SUPABASE,CFG["supabase_key"],123456789)
        paid.assert_called_once_with(acc)

    def test_linked_identity_credits_cannot_be_forged(self):
        p = {"account_id":UUID,"legacy_telegram_user_id":123456789,
             "google_only_trial_remaining":None}
        with patch("web_v1_supabase_account_adapter.lookup_existing_supabase_account",
                   return_value={"authenticated":True,"telegram_user_id":999,
                                 "free_remaining":10}):
            with self.assertRaises(CanonicalAccountUnavailable):
                canonical_rph_access(CFG,p)


if __name__ == "__main__":
    unittest.main()
