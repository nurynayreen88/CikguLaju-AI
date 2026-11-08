"""Cross-Web/Telegram ten-generation trial billing and paid-payment isolation.

All files, accounts, credits and payments are fake. No real user is charged.
"""
import io
import unittest
from unittest.mock import patch

from flask import Flask

from web.unified_rph_web import create_blueprint, source_records
from web_v1_telegram_auth_routes import auth_blueprint

TRIAL={"authenticated":True,"telegram_user_id":712,
       "rakan_pembangun":False,"vip_until":None,"vip_expires_at":None,
       "free_remaining":10}
PAID={**TRIAL,"rakan_pembangun":True,"free_remaining":4}

def teacher_fields():
    row=source_records(4,"ENGLISH")[0]
    return {"year":"4","subject":"ENGLISH","unit":row["unit"],
            "lesson":row["token"],"teacher_class":"4 Bestari"}


class SharedWebTrialTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        app.register_blueprint(create_blueprint())
        self.client=app.test_client()
        self.credits=10
        self.calls=[]
        self.native_calls=[]
        self.account=dict(TRIAL)
        self.auth=patch("web.unified_rph_web._account",
                        side_effect=lambda:(dict(self.account,free_remaining=self.credits),None))
        self.auth.start();self.addCleanup(self.auth.stop)
        self.cfg=patch("web_v1_telegram_auth_routes._config",return_value={
            "account_backend":"supabase","supabase_url":"https://fake.supabase.co",
            "supabase_key":"secret-only-for-test"})
        self.cfg.start();self.addCleanup(self.cfg.stop)
        self.native=patch("web.native_telegram_rph_client.request_native_rph",
                           side_effect=self.render)
        self.native.start();self.addCleanup(self.native.stop)
        self.bill=patch("web.rph_delivery_quota.authorize_rendered_document",
                        side_effect=self.charge)
        self.bill.start();self.addCleanup(self.bill.stop)

    def render(self,selected,fmt):
        self.native_calls.append(fmt)
        if fmt=="word":
            from web.unified_rph_web import _docx
            return _docx(selected)
        return io.BytesIO(b"%PDF-1.4\n"+b"0"*1200)

    def charge(self,account,uid,document,url,key):
        self.calls.append((uid, len(document), account["free_remaining"]))
        self.assertEqual(url,"https://fake.supabase.co")
        self.assertEqual(key,"secret-only-for-test")
        self.assertEqual(uid,712)
        self.assertTrue(document.startswith((b"%PDF-",b"PK\x03\x04")))
        if self.credits==0:return {"allowed":False,"remaining":0,"reference":None}
        self.credits-=1
        return {"allowed":True,"remaining":self.credits,"reference":"web-rph:uuid"}

    def test_one_successful_word_uses_one_shared_credit_and_returns_balance(self):
        q=teacher_fields()
        before=self.client.get("/api/web/rph/availability",query_string=q)
        self.assertEqual(before.status_code,200,before.get_json())
        self.assertEqual(self.calls,[])
        response=self.client.get("/api/web/rph/word",query_string=q)
        self.assertEqual(response.status_code,200,response.get_json() if response.is_json else "")
        self.assertEqual(self.credits,9)
        self.assertEqual(self.calls,[(712,len(response.data),10)])
        self.assertEqual(response.headers["X-RPH-Generator"],"telegram-native")
        self.assertEqual(response.headers["X-RPH-Access-Mode"],"trial")
        self.assertEqual(response.headers["X-RPH-Trial-Remaining"],"9")
        self.assertEqual(response.headers["Cache-Control"],"no-store, private")

    def test_each_successful_format_consumes_one_not_two(self):
        q=teacher_fields()
        for fmt in ("word","pdf"):
            response=self.client.get("/api/web/rph/"+fmt,query_string=q)
            self.assertEqual(response.status_code,200)
        self.assertEqual(self.credits,8)
        self.assertEqual(len(self.calls),2)
        self.assertEqual(self.native_calls,["word","pdf"])

    def test_render_error_never_charges_trial(self):
        from web.native_telegram_rph_client import NativeRPHUnavailable
        with patch("web.native_telegram_rph_client.request_native_rph",
                   side_effect=NativeRPHUnavailable("native failed")):
            response=self.client.get("/api/web/rph/word",query_string=teacher_fields())
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.get_json()["code"],"TELEGRAM_RPH_GENERATOR_UNAVAILABLE")
        self.assertEqual(self.credits,10)
        self.assertEqual(self.calls,[])

    def test_paid_partner_unlimited_never_spends_remaining_trial(self):
        self.account=dict(PAID)
        self.credits=4
        for fmt in ("word","pdf"):
            response=self.client.get("/api/web/rph/"+fmt,query_string=teacher_fields())
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers["X-RPH-Access-Mode"],"paid")
            self.assertNotIn("X-RPH-Trial-Remaining",response.headers)
        self.assertEqual(self.credits,4)
        self.assertEqual(self.calls,[])

    def test_no_balance_cannot_render_or_download(self):
        self.credits=0
        # Source availability is read-only: the teacher may see that the
        # underlying RPH exists, but may not download it without access.
        # This deliberately differs from the Word/PDF billing boundary.
        availability=self.client.get("/api/web/rph/availability",
                                     query_string=teacher_fields())
        self.assertEqual(availability.status_code,200)
        self.assertEqual(availability.get_json()["available"],True)
        self.assertEqual(availability.get_json()["download_allowed"],False)
        self.assertEqual(availability.get_json()["access_status"],"exhausted")
        for path in ("word","pdf"):
            r=self.client.get("/api/web/rph/"+path,query_string=teacher_fields())
            self.assertEqual(r.status_code,403)
            self.assertEqual(r.get_json()["code"],"FREE_TRIAL_EXHAUSTED")
        self.assertEqual(self.native_calls,[])
        self.assertEqual(self.calls,[])

    def test_race_loss_after_render_never_reveals_document(self):
        self.credits=1
        with patch("web.rph_delivery_quota.authorize_rendered_document",
                   return_value={"allowed":False,"remaining":0,"reference":None}):
            r=self.client.get("/api/web/rph/word",query_string=teacher_fields())
        self.assertEqual(r.status_code,403)
        self.assertEqual(r.get_json()["remaining"],0)
        self.assertEqual(r.get_json()["code"],"FREE_TRIAL_EXHAUSTED")
        self.assertEqual(self.native_calls,["word"])
        self.assertNotIn(b"PK\x03\x04",r.data)

    def test_missing_balance_fails_closed_before_render(self):
        self.credits=10
        self.account["free_remaining"]=None
        with patch("web.unified_rph_web._account",return_value=(dict(self.account),None)):
            r=self.client.get("/api/web/rph/word",query_string=teacher_fields())
        self.assertEqual(r.status_code,503)
        self.assertEqual(r.get_json()["code"],"RPH_TRIAL_BALANCE_UNAVAILABLE")
        self.assertEqual(self.calls,[])
        self.assertEqual(self.native_calls,[])

    def test_full_rph_preview_not_free_unbilled(self):
        r=self.client.get("/api/web/rph/preview",query_string=teacher_fields())
        self.assertEqual(r.status_code,403)
        self.assertEqual(r.get_json()["code"],"TRIAL_PREVIEW_UNAVAILABLE")
        self.assertEqual(self.calls,[])
        self.assertEqual(self.native_calls,[])

    def test_server_charge_rpc_failure_does_not_leak_document(self):
        with patch("web.rph_delivery_quota.authorize_rendered_document",
                   side_effect=TimeoutError()):
            r=self.client.get("/api/web/rph/pdf",query_string=teacher_fields())
        self.assertEqual(r.status_code,503)
        self.assertEqual(r.get_json()["code"],"RPH_TRIAL_CHARGE_UNCONFIRMED")
        self.assertNotIn(b"%PDF-",r.data)


class TrialSessionTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        app.register_blueprint(auth_blueprint)
        self.client=app.test_client()
        self.conf={"CIKGULAJU_WEB_SESSION_SECRET":"x"*48}
        for target,value in (
            ("web_v1_telegram_auth_routes._config",self.conf),
            ("web_v1_telegram_auth_routes.verify_session_ticket",712),
        ):
            p=patch(target,return_value=value);p.start();self.addCleanup(p.stop)

    def test_signed_session_exposes_same_balance_not_new_credits(self):
        with patch("web_v1_telegram_auth_routes._lookup",return_value=dict(TRIAL,free_remaining=7)):
            r=self.client.get("/api/auth/telegram/session")
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json["rph_access_mode"],"trial")
        self.assertEqual(r.json["rph_trial_remaining"],7)
        self.assertEqual(r.json["access"],"7 janaan percuma berbaki")
        with patch("web_v1_telegram_auth_routes._lookup",return_value=dict(TRIAL,free_remaining=0)):
            r=self.client.get("/api/auth/telegram/session")
        self.assertEqual(r.json["rph_access_mode"],"exhausted")
        self.assertEqual(r.json["rph_trial_remaining"],0)

    def test_lifetime_member_keeps_old_trial_balance_and_unlimited_access(self):
        with patch("web_v1_telegram_auth_routes._lookup",return_value=dict(PAID)):
            r=self.client.get("/api/auth/telegram/session")
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json["rph_access_mode"],"paid")
        self.assertEqual(r.json["rph_trial_remaining"],4)
        self.assertEqual(r.json["access"],"Tanpa had seumur hidup")

if __name__=="__main__":
    unittest.main()
