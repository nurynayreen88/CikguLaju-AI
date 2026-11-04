"""RPT personalization: one-time name/logo, PDF source parity and paid gate."""
import io
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask, jsonify, request
from PIL import Image
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen.canvas import Canvas

from web import rpt2027_personalized_download_runtime as feature

ALL_CHOICES={
    "rpt2027_en_pdf_2":"english",
    "rpt2027_bm_pdf_2":"bm",
    "rpt2027_math_pdf_2":"math",
    "rpt2027_pi_pdf_2":"pi",
    "rpt2027_pjpk_pdf_2":"pjpk",
    "rpt2027_pm_ab_pdf_2":"pm",
    "rpt2027_psv_pdf_2":"psv",
}
def sample_png():
    image=Image.new("RGB",(220,120),(250,250,250))
    io_out=io.BytesIO()
    image.save(io_out,format="PNG")
    return io_out.getvalue()

def source_pdf(subject,year,folder):
    path=Path(folder)/("source_%s_%s.pdf"%(subject,year))
    c=Canvas(str(path),pagesize=landscape(A4))
    for text in ("ORIGINAL COVER","WEEK 01 LESSON 001","WEEK 02 LESSON 002"):
        c.setFont("Helvetica",18)
        c.drawString(80,340,text)
        c.showPage()
    c.save()
    return path

class PersonalizationTests(unittest.TestCase):
    def test_exact_subject_callbacks_and_school_name(self):
        for action,expected in ALL_CHOICES.items():
            self.assertEqual(feature.selection(action)[0],expected)
            self.assertEqual(feature.selection(action)[2],2)
        self.assertIsNone(feature.selection("rph_lesson_1"))
        self.assertEqual(feature.selection("rpt2027_psv_pdf_9")[2],None)
        self.assertEqual(feature.school_name(" Sekolah  Kebangsaan  Seri <Biru> "),
            "Sekolah Kebangsaan Seri Biru")
        self.assertEqual(feature.school_name("/pay"),"")
        self.assertEqual(feature.school_name("A"*100),"")
        self.assertTrue(feature.image_file_id({"photo":[{"file_id":"A"*30,"file_size":3400}]}))
        self.assertTrue(feature.image_file_id({"document":{"file_id":"B"*30,"mime_type":"image/png"}}))
        self.assertIsNone(feature.image_file_id({"document":{"file_id":"C"*30,"mime_type":"application/pdf"}}))

    def test_white_cover_preserves_source_pages_for_all_subjects(self):
        png=sample_png()
        with TemporaryDirectory() as d:
            root=Path(d)
            for action,subject in ALL_CHOICES.items():
                src=source_pdf(subject,2,root)
                dst=root/("personal_%s.pdf"%subject)
                result=feature.personalized_pdf(src,dst,"SEKOLAH KEBANGSAAN TAMAN BAHAGIA",
                                                png,subject,feature.selection(action)[1],2)
                pdf=PdfReader(str(result))
                skip=1 if subject in ("english","pm","psv") else 0
                self.assertEqual(len(pdf.pages),3+1-skip)
                self.assertIn("SEKOLAH KEBANGSAAN TAMAN BAHAGIA",
                              pdf.pages[0].extract_text())
                self.assertIn("WEEK 01",pdf.pages[-2].extract_text())
                self.assertIn("WEEK 02",pdf.pages[-1].extract_text())
                self.assertNotIn("ORIGINAL COVER",pdf.pages[0].extract_text())
                self.assertGreater(pdf.pages[0].mediabox.width,pdf.pages[0].mediabox.height)

    def _runtime(self):
        app=Flask("rpt_once_test")
        @app.route("/webhook",methods=["POST"])
        def webhook():
            return jsonify({"original":True})
        self.sent=[]
        self.finished=threading.Event()
        self.paid=True
        def send(cid,text,kb=None):
            self.sent.append(("text",str(text),kb))
            return SimpleNamespace(ok=True,json=lambda:{"ok":True})
        def send_document(cid,path,caption):
            pdf=PdfReader(str(path))
            self.sent.append(("pdf",str(caption),[p.extract_text() or "" for p in pdf.pages]))
            self.finished.set()
            return SimpleNamespace(ok=True,json=lambda:{"ok":True})
        rt=SimpleNamespace(
            app=app,request=request,jsonify=jsonify,API="https://api.telegram.org/botTEST",
            BOT_TOKEN="TEST",callback=lambda cid,data:("delegate",data),
            send=send,send_document=send_document,
            _is_admin=lambda cid:False,
            _access_info=lambda cid:{"active":self.paid},
            _telegram_delivery_ok_v25279=lambda result:result.ok)
        self.assertTrue(feature.install(rt))
        self.assertTrue(feature.install(rt))
        return rt,app.test_client()

    def test_one_input_per_download_no_profile_write_and_old_buttons(self):
        rt,client=self._runtime()
        self.assertEqual(rt.callback(99,"home"),("delegate","home"))
        self.paid=False
        rt.callback(99,"rpt2027_en_pdf_2")
        self.assertIn("hanya untuk",self.sent[-1][1])
        self.paid=True
        with patch.object(feature,"rpt_ready",return_value=True),\
             patch.object(feature,"download_logo",return_value=sample_png()),\
             patch.object(feature,"original_rpt",side_effect=source_pdf):
            for choice in ("rpt2027_en_pdf_2","rpt2027_pm_96_a_2"):
                self.finished.clear()
                rt.callback(99,choice)
                self.assertIn("taip nama sekolah",self.sent[-1][1])
                msg=lambda **kwargs:{"update_id":len(self.sent)+100,"message":{
                    "chat":{"id":99,"type":"private"},"from":{"id":99},**kwargs}}
                wrong=client.post("/webhook",json=msg(photo=[{"file_id":"A"*30,"file_size":1243}]))
                self.assertEqual(wrong.json["rpt_personalized"],True)
                self.assertIn("nama sekolah",self.sent[-1][1])
                client.post("/webhook",json=msg(text="SK SERI CAHAYA"))
                self.assertIn("hantar gambar",self.sent[-1][1])
                client.post("/webhook",json=msg(document={"file_id":"A"*30,"mime_type":"application/pdf"}))
                self.assertIn("JPG/PNG",self.sent[-1][1])
                client.post("/webhook",json=msg(photo=[{"file_id":"A"*30,"file_size":8000}]))
                self.assertTrue(self.finished.wait(timeout=12))
                self.assertEqual(self.sent[-1][0],"pdf")
                self.assertIn("SK SERI CAHAYA",self.sent[-1][2][0])
                self.assertIn("WEEK 02",self.sent[-1][2][-1])
            rt.callback(99,"rpt2027_bm_pdf_2")
            self.assertIn("taip nama sekolah",self.sent[-1][1])
            result=client.post("/webhook",json={"message":{"chat":{"id":99,"type":"private"},
                "from":{"id":99},"text":"/menu"},"update_id":80000})
            self.assertTrue(result.json["original"])
            self.assertEqual(rt.callback(99,"quick"),("delegate","quick"))
        self.assertFalse(hasattr(rt,"saved_logo"))
        self.assertFalse(hasattr(rt,"school_name"))

    def test_name_logo_not_mixed_with_other_users(self):
        rt,client=self._runtime()
        with patch.object(feature,"rpt_ready",return_value=True):
            rt.callback(11,"rpt2027_en_pdf_2")
            rt.callback(12,"rpt2027_bm_pdf_2")
        response=client.post("/webhook",json={"update_id":1,"message":{
            "chat":{"id":11,"type":"private"},"from":{"id":11},"text":"SEKOLAH 11"}})
        self.assertTrue(response.json["rpt_personalized"])
        response=client.post("/webhook",json={"update_id":2,"message":{
            "chat":{"id":12,"type":"private"},"from":{"id":12},"text":"SEKOLAH 12"}})
        self.assertTrue(response.json["rpt_personalized"])
        rt.callback(11,"rpt2027_logo_cancel")
        self.assertIn("dibatalkan",self.sent[-1][1])
        response=client.post("/webhook",json={"update_id":3,"message":{
            "chat":{"id":12,"type":"private"},"from":{"id":12},
            "document":{"mime_type":"application/pdf","file_id":"A"*30}}})
        self.assertTrue(response.json["rpt_personalized"])
        self.assertIn("JPG/PNG",self.sent[-1][1])

if __name__=="__main__":
    unittest.main()
