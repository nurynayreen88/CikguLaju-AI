"""No-network regression tests for private CikguLaju Web analytics."""
import json
import unittest
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from flask import Flask

from web import admin_usage_web as mod


class Response:
    def __init__(self, *, status=200, headers=None, body=b"[]"):
        self.status = status
        self.headers = headers or {}
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, n=-1):
        return self.body


class Opener:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append((request, timeout))
        return self.response


def conf(key="sb_secret_" + "x" * 40):
    return {"account_backend": "supabase",
            "supabase_url": "https://example.supabase.co",
            "supabase_key": key,
            "CIKGULAJU_WEB_SESSION_SECRET": "x" * 40}


NOW = datetime(2026, 11, 10, 23, 30, tzinfo=timezone.utc)
OLD = "2026-10-01T00:00:00+00:00"


class AdminAccessTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(mod.bp)
        app.testing = True
        self.client = app.test_client()

    def test_admin_ids_fail_closed_on_missing_or_bad_list(self):
        self.assertEqual(mod.allowed_admin_ids({}), set())
        for x in ("", "abc", "17, xyz", "0", "-5", "17,,19", " 017"):
            self.assertEqual(mod.allowed_admin_ids({"CIKGULAJU_WEB_ADMIN_IDS": x}), set())
        self.assertEqual(mod.allowed_admin_ids(
            {"CIKGULAJU_WEB_ADMIN_IDS": " 17 , 19 "}), {17, 19})

    def test_missing_session_is_401(self):
        with patch.object(mod, "_config", return_value=conf()), patch.object(
                mod, "verify_session_ticket", return_value=None):
            response = self.client.get("/api/web/admin/usage")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")

    def test_unlisted_registered_user_is_denied_without_query(self):
        with patch.object(mod, "_config", return_value=conf()), patch.object(
                mod, "verify_session_ticket", return_value=123), patch.object(
                mod, "allowed_admin_ids", return_value={99}), patch.object(
                mod, "_lookup") as lookup, patch.object(
                mod, "summarize_admin_usage") as summary:
            response = self.client.get("/api/web/admin/usage")
        self.assertEqual(response.status_code, 403)
        lookup.assert_not_called()
        summary.assert_not_called()

    def test_missing_admin_config_denies_everyone(self):
        with patch.object(mod, "_config", return_value=conf()), patch.object(
                mod, "verify_session_ticket", return_value=123), patch.object(
                mod, "allowed_admin_ids", return_value=set()):
            self.assertEqual(self.client.get("/api/web/admin/usage").status_code, 403)

    def test_listed_id_still_must_be_registered(self):
        with patch.object(mod, "_config", return_value=conf()), patch.object(
                mod, "verify_session_ticket", return_value=123), patch.object(
                mod, "allowed_admin_ids", return_value={123}), patch.object(
                mod, "_lookup", return_value=None), patch.object(
                mod, "summarize_admin_usage") as summary:
            res = self.client.get("/api/web/admin/usage")
        self.assertEqual(res.status_code, 403)
        summary.assert_not_called()

    def test_allowed_admin_gets_aggregate_without_user_ids(self):
        result = {
            "registered_users": 52, "rakan_pembangun": 9,
            "users_today": 3, "users_7d": 8, "users_30d": 14,
            "tracking_status": "partial_history",
            "trial_credit_debits": 7, "confirmed_rph_records": None,
        }
        with patch.object(mod, "_config", return_value=conf()), patch.object(
                mod, "verify_session_ticket", return_value=123), patch.object(
                mod, "allowed_admin_ids", return_value={123}), patch.object(
                mod, "_lookup", return_value={"telegram_user_id": 123}), patch.object(
                mod, "summarize_admin_usage", return_value=result):
            res = self.client.get("/api/web/admin/usage")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["registered_users"], 52)
        self.assertNotIn("telegram_user_id", res.get_data(as_text=True))
        self.assertEqual(res.headers.get("Vary"), "Cookie")

    def test_unexpected_query_rejected(self):
        self.assertEqual(self.client.get("/api/web/admin/usage?user=123").status_code, 400)


class StoredMetricsTests(unittest.TestCase):
    def test_supabase_count_is_head_only(self):
        opener = Opener(Response(status=206, headers={"Content-Range": "0-0/52"}))
        self.assertEqual(mod._fetch(conf(), "cikgulaju_users",
                                     {"select": "telegram_user_id", "limit": "1"},
                                     count=True, opener=opener), 52)
        req, timeout = opener.requests[0]
        self.assertEqual(req.get_method(), "HEAD")
        self.assertEqual(req.get_header("Apikey"), conf()["supabase_key"])
        self.assertIsNone(req.get_header("Authorization"))
        self.assertEqual(req.get_header("Prefer"), "count=exact")
        self.assertEqual(timeout, 8)

    def test_jwt_is_authorization_only_on_server(self):
        secret = "e" * 50
        opener = Opener(Response(status=200, body=b"[]"))
        mod._fetch(conf(secret), "web_login_events",
                   {"select": "logged_in_at", "limit": "1"}, opener=opener)
        self.assertEqual(opener.requests[0][0].get_header("Authorization"),
                         "Bearer " + secret)

    def test_untrusted_supabase_url_rejected(self):
        for url in ("http://test.com", "https://test.com/path",
                    "https://test.com?q=1", "https://x:y@test.com"):
            cfg = conf()
            cfg["supabase_url"] = url
            with self.subTest(url=url), self.assertRaises(RuntimeError):
                mod._api_config(cfg)

    def test_no_event_recording_reports_unknown_not_zero(self):
        with patch.object(mod, "_oldest_login", return_value=None):
            result = mod._login_metrics(conf(), NOW)
        self.assertIsNone(result["users_today"])
        self.assertIsNone(result["users_7d"])
        self.assertEqual(result["tracking_status"], "not_started")

    def test_unique_users_use_kuala_lumpur_day_and_rolling_windows(self):
        rows = [
            {"telegram_user_id": 1, "logged_in_at": "2026-11-10T15:59:00Z"},
            {"telegram_user_id": 1, "logged_in_at": "2026-11-10T18:00:00Z"},
            {"telegram_user_id": 1, "logged_in_at": "2026-11-10T19:00:00Z"},
            {"telegram_user_id": 2, "logged_in_at": "2026-11-10T20:00:00Z"},
        ]
        def fake(_conf, table, query, *, count=False, opener=None):
            self.assertEqual(table, "web_login_events")
            self.assertEqual(query.get("source"), "eq.web")
            if count:
                return len(rows)
            if query.get("select") == "telegram_user_id,logged_in_at":
                self.assertEqual(query.get("order"), "logged_in_at.asc,id.asc")
                return rows
            raise AssertionError("Unexpected API query")
        with patch.object(mod, "_oldest_login",
                          return_value=mod._parse_utc(OLD)), patch.object(
                          mod, "_fetch", side_effect=fake):
            result = mod._login_metrics(conf(), NOW)
        self.assertEqual(result["users_today"], 2)
        self.assertEqual(result["users_7d"], 2)
        self.assertEqual(result["users_30d"], 2)
        self.assertTrue(all(result["coverage"].values()))

    def test_partial_history_is_labelled(self):
        with patch.object(mod, "_oldest_login", return_value=NOW), patch.object(
                mod, "_fetch", return_value=0):
            result = mod._login_metrics(conf(), NOW)
        self.assertEqual(result["users_today"], 0)
        self.assertEqual(result["tracking_status"], "partial_history")
        self.assertFalse(result["coverage"]["last_30_days"])

    def test_event_limit_blocks_misleading_partial_count(self):
        with patch.object(mod, "_oldest_login", return_value=NOW), patch.object(
                mod, "_fetch", return_value=mod.MAX_LOGIN_EVENTS + 1):
            result = mod._login_metrics(conf(), NOW)
        self.assertIsNone(result["users_7d"])
        self.assertEqual(result["tracking_status"], "event_limit")

    def test_incomplete_page_is_rejected(self):
        with patch.object(mod, "_oldest_login", return_value=NOW), patch.object(
                mod, "_fetch", side_effect=[2, [{"telegram_user_id": 1,
                           "logged_in_at": "2026-11-10T20:00:00Z"}]]):
            with self.assertRaises(RuntimeError):
                mod._login_metrics(conf(), NOW)

    def test_summary_distinguishes_debit_and_partial_rph_data(self):
        def fake(_conf, table, query, *, count=False, opener=None):
            if table == "pioneer_entitlements":
                # Original lifetime entitlement values in Supabase are
                # uppercase PIONEER_LIFETIME; do not filter by lowercase only.
                self.assertEqual(query["revoked_at"], "is.null")
                self.assertNotIn("entitlement", query)
            return {"cikgulaju_users": 52, "pioneer_entitlements": 9,
                    "trial_ledger": 7, "admin_rph_deliveries": 0}[table]
        with patch.object(mod, "_fetch", side_effect=fake), patch.object(
                mod, "_login_metrics", return_value={
                    "users_today": None, "users_7d": None, "users_30d": None
                }):
            result = mod.summarize_admin_usage(conf(), now=NOW)
        self.assertEqual(result["registered_users"], 52)
        self.assertEqual(result["trial_credit_debits"], 7)
        self.assertIsNone(result["confirmed_rph_records"])
        self.assertEqual(result["rph_coverage"], "not_instrumented")


if __name__ == "__main__":
    unittest.main()
