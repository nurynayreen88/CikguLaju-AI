import os
import unittest
from io import BytesIO
from unittest.mock import patch
from flask import Flask
from docx import Document
import fitz
from web import kp2027_bm_rpt_aligned as bm, kp2027_bm_5p as five, kp2027_bm_rph_web as web

class TestFiveP(unittest.TestCase):
    def test_complete_and_native_pdf(self):
        self.assertEqual(len(five.companions()),353)
        for g,count in bm.COUNTS.items():
            for n in range(1,count+1):
                with self.subTest(g=g,n=n):
                    src,c,raw,profile=five.prepare(g,n,{})
                    r=bm.lesson(g,n)
                    self.assertEqual(src["sp"],r["sp_code"]+" "+r["sp"])
                    self.assertEqual(src["criteria"],r["criteria"])
                    with fitz.open(stream=five.render_pdf(src,c,profile),filetype="pdf") as doc:
                        self.assertEqual(len(doc),1)
                        txt=" ".join(doc[0].get_text().split())
                        for label in ("Penglibatan","Penerokaan","Penerangan","Pengembangan","Penilaian","Refleksi",r["sp_code"]):
                            self.assertIn(label,txt)
                        self.assertIn(r["criteria"],txt)
    def test_personalized_both_formats(self):
        fields={"teacher_class":"1 Bestari","teacher_date":"2027-03-02","teacher_start":"08:00",
                "teacher_end":"09:00","teacher_students":"30","reflection_mode":"manual",
                "reflection":"Murid memerlukan latihan susulan."}
        for g,n in (("A",1),("A",31),("B",175)):
            word=Document(BytesIO(five.render(g,n,"word",fields)))
            self.assertEqual(len(word.tables),1)
            self.assertEqual(len(word.tables[0].rows),21)
            self.assertIn("1 Bestari",word.tables[0].cell(1,0).text)
            self.assertEqual(word.tables[0].cell(20,1).text,fields["reflection"])
            with fitz.open(stream=five.render(g,n,"pdf",fields),filetype="pdf") as d:
                self.assertEqual(len(d),1)
                t=" ".join(d[0].get_text().split())
                for item in ("1 Bestari","02/03/2027","08:00","30",fields["reflection"]):
                    self.assertIn(item,t)
    def test_access_and_original_unchanged(self):
        app=Flask(__name__);app.config["TESTING"]=True;app.register_blueprint(web.create_blueprint())
        c=app.test_client()
        url="/api/kp2027/sk/tahun-1/bahasa-melayu-sk"
        payload={"group":"A","lesson":1,"format":"word","rph_variant":"5p"}
        origin={"Origin":web.ORIGIN}
        with patch.dict(os.environ,{"CIKGULAJU_BM_KP2027_5P_ENABLED":"1"}),patch.object(web,"_config",return_value={"account_backend":"supabase","CIKGULAJU_WEB_SESSION_SECRET":"s"*40,"supabase_url":"https://example.supabase.co","supabase_key":"unused"}),patch.object(web,"verify_session_ticket",return_value=42),patch.object(web,"_lookup",return_value={"telegram_user_id":42,"authenticated":True,"free_remaining":10,"rakan_pembangun":True}),patch.object(web,"debit_shared_trial") as debit:
            self.assertIn("5p",c.get(url+"/available").get_json()["rph_variants"])
            self.assertEqual(c.post(url+"/download",json=payload).status_code,403)
            out=c.post(url+"/download",json=payload,headers=origin)
            self.assertEqual(out.status_code,200)
            self.assertEqual(out.headers["X-RPH-Variant"],"5p")
            self.assertIn("_5P_",out.headers["Content-Disposition"])
            self.assertEqual(len(Document(BytesIO(out.data)).tables),1)
            original={k:v for k,v in payload.items() if k!="rph_variant"}
            old=c.post(url+"/download",json=original,headers=origin)
            self.assertEqual(old.status_code,200)
            self.assertEqual(len(Document(BytesIO(old.data)).tables),2)
            self.assertFalse(debit.called)
            with patch.dict(os.environ,{"CIKGULAJU_BM_KP2027_5P_ENABLED":"0"}):
                self.assertEqual(c.post(url+"/download",json=payload,headers=origin).status_code,404)
                self.assertNotIn("5p",c.get(url+"/available").get_json()["rph_variants"])

if __name__=="__main__":unittest.main()
