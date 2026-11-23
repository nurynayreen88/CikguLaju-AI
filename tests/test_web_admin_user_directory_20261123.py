"""Read-only admin directory: authorization, privacy, filters and email login ledger."""
import json
import os
import unittest
from unittest.mock import patch
from flask import Flask
from pathlib import Path

from web.admin_users_web import bp, _admin_users_data

CONF = {
    "account_backend": "supabase",
    "CIKGULAJU_WEB_SESSION_SECRET": "test-only-session-secret-with-at-least-32-chars",
    "supabase_url": "https://unit.supabase.co",
    "supabase_key": "sb_secret_server-test-not-live-000000000000",
}
UID = 901
EMAIL_ID = 8000000000000000003
SAMPLE = {
    "page": 0, "page_size": 20, "total": 2,
    "items": [
        {"account_type": "email", "telegram_id": None,
         "email": "example@teacher.test", "display_name": "Pengguna E-mel",
         "registered_at": "2026-11-22T12:10:00+00:00",
         "last_login_at": "2026-11-22T14:00:00+00:00",
         "access_status": "rakan", "subscription_expires_at": None,
         "trial_remaining": 10, "chat_user_id": str(EMAIL_ID),
         "telegram_user_id": EMAIL_ID, "auth_user_id": "secret"},
        {"account_type": "telegram", "telegram_id": "712",
         "email": None, "display_name": "Cikgu Contoh",
         "registered_at": "2026-11-20T12:10:00+00:00",
         "last_login_at": None,
         "access_status": "free", "subscription_expires_at": None,
         "trial_remaining": 8, "chat_user_id": "712",
         "telegram_user_id": 712, "internal_note": "never-send"},
    ]
}


class FakeReply:
    status = 200
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n): return json.dumps(self.payload).encode("utf-8")


class FakeOpener:
    def __init__(self, payload=SAMPLE): self.payload = payload; self.requests = []
    def open(self, req, timeout):
        self.requests.append((req, timeout))
        return FakeReply(self.payload)


class UserDirectoryTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(bp)
        self.client = app.test_client()
        self.allowlist = patch.dict(os.environ, {"CIKGULAJU_WEB_ADMIN_IDS": str(UID)})
        self.allowlist.start()
        self.addCleanup(self.allowlist.stop)
        self.config = patch("web.admin_users_web._config", return_value=CONF)
        self.config.start()
        self.addCleanup(self.config.stop)

    def test_opaque_secret_rpc_uses_exclusive_database_acl_not_missing_jwt_guc(self):
        """Modern sb_secret_ calls do not populate request.jwt.claim.role."""
        migration = Path(__file__).resolve().parents[1] / (
            "supabase/migrations/20261123_fix_admin_user_directory_opaque_key_403.sql"
        )
        sql = migration.read_text(encoding="utf-8")
        self.assertIn("SECURITY DEFINER", sql)
        self.assertIn("REVOKE ALL ON FUNCTION public.admin_user_directory", sql)
        self.assertIn("FROM PUBLIC, anon, authenticated", sql)
        self.assertIn("GRANT EXECUTE ON FUNCTION public.admin_user_directory", sql)
        self.assertIn("TO service_role", sql)
        self.assertNotIn("IF current_setting('request.jwt.claim.role'", sql)
        self.assertIn("LIMIT 20 OFFSET (p_page * 20)", sql)
        self.assertNotIn("EXECUTE format(", sql)

    def test_anonymous_and_non_admin_never_query_directory(self):
        with patch("web.admin_users_web.verify_session_ticket", return_value=None), \
             patch("web.admin_users_web._admin_users_data") as data:
            reply = self.client.get("/api/web/admin/users")
        self.assertEqual(reply.status_code, 401)
        data.assert_not_called()
        with patch("web.admin_users_web.verify_session_ticket", return_value=902), \
             patch("web.admin_users_web._admin_users_data") as data:
            reply = self.client.get("/api/web/admin/users")
        self.assertEqual(reply.status_code, 403)
        data.assert_not_called()
        self.assertNotIn("example@teacher.test", reply.get_data(as_text=True))

    def test_admin_must_still_have_authoritative_account(self):
        with patch("web.admin_users_web.verify_session_ticket", return_value=UID), \
             patch("web.admin_users_web._lookup", return_value=None), \
             patch("web.admin_users_web._admin_users_data") as data:
            reply = self.client.get("/api/web/admin/users")
        self.assertEqual(reply.status_code, 403)
        data.assert_not_called()

    def test_strict_filters_fail_before_any_private_lookup(self):
        bad = [
            "status=admin", "status=free&status=rakan", "page=-1",
            "page=100001", "page=1.5", "page=0&extra=1",
            "search=" + ("a" * 101), "search=%0Abad",
        ]
        with patch("web.admin_users_web.verify_session_ticket", return_value=UID), \
             patch("web.admin_users_web._lookup") as lookup, \
             patch("web.admin_users_web._admin_users_data") as data:
            for args in bad:
                with self.subTest(args=args):
                    response = self.client.get("/api/web/admin/users?" + args)
                    self.assertEqual(response.status_code, 400, response.json)
        lookup.assert_not_called()
        data.assert_not_called()

    def test_private_admin_query_uses_server_side_status_search_page(self):
        with patch("web.admin_users_web.verify_session_ticket", return_value=UID), \
             patch("web.admin_users_web._lookup", return_value={"telegram_user_id": UID}), \
             patch("web.admin_users_web._admin_users_data", return_value={
                 "items": SAMPLE["items"][:1], "total": 1, "page": 1,
                 "page_size": 20, "more": False
             }) as source:
            reply = self.client.get("/api/web/admin/users?status=rakan&search=teacher&page=1")
        self.assertEqual(reply.status_code, 200, reply.json)
        source.assert_called_once_with(CONF, "rakan", "teacher", 1)
        self.assertIn("no-store", reply.headers["Cache-Control"])
        self.assertEqual(reply.json["total"], 1)

    def test_rpc_is_server_only_and_scrubs_internal_ids(self):
        opener = FakeOpener()
        result = _admin_users_data(CONF, "free", "Cikgu", 0, opener=opener)
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["items"]), 2)
        self.assertNotIn("telegram_user_id", str(result))
        self.assertNotIn("auth_user_id", str(result))
        self.assertEqual(result["items"][0]["chat_user_id"], str(EMAIL_ID))
        self.assertEqual(result["items"][1]["chat_user_id"], "712")
        self.assertEqual(result["items"][0]["email"], "example@teacher.test")
        self.assertIsNone(result["items"][1]["last_login_at"])
        req, timeout = opener.requests[0]
        self.assertEqual(req.full_url, "https://unit.supabase.co/rest/v1/rpc/admin_user_directory")
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(json.loads(req.data), {
            "p_status": "free", "p_search": "Cikgu", "p_page": 0,
        })
        self.assertEqual(req.get_header("Apikey"), CONF["supabase_key"])
        self.assertIsNone(req.get_header("Authorization"))
        self.assertEqual(timeout, 12)

    def test_invalid_rpc_reply_fails_closed(self):
        with self.assertRaises(RuntimeError):
            _admin_users_data(CONF, "all", "", 0,
                              opener=FakeOpener({"items": [], "total": "67",
                                                 "page": 0, "page_size": 20}))

    def test_email_login_recorder_accepts_verified_synthetic_id(self):
        from web.web_login_analytics import record_verified_web_login
        opener = FakeOpener()
        self.assertTrue(record_verified_web_login(CONF, EMAIL_ID, opener=opener))
        self.assertEqual(json.loads(opener.requests[0][0].data),
                         {"telegram_user_id": EMAIL_ID, "source": "web"})
        with self.assertRaises(ValueError):
            record_verified_web_login(CONF, 2**63, opener=FakeOpener())


if __name__ == "__main__":
    unittest.main()
