"""Special RPH Web source parity and no unauthorized or duplicate trial debit."""
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch, call
from flask import Flask, jsonify

from web.special_activities_web import bp, SUBJECTS, SELEPAS, TRANSISI

DIGEST="a"*64
SOURCE={"status":"DRAFT_REVIEW","source_digest":DIGEST,
        "items":[{"id":"S03C","label":"Matematik — Projek","phase":None}]}
SUBJECT_SOURCE={"status":"DRAFT_REVIEW","source_digest":DIGEST,
                "items":[{"value":x,"label":x} for x in SUBJECTS]}


class SpecialRphWebTests(unittest.TestCase):
    def setUp(self):
        self.app=Flask(__name__)
        self.app.register_blueprint(bp)
        self.client=self.app.test_client()
        self.account={"telegram_user_id":777,"free_remaining":5}

    def qs(self,**extra):
        return {"kind":SELEPAS,"year":"6","subject":"Matematik",
                "activity_id":"S03C","source_digest":DIGEST,
                "teacher_class":"6 Bestari","teacher_date":"2026-11-06",
                "teacher_start":"08:00","teacher_end":"09:00",
                "teacher_students":"32",**extra}

    def test_unauthenticated_user_sees_no_source_or_document(self):
        with patch("web.special_activities_web._account",
                   return_value=(None,(jsonify({"error":"Log masuk dahulu"}),401))):
            for endpoint in ("options","subjects","word","pdf"):
                with self.subTest(endpoint=endpoint):
                    url="/api/web/aktiviti-khas/"+endpoint
                    r=self.client.get(url,query_string=self.qs())
                    self.assertEqual(r.status_code,401)

    def test_read_only_catalog_is_trusted_from_telegram(self):
        with patch("web.special_activities_web._account",return_value=(self.account,None)),\
             patch("web.special_activities_web._private_request",return_value=SOURCE) as native:
            r=self.client.get("/api/web/aktiviti-khas/options",
                query_string={"kind":SELEPAS,"year":"6","subject":"Matematik"})
            self.assertEqual(r.status_code,200)
            self.assertEqual(r.get_json()["status"],"DRAF")
            self.assertEqual(len(r.get_json()["items"]),1)
            native.assert_called_once_with("options",query={
                "kind":SELEPAS,"year":6,"subject":"Matematik"})
        with patch("web.special_activities_web._account",return_value=(self.account,None)),\
             patch("web.special_activities_web._private_request",return_value=SUBJECT_SOURCE):
            r=self.client.get("/api/web/aktiviti-khas/subjects",
                              query_string={"kind":SELEPAS,"year":"6"})
            self.assertEqual(r.status_code,200)
            self.assertEqual(len(r.get_json()["items"]),13)

    def test_no_public_pdf_while_trial_exhausted(self):
        account={**self.account,"free_remaining":0}
        with patch("web.special_activities_web._account",return_value=(account,None)),\
             patch("web.special_activities_web._has_paid_access",return_value=False),\
             patch("web.special_activities_web._private_request") as upstream:
            r=self.client.get("/api/web/aktiviti-khas/pdf",
                              query_string=self.qs())
            self.assertEqual(r.status_code,403)
            upstream.assert_not_called()

    def test_paid_teacher_document_from_native_without_credit_charge(self):
        pdf=b"%PDF-" + b"0"*1200
        def native(endpoint,**kw):
            if endpoint=="options":return SOURCE
            if endpoint=="render":
                self.assertEqual(kw["fmt"],"pdf")
                self.assertEqual(kw["payload"]["selection"]["activity_id"],"S03C")
                self.assertEqual(kw["payload"]["selection"]["subject"],"Matematik")
                self.assertEqual(kw["payload"]["teacher"]["class"],"6 Bestari")
                self.assertEqual(kw["payload"]["teacher"]["date"],"2026-11-06")
                self.assertEqual(kw["payload"]["teacher"]["time"],"08:00 - 09:00")
                return pdf
            raise AssertionError(endpoint)
        with patch("web.special_activities_web._account",return_value=(self.account,None)),\
             patch("web.special_activities_web._has_paid_access",return_value=True),\
             patch("web.special_activities_web._private_request",side_effect=native),\
             patch("web.rph_delivery_quota.authorize_rendered_document") as quota:
            r=self.client.get("/api/web/aktiviti-khas/pdf",query_string=self.qs())
            self.assertEqual(r.status_code,200)
            self.assertEqual(r.data,pdf)
            self.assertIn("DRAF",r.headers["Content-Disposition"])
            self.assertEqual(r.headers["X-RPH-Generator"],"telegram-native")
            quota.assert_not_called()

    def test_trial_charge_only_after_verified_document(self):
        pdf=b"%PDF-"+b"0"*1200
        with patch("web.special_activities_web._account",return_value=(self.account,None)),\
             patch("web.special_activities_web._has_paid_access",return_value=False),\
             patch("web.special_activities_web._private_request",
                   side_effect=lambda endpoint,**kw: SOURCE if endpoint=="options" else pdf),\
             patch("web_v1_telegram_auth_routes._config",
                   return_value={"account_backend":"supabase","supabase_url":"https://db.example",
                                 "supabase_key":"test-only"}),\
             patch("web.rph_delivery_quota.authorize_rendered_document",
                   return_value={"allowed":True,"remaining":4}) as quota:
            r=self.client.get("/api/web/aktiviti-khas/pdf",query_string=self.qs())
            self.assertEqual(r.status_code,200)
            self.assertEqual(r.headers["X-RPH-Trial-Remaining"],"4")
            quota.assert_called_once()
            self.assertEqual(quota.call_args.args[2],pdf)
        with patch("web.special_activities_web._account",return_value=(self.account,None)),\
             patch("web.special_activities_web._has_paid_access",return_value=False),\
             patch("web.special_activities_web._private_request",
                   side_effect=lambda endpoint,**kw: SOURCE if endpoint=="options" else
                   (_ for _ in ()).throw(ValueError("failed"))),\
             patch("web.rph_delivery_quota.authorize_rendered_document") as quota:
            r=self.client.get("/api/web/aktiviti-khas/pdf",query_string=self.qs())
            self.assertEqual(r.status_code,400)
            quota.assert_not_called()

    def test_digest_and_subject_cannot_be_forged(self):
        with patch("web.special_activities_web._account",return_value=(self.account,None)),\
             patch("web.special_activities_web._has_paid_access",return_value=True),\
             patch("web.special_activities_web._private_request",return_value=SOURCE) as up:
            a=self.client.get("/api/web/aktiviti-khas/pdf",
                              query_string=self.qs(source_digest="f"*64))
            self.assertEqual(a.status_code,503)
            self.assertEqual(up.call_count,1)
            b=self.client.get("/api/web/aktiviti-khas/pdf",
                              query_string=self.qs(subject="Sejarah"))
            self.assertEqual(b.status_code,503)
            c=self.client.get("/api/web/aktiviti-khas/pdf",
                              query_string={**self.qs(),"uid":"777"})
            self.assertEqual(c.status_code,400)
            d=self.client.get("/api/web/aktiviti-khas/options",
                              query_string={"kind":TRANSISI,"year":"2","phase":"Fasa Kesediaan"})
            self.assertEqual(d.status_code,400)
            self.assertTrue(all(x.status_code != 200 for x in (a,b,c,d)))

    def test_web_ui_is_separate_and_profile_first(self):
        html=(Path(__file__).resolve().parents[1]/
              "web_v1_static_preview"/"index.html").read_text("utf8")
        js=(Path(__file__).resolve().parents[1]/
            "web_v1_static_preview"/"special-activities.js").read_text("utf8")
        self.assertIn('id="view-special"',html)
        self.assertIn('data-web-view="special"',html)
        self.assertLess(html.index('data-web-view="account"'),
                        html.index('data-web-view="special"'))
        self.assertLess(html.index('data-web-view="today"'),
                        html.index('data-web-view="special"'))
        self.assertIn('id="special-subject"',html)
        self.assertIn('id="special-phase"',html)
        self.assertIn('id="special-date"',html)
        self.assertIn('id="special-activity"',html)
        self.assertIn('"/api/web/aktiviti-khas/"+fmt+"?"',js)
        self.assertIn('source_digest',js)
        self.assertIn('DRAF',html)
        self.assertIn("59",html) if "59" in html else None
        self.assertNotIn("app.py",js)


if __name__=="__main__":
    unittest.main()
