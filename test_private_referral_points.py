"""Offline contract checks for opt-in private referral points; no live payments."""
import os
import unittest
from unittest.mock import patch
import referral_points_telegram as referral


class FakeApp:
    def __init__(self):
        self.view_functions = {"webhook": lambda: {"old": True}}


def fixture():
    sent, calls, registered = [], [], []
    payments = {7: {"id": 7, "status": "pending", "chat_id": "301", "amount": 10.0}}
    member = []
    def sb(method, path, **kwargs):
        calls.append((method, path, kwargs))
        if path.startswith("referral_members?"):
            return member[:]
        if path.startswith("cikgulaju_users?"):
            return [{"telegram_user_id": 301}]
        if path.startswith("referral_signups?") or path.startswith("referral_point_events?"):
            return []
        if path.startswith("pioneer_entitlements?"):
            return [{"entitlement":"PIONEER_LIFETIME",
                     "payment_reference":"pioneer-payment:301:abcdef"}]
        if path.startswith("subscription_payments?"):
            return [{"status":"paid","payment_reference":"payment-request:7"}]
        if path == "referral_members" and method == "POST":
            member.append(dict(kwargs["json"]))
        if path.startswith("rpc/"):
            if path.endswith("referral_award_verified_payment"):
                return {"awarded":True,"points":5}
            return {"captured":True}
        return []
    def callback(uid, data):
        if data.startswith("admin_approve"):
            payments[7]["status"] = "approved"
        return "original"
    app = FakeApp()
    ns = {"app":app,"callback":callback,"send":lambda uid,txt,*a: sent.append((uid,txt)),
          "_sb_request":sb,"_bot_username_v25267":lambda: "CikguLajuBot",
          "_payment_request":lambda rid: dict(payments[rid]),
          "_is_admin":lambda uid: uid == 1,
          "_upsert_user":lambda user,uid:registered.append(uid),
          "menu":lambda uid,**kw: sent.append((uid,"menu")),
          "request":None,"jsonify":lambda x:x}
    return ns, sent, calls, registered


class TestPrivateReferral(unittest.TestCase):
    def test_feature_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            ns, _, _, _ = fixture()
            self.assertFalse(referral.install(ns))
            self.assertEqual(ns["callback"](1, "other"), "original")

    def test_only_private_user_messages(self):
        self.assertTrue(referral.is_private_message({
            "chat":{"id":42,"type":"private"},"from":{"id":42}}))
        self.assertFalse(referral.is_private_message({
            "chat":{"id":42,"type":"group"},"from":{"id":42}}))
        self.assertFalse(referral.is_private_message({
            "chat":{"id":42,"type":"private"},"from":{"id":43}}))

    def test_capture_opaque_token_without_legacy_vip(self):
        ns, sent, calls, registered = fixture()
        msg = {"chat":{"id":301,"type":"private"},"from":{"id":301},
               "text":"/start rp_" + "A"*24}
        ns["request"] = type("Request",(),{"headers":{"X-Telegram-Bot-Api-Secret-Token":"correct-long-secret"},"get_json":lambda self,**_:{"message":msg}})()
        with patch.dict(os.environ, {"CIKGULAJU_REFERRAL_POINTS_ENABLED":"1","CIKGULAJU_TELEGRAM_WEBHOOK_SECRET":"correct-long-secret"}):
            self.assertTrue(referral.install(ns))
            response = ns["app"].view_functions["webhook"]()
        self.assertTrue(response["private_referral"])
        self.assertEqual(registered, [301])
        self.assertTrue(any(p.endswith("referral_capture_signup") for m,p,a in calls))

    def test_legacy_link_does_not_award_vip_when_enabled(self):
        ns, sent, calls, registered = fixture()
        msg={"chat":{"id":301,"type":"private"},"from":{"id":301},
             "text":"/start ref_123"}
        ns["request"]=type("Request",(),{"headers":{"X-Telegram-Bot-Api-Secret-Token":"correct-long-secret"},"get_json":lambda self,**_:{"message":msg}})()
        with patch.dict(os.environ, {"CIKGULAJU_REFERRAL_POINTS_ENABLED":"1","CIKGULAJU_TELEGRAM_WEBHOOK_SECRET":"correct-long-secret"}):
            referral.install(ns)
            response = ns["app"].view_functions["webhook"]()
        self.assertTrue(response["legacy_referral_closed"])
        self.assertEqual(registered,[301])
        self.assertFalse(any("referral_award" in p for m,p,a in calls))

    def test_reject_forged_webhook(self):
        ns, sent, calls, registered = fixture()
        msg={"chat":{"id":1,"type":"private"},"from":{"id":1},"text":"/refadd 301"}
        ns["request"]=type("Request",(),{"headers":{},
            "get_json":lambda self,**_:{"message":msg}})()
        with patch.dict(os.environ,{"CIKGULAJU_REFERRAL_POINTS_ENABLED":"1",
                                    "CIKGULAJU_TELEGRAM_WEBHOOK_SECRET":"correct-long-secret"}):
            referral.install(ns)
            response=ns["app"].view_functions["webhook"]()
        self.assertEqual(response[1],403)
        self.assertFalse(any(path=="referral_members" for method,path,args in calls))

    def test_pioneer_points_after_admin_approval_only(self):
        ns,sent,calls,_=fixture()
        ns["request"]=type("Request",(),{"headers":{"X-Telegram-Bot-Api-Secret-Token":"correct-long-secret"},"get_json":lambda self,**_:{} })()
        with patch.dict(os.environ,{"CIKGULAJU_REFERRAL_POINTS_ENABLED":"1","CIKGULAJU_TELEGRAM_WEBHOOK_SECRET":"correct-long-secret"}):
            referral.install(ns)
            ns["callback"](1,"admin_approve|7|301")
            ns["callback"](1,"admin_approve|7|301")  # no second award request
        awards=[(m,p,a) for m,p,a in calls if p=="rpc/referral_award_verified_payment"]
        self.assertEqual(len(awards),1)
        self.assertEqual(awards[0][2]["json"]["p_payment_kind"],"pioneer")


if __name__ == "__main__":
    unittest.main()
