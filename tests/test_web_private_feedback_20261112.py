"""Web comments: authorization, CSRF, Supabase reuse, no credit writes."""
from pathlib import Path
import unittest
from unittest.mock import patch

from flask import Flask

from web.web_feedback_routes import bp, _url_and_headers, FeedbackUnavailable


class PrivateWebFeedbackTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(bp)
        self.client = app.test_client()
        self.conf = {"account_backend": "supabase",
                     "supabase_url": "https://project.supabase.co",
                     "supabase_key": "s" * 40}

    def post(self, body, **kwargs):
        return self.client.post("/api/web/feedback", json=body,
                                headers={"Origin": "https://localhost", **kwargs})

    @patch("web.web_feedback_routes._auth")
    def test_must_login_and_match_registered_account(self, auth):
        auth.return_value = None, None, ({"error": "Sila log masuk"}, 401)
        # endpoint is invoked only after the identity gate
        response = self.post({"category": "Cadangan", "message": "Tolong lengkapkan RPT 2027"})
        self.assertEqual(response.status_code, 401)

    @patch("web.web_feedback_routes._auth")
    @patch("web.web_feedback_routes._db")
    def test_teacher_submits_only_own_verified_telegram_id(self, db, auth):
        auth.return_value = self.conf, 171435592, None
        db.side_effect = [[], [{"id": 44}]]
        response = self.post({"category": "Masalah RPT",
                              "message": "  RPT Sains Tahun 4 perlu halaman buku tepat  "})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json["ok"])
        self.assertEqual(db.call_count, 2)
        self.assertEqual(db.call_args.kwargs["payload"], {
            "chat_id": "171435592", "category": "Masalah RPT",
            "feedback_text": "RPT Sains Tahun 4 perlu halaman buku tepat",
        })
        self.assertEqual(response.headers.get("Cache-Control"), "no-store, private")

    @patch("web.web_feedback_routes._auth")
    @patch("web.web_feedback_routes._db")
    def test_browser_cannot_claim_another_user(self, db, auth):
        auth.return_value = self.conf, 25, None
        response = self.post({"category": "Umum", "message": "Saya ingin membantu",
                              "chat_id": "7777"})
        self.assertEqual(response.status_code, 400)
        db.assert_not_called()

    @patch("web.web_feedback_routes._auth")
    @patch("web.web_feedback_routes._db")
    def test_cross_site_requests_and_invalid_messages_rejected(self, db, auth):
        auth.return_value = self.conf, 25, None
        bad_origin = self.client.post("/api/web/feedback",
                                     json={"category": "Umum", "message": "Panjang cukup"})
        self.assertEqual(bad_origin.status_code, 403)
        for body in [
            {"category": "Umum", "message": "pendek"},
            {"category": "Umum", "message": "z" * 1501},
            {"category": "Akaun VIP", "message": "Masalah saya panjang"},
            {"category": "Umum", "message": 5},
        ]:
            self.assertEqual(self.post(body).status_code, 400)
        db.assert_not_called()

    @patch("web.web_feedback_routes._auth")
    @patch("web.web_feedback_routes._db")
    def test_feedback_rate_limit_is_server_enforced(self, db, auth):
        auth.return_value = self.conf, 25, None
        db.return_value = [{}, {}, {}]
        response = self.post({"category": "Umum", "message": "Saya ingin beri ulasan"})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(db.call_count, 1)

    @patch("web.web_feedback_routes._auth")
    @patch("web.web_feedback_routes._db")
    def test_my_history_scoped_to_cookie_id_and_no_other_identity(self, db, auth):
        auth.return_value = self.conf, 25, None
        db.return_value = [{
            "id": 1, "chat_id": "25", "feedback_text": "Komen selamat",
            "category": "Umum", "status": "baru",
            "created_at": "2026-11-12T02:00:00Z"
        }]
        response = self.client.get("/api/web/feedback")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(db.call_args.args[2]["chat_id"], "eq.25")
        self.assertNotIn("chat_id", response.json["items"][0])
        self.assertEqual(self.client.get("/api/web/feedback?chat_id=777").status_code, 400)

    @patch("web.web_feedback_routes._auth")
    @patch("web.web_feedback_routes.allowed_admin_ids")
    @patch("web.web_feedback_routes._db")
    def test_admin_list_never_exposes_other_feedback_to_teacher(self, db, admins, auth):
        auth.return_value = self.conf, 25, None
        admins.return_value = {1234}
        response = self.client.get("/api/web/admin/feedback")
        self.assertEqual(response.status_code, 403)
        db.assert_not_called()
        admins.return_value = {25}
        db.return_value = [{
            "id": 2, "chat_id": "7777", "feedback_text": "Contoh maklum balas",
            "category": "Cadangan", "status": "baru",
            "created_at": "2026-11-12T02:00:00Z",
        }]
        result = self.client.get("/api/web/admin/feedback")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json["items"][0]["chat_id"], "7777")
        self.assertEqual(db.call_args.args[2]["limit"], "50")

    @patch("web.web_feedback_routes._auth")
    @patch("web.web_feedback_routes.allowed_admin_ids")
    @patch("web.web_feedback_routes._db")
    def test_admin_can_update_only_status_in_telegram_shared_ledger(self, db, admins, auth):
        auth.return_value = self.conf, 25, None
        admins.return_value = {25}
        db.return_value = [{"id": 48, "status": "dibaca"}]
        response = self.client.patch(
            "/api/web/admin/feedback/48",
            json={"status": "dibaca"},
            headers={"Origin": "https://localhost"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"ok": True, "id": 48, "status": "dibaca"})
        self.assertEqual(db.call_args.args[1], "PATCH")
        self.assertEqual(db.call_args.args[2], {"id": "eq.48", "select": "id,status"})
        self.assertEqual(db.call_args.args[3], {"status": "dibaca"})
        self.assertEqual(response.headers.get("Cache-Control"), "no-store, private")

    @patch("web.web_feedback_routes._auth")
    @patch("web.web_feedback_routes.allowed_admin_ids")
    @patch("web.web_feedback_routes._db")
    def test_non_admin_cannot_change_status(self, db, admins, auth):
        auth.return_value = self.conf, 25, None
        admins.return_value = {100}
        response = self.client.patch(
            "/api/web/admin/feedback/48",
            json={"status": "selesai"},
            headers={"Origin": "https://localhost"},
        )
        self.assertEqual(response.status_code, 403)
        db.assert_not_called()

    @patch("web.web_feedback_routes._auth")
    @patch("web.web_feedback_routes.allowed_admin_ids")
    @patch("web.web_feedback_routes._db")
    def test_status_update_rejects_csrf_extra_fields_and_invalid_status(self, db, admins, auth):
        auth.return_value = self.conf, 25, None
        admins.return_value = {25}
        url = "/api/web/admin/feedback/48"
        payload = {"status": "selesai"}
        cases = [
            (url, payload, {}, 403),
            (url, {"status": "selesai", "chat_id": "9999"},
             {"Origin": "https://localhost"}, 400),
            (url, {"status": "padam"},
             {"Origin": "https://localhost"}, 400),
            (url, {"status": "SELESAI"},
             {"Origin": "https://localhost"}, 400),
            ("/api/web/admin/feedback/0", payload,
             {"Origin": "https://localhost"}, 400),
        ]
        for route, body, headers, expected in cases:
            with self.subTest(route=route, body=body):
                response = self.client.patch(route, json=body, headers=headers)
                self.assertEqual(response.status_code, expected)
        db.assert_not_called()

    @patch("web.web_feedback_routes._auth")
    @patch("web.web_feedback_routes.allowed_admin_ids")
    @patch("web.web_feedback_routes._db")
    def test_missing_or_unconfirmed_status_write_returns_failure(self, db, admins, auth):
        auth.return_value = self.conf, 25, None
        admins.return_value = {25}
        for returned, code in (([], 404), ([{"id": 48, "status": "baru"}], 503)):
            with self.subTest(returned=returned):
                db.return_value = returned
                result = self.client.patch(
                    "/api/web/admin/feedback/48",
                    json={"status": "selesai"},
                    headers={"Origin": "https://localhost"},
                )
                self.assertEqual(result.status_code, code)
                self.assertNotIn("ok", result.json)

    @patch("web.web_feedback_routes._auth")
    @patch("web.web_feedback_routes._db")
    def test_failed_database_write_must_never_show_success(self, db, auth):
        auth.return_value = self.conf, 25, None
        db.side_effect = [[], FeedbackUnavailable("connection refused")]
        response = self.post({"category": "Umum", "message": "Sambungan bermasalah"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("ok", response.json)

    def test_server_key_and_https_guard(self):
        url, headers = _url_and_headers(self.conf)
        self.assertEqual(url, "https://project.supabase.co/rest/v1/bot_user_feedback")
        self.assertEqual(headers["Authorization"], "Bearer " + "s" * 40)
        conf = dict(self.conf, supabase_url="http://insecure.example")
        with self.assertRaises(FeedbackUnavailable):
            _url_and_headers(conf)
        conf = dict(self.conf, supabase_key="sb_secret_" + "x" * 40)
        _, headers = _url_and_headers(conf)
        self.assertNotIn("Authorization", headers)

    def test_actual_ui_assets_registered_without_external_script(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "web_v1_static_preview/index.html").read_text("utf-8")
        js = (root / "web_v1_static_preview/web-feedback.js").read_text("utf-8")
        wsgi = (root / "tools/run_web_production.py").read_text("utf-8")
        for token in ('data-web-view="feedback"', 'id="view-feedback"',
                      'id="web-feedback-form"', 'id="web-feedback-admin-list"',
                      '/assets/web-feedback.js'):
            self.assertIn(token, html)
        self.assertIn("window.cikgulajuFeedbackLoad", js)
        self.assertIn("window.cikgulajuFeedbackAdminLoad", js)
        self.assertIn("Simpan Status", js)
        self.assertIn('method:"PATCH"', js)
        self.assertIn('credentials:"same-origin"', js)
        self.assertIn("app.register_blueprint(web_feedback_bp)", wsgi)
        self.assertNotIn("SUPABASE_SECRET_KEY", js)


if __name__ == "__main__":
    unittest.main()
