"""No-network tests for the invite-only admin referral points interface."""
import unittest
from unittest.mock import patch

from web.private_referral_admin_runtime import install


class Response:
    ok = True

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class FakeRuntime:
    API = "https://api.telegram.invalid/botTEST"

    def __init__(self):
        self.sent = []
        self.calls = []
        self.old_calls = []
        self.members = [{"referrer_user_id": 301, "enabled": True}]
        self.signups = [{"referred_user_id": 901}]
        self.events = [{"referred_user_id": 901, "points_delta": "2.00",
                        "payment_kind": "pioneer", "awarded_at": "2026-11-04T12:00:00Z"}]
        self.points = {"earned":12,"balance":2,"available":2,"reserved":0,"paid":10}

    def _is_admin(self, cid):
        return int(cid) == 1

    def _private_referral_member(self, cid):
        return self.members[0] if int(cid) == 301 else None

    def _sb_request(self, method, path, **kwargs):
        self.calls.append((method, path))
        if method == "POST" and path == "rpc/affiliate_point_summary":
            return [self.points]
        if method == "POST" and path == "rpc/affiliate_admin_members":
            return {"items":[{"user_id":"301","first_name":"Teacher","enabled":True,
                              "registered_count":1,"payment_count":1,**self.points}],"more":False}
        if method != "GET":
            raise AssertionError("Points view must be read-only")
        if path.startswith("referral_members?"):
            return self.members
        if path.startswith("referral_signups?"):
            return self.signups
        if path.startswith("referral_point_events?"):
            return self.events
        if path.startswith("cikgulaju_users?"):
            return [{"first_name": "Teacher", "username": "teacher_one"}]
        raise AssertionError("Unexpected database table")

    def send(self, cid, text, keyboard=None):
        self.sent.append((cid, text, keyboard))
        return Response({"ok": True, "result": {"message_id": 42,
              "reply_markup": {"inline_keyboard": keyboard or []}}})

    def _admin_panel(self, cid):
        return self.send(cid, "Existing Admin Panel", [
            [{"text": "Usage", "callback_data": "admin_usage_stats"}],
            [{"text": "System", "callback_data": "admin_system"}],
            [{"text": "Refresh", "callback_data": "admin_panel"}],
        ])

    def callback(self, cid, data):
        self.old_calls.append((cid, data))
        return "old_callback"


class TestReferralAdminPanel(unittest.TestCase):
    def test_admin_panel_contains_read_only_referral_button(self):
        rt = FakeRuntime()
        self.assertTrue(install(rt))
        with patch("web.private_referral_admin_runtime.requests.post") as post:
            post.return_value = Response({"ok": True})
            rt._admin_panel(1)
        keyboard = post.call_args.kwargs["json"]["reply_markup"]["inline_keyboard"]
        values = [b["callback_data"] for row in keyboard for b in row]
        self.assertEqual(values, [
            "admin_usage_stats", "admin_ref_points|list|0",
            "admin_system", "admin_panel",
        ])
        self.assertEqual(rt.sent[0][1], "Existing Admin Panel")

    def test_non_admin_cannot_open_points_list_or_member_details(self):
        rt = FakeRuntime()
        install(rt)
        rt.callback(2, "admin_ref_points|list|0")
        rt.callback(2, "admin_ref_points|detail|301")
        self.assertEqual(rt.calls, [])
        self.assertEqual(len(rt.sent), 2)
        self.assertTrue(all("admin" in msg.lower() for _, msg, _ in rt.sent))

    def test_admin_list_reports_signups_paid_points_and_detail(self):
        rt = FakeRuntime()
        install(rt)
        rt.callback(1, "admin_ref_points|list|0")
        cid, message, keyboard = rt.sent[-1]
        self.assertEqual(cid, 1)
        self.assertIn("Baki <b>2</b> mata", message)
        self.assertIn("Dibayar 10", message)
        self.assertIn("1 daftar", message)
        self.assertIn("1 bayaran", message)
        self.assertTrue(any(b.get("callback_data") == "admin_ref_points|detail|301"
                            for row in keyboard for b in row))
        rt.callback(1, "admin_ref_points|detail|301")
        detail = rt.sent[-1][1]
        self.assertIn("Teacher", detail)
        self.assertIn("+2 mata", detail)
        self.assertIn("Baki mata: <b>2</b>", detail)
        self.assertIn("Rakan Pembangun", detail)
        self.assertEqual([path for method, path in rt.calls if method != "GET"],
                         ["rpc/affiliate_admin_members", "rpc/affiliate_point_summary"])

    def test_non_referral_callbacks_preserve_existing_behavior(self):
        rt = FakeRuntime()
        install(rt)
        self.assertEqual(rt.callback(1, "admin_system"), "old_callback")
        self.assertEqual(rt.old_calls, [(1, "admin_system")])

    def test_disabled_member_still_visible_to_admin(self):
        rt = FakeRuntime()
        rt.members[0]["enabled"] = False
        install(rt)
        rt.callback(1, "admin_ref_points|detail|301")
        self.assertIn("DINYAH-AKTIFKAN", rt.sent[-1][1])

    def test_database_error_does_not_report_false_zero(self):
        rt = FakeRuntime()
        def unavailable(*args, **kwargs):
            raise RuntimeError("DB unavailable")
        rt._sb_request = unavailable
        install(rt)
        rt.callback(1, "admin_ref_points|list|0")
        self.assertIn("belum dapat disemak", rt.sent[-1][1])
        self.assertNotIn("0 mata", rt.sent[-1][1])


if __name__ == "__main__":
    unittest.main()
