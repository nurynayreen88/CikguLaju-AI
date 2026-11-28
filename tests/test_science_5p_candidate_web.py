"""Isolated candidate endpoint checks with real signed session tickets.
No live accounts, network calls or quota mutations.
"""
import os
import unittest
from io import BytesIO
from unittest.mock import patch, Mock
from contextlib import ExitStack
from flask import Flask
from docx import Document
from web import science_5p_candidate_web as candidate
from web_v1_sessions import issue_session_ticket
from tools.audit_science_native_5p_documents_20261128 import inventory

SECRET="test-only-science-candidate-secret-not-production"
class CandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows={y:inventory(y) for y in (5,6)}
        cls.units={}
        cls.lessons={}
        for y,rows in cls.rows.items():
            prefix={5:"v",6:"w"}[y]
            groups=list(dict.fromkeys(r["unit"] for r in rows))
            cls.units[y]=[{"value":prefix+format(i+1,"024x"),"label":g} for i,g in enumerate(groups)]
            for u in cls.units[y]:
                cls.lessons[y,u["value"]]=[
                    {"value":r["lesson_id"],"label":f"PdP {int(r['lesson_id'].rsplit('-',1)[-1]):03d} • {r['title']}",
                     "textbook_ref":f"Buku Teks m/s {r['textbook_pages']}"}
                    for r in rows if r["unit"]==u["label"]]
    def setUp(self):
        self.app=Flask(__name__); self.app.testing=True
        self.app.register_blueprint(candidate.create_blueprint())
        self.app.register_blueprint(candidate.create_blueprint(published=True))
        self.client=self.app.test_client()
        self.account={"telegram_user_id":42,"authenticated":True,"free_remaining":10,"rakan_pembangun":False}
        self.stack=ExitStack(); self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ,{"CIKGULAJU_SCIENCE_5P_ENABLED":"1"}))
        self.stack.enter_context(patch.object(candidate,"_config",return_value={
            "account_backend":"supabase","CIKGULAJU_WEB_SESSION_SECRET":SECRET,
            "supabase_url":"https://example.invalid","supabase_key":"test-only"}))
        self.lookup=self.stack.enter_context(patch.object(candidate,"_lookup",return_value=self.account))
        self.debit=self.stack.enter_context(patch.object(candidate,"debit_shared_trial",return_value={"ok":True,"remaining":9}))
        self.native_units=self.stack.enter_context(patch.object(candidate.native,"list_native_units",side_effect=lambda y,s:self.units[y]))
        self.native_lessons=self.stack.enter_context(patch.object(candidate.native,"list_native_lessons",side_effect=lambda y,s,u:self.lessons[y,u]))
        self.available=self.stack.enter_context(patch.object(candidate.native,"verified_native_sequence_available",return_value=True))
        self.payload={"year":5,"subject":"SCIENCE","unit":self.units[5][0]["value"],
                      "lesson":self.rows[5][0]["lesson_id"],"format":"word","rph_variant":"5p"}
    def post(self,**updates):
        return self.client.post(candidate.URL,json={**self.payload,**updates},headers={"Origin":candidate.ORIGIN})
    def login(self,uid=42,**kw):
        self.client.set_cookie(candidate.COOKIE,issue_session_ticket(uid,SECRET,**kw))
    def test_default_gate_even_with_env(self):
        self.login()
        self.assertEqual(self.post().status_code,404)
        self.lookup.assert_not_called(); self.debit.assert_not_called()
    def test_session_and_quota(self):
        with patch.object(candidate,"RELEASE_APPROVED",True):
            self.assertEqual(self.post().status_code,401)
            self.login(now=1)
            self.assertEqual(self.post().status_code,401)
            self.login(43)
            self.assertEqual(self.post().status_code,403)
            self.login()
            self.assertEqual(self.client.post(candidate.URL,json=self.payload).status_code,403)
            self.assertEqual(self.post(reference="forged").status_code,400)
            self.assertEqual(self.post(unit="u"+"0"*24).status_code,503)
            self.assertEqual(self.post(teacher_students="999").status_code,400)
            self.available.return_value=False
            self.assertEqual(self.post().status_code,503)
            self.available.return_value=True
            self.debit.assert_not_called()
            out=self.post(teacher_class="5 Bestari",teacher_students="30")
            self.assertEqual(out.status_code,200)
            self.assertEqual(out.headers["X-RPH-Trial-Remaining"],"9")
            self.assertEqual(out.headers["Cache-Control"],"no-store, private")
            self.assertIn("5 Bestari",Document(BytesIO(out.data)).tables[0].cell(1,0).text)
            self.debit.assert_called_once()
            self.assertTrue(self.debit.call_args.args[3].startswith("web-rph:"))
            self.debit.return_value={"ok":False,"remaining":0}
            out=self.post()
            self.assertEqual(out.status_code,403)
            self.assertNotIn("Content-Disposition",out.headers)
            self.account["free_remaining"]=0
            self.assertEqual(self.post().status_code,403)
            self.assertEqual(self.debit.call_count,2)
    def test_availability_never_debits(self):
        selection={k:self.payload[k] for k in ("year","subject","unit","lesson")}
        def get(**updates):
            return self.client.get(candidate.AVAILABILITY_URL,query_string={**selection,**updates})
        self.assertEqual(get().status_code,404)
        with patch.object(candidate,"RELEASE_APPROVED",True):
            self.assertEqual(get().status_code,401)
            self.login()
            out=get()
            self.assertEqual(out.status_code,200)
            self.assertEqual(out.get_json(),{"available":True,"formats":["word","pdf"],"status":"DRAFT-NOT-FOR-TEACHING"})
            self.assertEqual(out.headers["Cache-Control"],"no-store, private")
            self.assertEqual(get(extra="wrong").status_code,400)
            self.assertEqual(get(year=4).status_code,404)
            self.available.return_value=False
            self.assertEqual(get().status_code,503)
            self.account["free_remaining"]=0
            out=get()
            self.assertEqual(out.status_code,403)
            self.assertEqual(out.get_json()["code"],"FREE_TRIAL_EXHAUSTED")
        self.debit.assert_not_called()

    def test_paid_pdf_no_charge(self):
        self.login()
        self.account.update(rakan_pembangun=True,free_remaining=0)
        with patch.object(candidate,"RELEASE_APPROVED",True):
            out=self.post(year=6,unit=self.units[6][0]["value"],lesson=self.rows[6][0]["lesson_id"],format="pdf")
        self.assertEqual(out.status_code,200)
        self.assertTrue(out.data.startswith(b"%PDF-"))
        self.debit.assert_not_called()
    def test_published_requires_exact_approval_and_preserves_quota(self):
        from web import science_5p_release as gate
        self.login()
        purl="/api/kssr/sk/science/5p/download"
        aurl="/api/kssr/sk/science/5p/available"
        selection={k:self.payload[k] for k in ("year","subject","unit","lesson")}
        def post(**changes):
            return self.client.post(purl,json={**self.payload,**changes},headers={"Origin":candidate.ORIGIN})
        self.assertEqual(post().status_code,404)
        self.assertEqual(self.client.get(aurl,query_string=selection).status_code,404)
        self.debit.assert_not_called()
        self.available.assert_not_called()
        rows={k:dict(v,ready=False) for k,v in gate.records().items()}
        rows[5,self.payload["lesson"]].update(ready=True,status="APPROVED_FOR_RELEASE")
        with patch.object(gate,"records",return_value=rows):
            out=self.client.get(aurl,query_string=selection)
            self.assertEqual(out.get_json(),{"available":True,"formats":["word","pdf"],"status":"INTERNAL-REVIEWED"})
            self.assertEqual(post(lesson="SK27-SCI-Y5-PDP-002").status_code,404)
            self.debit.assert_not_called()
            out=post(teacher_class="5 Bestari")
            self.assertEqual(out.status_code,200)
            self.assertEqual(out.headers["X-RPH-QA-Status"],"INTERNAL-REVIEWED")
            self.assertNotIn("DRAF_QA",out.headers["Content-Disposition"])
            self.assertEqual(Document(BytesIO(out.data)).tables[0].cell(1,1).text,"SAINS SK\nTAHUN 5")
            self.debit.assert_called_once()
            self.account.update(rakan_pembangun=True,free_remaining=0)
            out=post(format="pdf")
            self.assertEqual(out.status_code,200)
            self.assertTrue(out.data.startswith(b"%PDF-"))
            self.debit.assert_called_once()
        self.assertEqual(self.post().status_code,404)

    def test_all_original_selection_contracts_and_drift(self):
        for y,rows in self.rows.items():
            for row in rows:
                unit=next(u["value"] for u in self.units[y] if u["label"]==row["unit"])
                self.assertEqual(candidate.verified_selection(y,unit,row["lesson_id"],rows),row)
        self.native_lessons.side_effect=lambda y,s,u:[dict(x,textbook_ref="wrong") for x in self.lessons[y,u]]
        with self.assertRaises(ValueError):
            candidate.verified_selection(5,self.payload["unit"],self.payload["lesson"],self.rows[5])
        self.native_units.side_effect=lambda y,s:list(reversed(self.units[y]))
        with self.assertRaises(ValueError):
            candidate.verified_selection(5,self.payload["unit"],self.payload["lesson"],self.rows[5])

if __name__=="__main__":
    unittest.main()
