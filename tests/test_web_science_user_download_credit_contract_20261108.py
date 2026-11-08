"""Science T2–T6 real Web route/credit contract with synthetic users only.

Exercises production Flask handlers /api/web/rph/availability, /word and /pdf
using the actual Telegram-native selection branch. Mocks only account,
server-to-server transport and authoritative trial debit; never creates real
accounts, touches Supabase, calls live Telegram or spends user credits.
"""
from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from docx import Document
from flask import Flask
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4

from web.unified_rph_web import create_blueprint
from web.native_telegram_rph_client import NativeRPHUnavailable

PAID={
    "authenticated":True,"telegram_user_id":825001,
    "rakan_pembangun":True,"vip_until":None,
    "vip_expires_at":None,"free_remaining":2,
}
FREE={**PAID,"rakan_pembangun":False,"free_remaining":10}
UNIT="u"+"a"*24


def actual_sample(fmt,year):
    output=BytesIO()
    if fmt=="word":
        doc=Document()
        heading=doc.add_heading("SAINS • TAHUN "+str(year),0)
        doc.add_paragraph("SCI-Y"+str(year)+"-PDP-001")
        table=doc.add_table(rows=3,cols=2)
        table.cell(0,0).text="SP"
        table.cell(0,1).text="2.1.1"
        table.cell(1,0).text="Aktiviti 1"
        table.cell(1,1).text="Murid memerhati dan mencatat."
        table.cell(2,0).text="PBD"
        table.cell(2,1).text="Rekod respons setiap murid."
        doc.save(output)
    else:
        c=Canvas(output,pagesize=A4)
        c.drawString(48,780,"SAINS TAHUN "+str(year))
        c.drawString(48,750,"SCI-Y"+str(year)+"-PDP-001")
        c.drawString(48,720,"Aktiviti 1 - PBD")
        c.showPage()
        c.save()
    output.seek(0)
    return output


class ScienceWebUserDownloadContracts(unittest.TestCase):
    def setUp(self):
        app=Flask("science_t2_to_t6_route_contract")
        app.register_blueprint(create_blueprint())
        self.client=app.test_client()
        self.account=dict(FREE)
        self.remaining=10
        self.debits=[]
        self.renders=[]
        self.selection_checks=[]
        self.account_check=patch("web.unified_rph_web._account",
            side_effect=lambda:(dict(self.account,free_remaining=self.remaining),None))
        self.account_check.start()
        self.addCleanup(self.account_check.stop)
        self.backend=patch("web.native_telegram_sequence_rph_client.verified_native_sequence_available",
                           side_effect=self.available)
        self.backend.start()
        self.addCleanup(self.backend.stop)
        self.documents=patch("web.native_telegram_sequence_rph_client.request_native_sequence_rph",
                             side_effect=self.generate)
        self.documents.start()
        self.addCleanup(self.documents.stop)
        self.trial_config=patch("web_v1_telegram_auth_routes._config",
              return_value={"account_backend":"supabase","supabase_url":"https://example.supabase.co",
                            "supabase_key":"internal-fixture-only"})
        self.trial_config.start()
        self.addCleanup(self.trial_config.stop)
        self.debit=patch("web.rph_delivery_quota.authorize_rendered_document",
                         side_effect=self.charge)
        self.debit.start()
        self.addCleanup(self.debit.stop)

    def query(self,year):
        return {"year":str(year),"subject":"SCIENCE",
                "unit":UNIT,"lesson":f"SCI-Y{year}-PDP-001",
                "teacher_class":"4 Bestari","teacher_date":"2026-11-08",
                "teacher_start":"08:00","teacher_end":"09:00",
                "teacher_students":"32"}

    def available(self,year,subject,unit,lesson):
        self.selection_checks.append((year,subject,unit,lesson))
        if (year not in range(2,7) or subject!="SCIENCE"
                or unit!=UNIT or lesson!=f"SCI-Y{year}-PDP-001"):
            raise NativeRPHUnavailable("Invalid original Science source")
        return True

    def generate(self,selected,fmt):
        self.renders.append((selected,fmt))
        self.assertEqual(selected["source"],"telegram-native-pdp-sequence")
        self.assertEqual(selected["subject"],"SCIENCE")
        self.assertEqual(selected["unit"],UNIT)
        self.assertEqual(selected["lesson"],f"SCI-Y{selected['year']}-PDP-001")
        self.assertEqual(selected["teacher"],{
            "class":"4 Bestari","date":"2026-11-08",
            "time":"08:00 - 09:00","students":"32"})
        self.assertNotIn("telegram_user_id",selected)
        self.assertNotIn("free_remaining",selected)
        return actual_sample(fmt,selected["year"])

    def charge(self,account,uid,document,url,key):
        self.debits.append((uid,len(document),self.remaining))
        self.assertEqual(uid,825001)
        self.assertEqual(url,"https://example.supabase.co")
        self.assertEqual(key,"internal-fixture-only")
        self.assertTrue(document.startswith((b"PK\\x03\\x04",b"%PDF-")))
        if self.remaining==0:
            return {"allowed":False,"remaining":0,"reference":None}
        self.remaining-=1
        return {"allowed":True,"remaining":self.remaining,
                "reference":"web-rph:synthetic-reference"}

    def test_paid_word_pdf_all_five_years_one_actual_route_each(self):
        self.account=dict(PAID)
        self.remaining=2
        for year in range(2,7):
            with self.subTest(year=year):
                q=self.query(year)
                available=self.client.get("/api/web/rph/availability",query_string=q)
                self.assertEqual(available.status_code,200,available.json)
                self.assertEqual(available.json["access_status"],"paid")
                self.assertTrue(available.json["download_allowed"])
                self.assertNotIn("teacher",available.json)
                for fmt in ("word","pdf"):
                    response=self.client.get("/api/web/rph/"+fmt,query_string=q)
                    self.assertEqual(response.status_code,200,response.get_json(silent=True))
                    self.assertEqual(response.headers["X-RPH-Generator"],"telegram-native")
                    self.assertEqual(response.headers["X-RPH-Access-Mode"],"paid")
                    self.assertNotIn("X-RPH-Trial-Remaining",response.headers)
                    self.assertIn("attachment;",response.headers["Content-Disposition"])
                    self.assertIn(f"SCI-Y{year}-PDP-001",response.headers["Content-Disposition"])
                    self.assertEqual(response.headers["Cache-Control"],"no-store, private")
                    if fmt=="word":
                        doc=Document(BytesIO(response.data))
                        text=" ".join(p.text for p in doc.paragraphs)
                        self.assertIn(f"SCI-Y{year}-PDP-001",text)
                    else:
                        pdf=PdfReader(BytesIO(response.data))
                        self.assertEqual(len(pdf.pages),1)
                        self.assertIn(f"SCI-Y{year}-PDP-001",pdf.pages[0].extract_text())
        self.assertEqual(len(self.renders),10)
        self.assertEqual(self.remaining,2)
        self.assertEqual(self.debits,[])

    def test_trial_charges_only_after_successful_native_science_document(self):
        self.account=dict(FREE)
        self.remaining=10
        q=self.query(2)
        availability=self.client.get("/api/web/rph/availability",query_string=q)
        self.assertEqual(availability.status_code,200)
        self.assertEqual(availability.json["access_status"],"trial")
        self.assertEqual(self.remaining,10)
        self.assertEqual(self.debits,[])
        response=self.client.get("/api/web/rph/word",query_string=q)
        self.assertEqual(response.status_code,200,response.get_json(silent=True))
        self.assertEqual(response.headers["X-RPH-Trial-Remaining"],"9")
        self.assertEqual(self.remaining,9)
        self.assertEqual(len(self.debits),1)
        response=self.client.get("/api/web/rph/pdf",query_string=q)
        self.assertEqual(response.status_code,200,response.get_json(silent=True))
        self.assertEqual(response.headers["X-RPH-Trial-Remaining"],"8")
        self.assertEqual(self.remaining,8)
        self.assertEqual(len(self.debits),2)

    def test_exhausted_and_unavailable_credits_block_science_before_generating(self):
        q=self.query(3)
        self.remaining=0
        availability=self.client.get("/api/web/rph/availability",query_string=q)
        self.assertEqual(availability.status_code,200)
        self.assertFalse(availability.json["download_allowed"])
        self.assertEqual(availability.json["access_status"],"exhausted")
        for fmt in ("word","pdf"):
            response=self.client.get("/api/web/rph/"+fmt,query_string=q)
            self.assertEqual(response.status_code,403)
            self.assertEqual(response.json["code"],"FREE_TRIAL_EXHAUSTED")
        self.assertEqual(self.renders,[])
        self.assertEqual(self.debits,[])
        self.remaining="10" # untrusted string is never accepted as a real balance
        for fmt in ("word","pdf"):
            response=self.client.get("/api/web/rph/"+fmt,query_string=q)
            self.assertEqual(response.status_code,503)
            self.assertEqual(response.json["code"],"RPH_TRIAL_BALANCE_UNAVAILABLE")
        self.assertEqual(self.renders,[])

    def test_unavailable_telegram_source_never_renders_or_charges(self):
        q=self.query(4)
        with patch("web.native_telegram_sequence_rph_client.verified_native_sequence_available",
                   side_effect=NativeRPHUnavailable("source down")):
            for fmt in ("word","pdf"):
                response=self.client.get("/api/web/rph/"+fmt,query_string=q)
                self.assertEqual(response.status_code,503)
                self.assertEqual(response.json["code"],"TELEGRAM_NATIVE_PDP_RPH_NOT_READY")
        self.assertEqual(self.renders,[])
        self.assertEqual(self.debits,[])

    def test_telegram_renderer_failure_never_consumes_trial(self):
        q=self.query(5)
        with patch("web.native_telegram_sequence_rph_client.request_native_sequence_rph",
                   side_effect=NativeRPHUnavailable("generator down")):
            response=self.client.get("/api/web/rph/pdf",query_string=q)
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json["code"],"TELEGRAM_RPH_GENERATOR_UNAVAILABLE")
        self.assertEqual(self.remaining,10)
        self.assertEqual(self.debits,[])

    def test_last_credit_race_does_not_release_file(self):
        self.remaining=1
        q=self.query(6)
        with patch("web.rph_delivery_quota.authorize_rendered_document",
                   return_value={"allowed":False,"remaining":0,"reference":None}):
            response=self.client.get("/api/web/rph/pdf",query_string=q)
        self.assertEqual(response.status_code,403)
        self.assertEqual(response.json["code"],"FREE_TRIAL_EXHAUSTED")
        self.assertNotIn(b"%PDF-",response.data)

    def test_no_anonymous_science_download_or_duplicate_param(self):
        with patch("web.unified_rph_web._account",
                   return_value=(None,({"error":"login required"},401))):
            response=self.client.get("/api/web/rph/pdf",query_string=self.query(2))
        self.assertEqual(response.status_code,401)
        response=self.client.get("/api/web/rph/pdf",
            query_string="year=2&year=3&subject=SCIENCE&unit="+UNIT+
                         "&lesson=SCI-Y2-PDP-001")
        self.assertEqual(response.status_code,400)
        self.assertEqual(self.debits,[])


if __name__=="__main__":
    unittest.main()
