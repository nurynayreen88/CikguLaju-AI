"""Offline route security and personalization regression checks."""
import os
import unittest
from io import BytesIO
from unittest.mock import patch
from flask import Flask
from docx import Document
import fitz
from web import kp2027_math_canary_web as c, kp2027_math_5p as five
from web import rph_delivery_quota as quota
import web_v1_telegram_auth_routes as auth
import web_v1_sessions as sessions

class TestMath5PDelivery(unittest.TestCase):
    def setUp(self):
        self.account={"authenticated":True,"telegram_user_id":123,"rakan_pembangun":False,"free_remaining":10}
        self.config={"account_backend":"supabase","supabase_url":"https://"+c.HOST,"supabase_key":"unused-test-key","CIKGULAJU_WEB_SESSION_SECRET":"s"*48}
        self.asset=b"original-approved-asset"
        self.stack=[
            patch.dict(os.environ,{c.FEATURE_FLAG:"1",c.FIVE_P_FLAG:"1"}),
            patch.object(auth,"_config",return_value=self.config),
            patch.object(auth,"_lookup",return_value=self.account),
            patch.object(sessions,"verify_session_ticket",return_value=123),
            patch.object(c,"fetch_private_document",return_value=self.asset),
            patch.object(c,"fetch_approved_catalog",return_value={"A":[1],"B":[1]}),
            patch.object(c,"debit_shared_trial",return_value={"ok":True,"remaining":9}),
            patch("web.kp2027_pilot_teacher_fields.personalize_approved_rph",side_effect=lambda data,fmt,fields:data)]
        self.mocks=[p.start() for p in self.stack]
        self.addCleanup(lambda:[p.stop() for p in reversed(self.stack)])
        app=Flask(__name__);app.testing=True;app.register_blueprint(c.create_blueprint())
        self.client=app.test_client()
        self.url="/api/kp2027/sk/tahun-1/matematik"
        self.payload={"group":"A","lesson":1,"format":"word","rph_variant":"5p"}
    def post(self,payload=None):
        return self.client.post(self.url+"/download",json=payload or self.payload,headers={"Origin":c.ORIGIN})
    def test_access_and_quota(self):
        self.assertIn("5p",self.client.get(self.url+"/available").get_json()["rph_variants"])
        self.mocks[6].assert_not_called()
        with patch.dict(os.environ,{c.FIVE_P_FLAG:"0"}):
            self.assertEqual(self.post().status_code,404)
            self.assertNotIn("5p",self.client.get(self.url+"/available").get_json()["rph_variants"])
        self.assertEqual(self.client.post(self.url+"/download",json=self.payload).status_code,403)
        self.mocks[3].return_value=None
        self.assertEqual(self.post().status_code,401)
        self.mocks[3].return_value=123
        self.mocks[4].side_effect=c.PilotUnavailable("source missing")
        self.assertEqual(self.post().status_code,503)
        self.mocks[4].side_effect=None
        with patch.object(five,"render",side_effect=c.PilotUnavailable("render failed")):
            self.assertEqual(self.post().status_code,503)
        self.assertEqual(self.post({**self.payload,"teacher_students":"999"}).status_code,400)
        self.mocks[6].assert_not_called()
        res=self.post()
        self.assertEqual(res.status_code,200)
        self.assertEqual(res.headers["X-RPH-Trial-Remaining"],"9")
        self.assertEqual(res.headers["X-RPH-Variant"],"5p")
        self.assertIn("_5P",res.headers["Content-Disposition"])
        self.assertEqual(len(Document(BytesIO(res.data)).tables),1)
        self.mocks[6].assert_called_once()
        self.account["free_remaining"]=0
        self.assertEqual(self.post().status_code,403)
        self.mocks[6].assert_called_once()
    def test_paid_and_original(self):
        self.account["rakan_pembangun"]=True
        fields={"teacher_class":"1 Bestari","teacher_date":"2027-03-02","teacher_start":"08:00","teacher_end":"09:00","teacher_students":"30","reflection_mode":"manual","reflection":"Murid memerlukan latihan susulan."}
        for fmt in ("word","pdf"):
            res=self.post({**self.payload,"format":fmt,**fields})
            self.assertEqual(res.status_code,200)
            if fmt=="word":
                doc=Document(BytesIO(res.data));self.assertEqual(doc.tables[0].cell(20,1).text,fields["reflection"])
            else:
                with fitz.open(stream=res.data,filetype="pdf") as d:
                    self.assertEqual(len(d),1)
                    txt=d[0].get_text()
                    self.assertIn("1 Bestari",txt)
                    self.assertIn(fields["reflection"],txt)
        old=self.post({"group":"A","lesson":1,"format":"pdf"})
        self.assertEqual(old.status_code,200)
        self.assertEqual(old.data,self.asset)
        self.assertEqual(old.headers["X-RPH-Variant"],"lengkap")
        self.assertIn("LESSON001.pdf",old.headers["Content-Disposition"])
        self.mocks[6].assert_not_called()

if __name__=="__main__":unittest.main()
