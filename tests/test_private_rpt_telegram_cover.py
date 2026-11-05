"""Telegram private RPT personalization: original page retention and strict hash auth."""
import base64
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from flask import Flask
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from PIL import Image

from web.native_rpt_telegram_api import create_private_rpt_blueprint, validate_payload, select_source


class ProtectedRptTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.root=Path(self.temp.name)
        path=self.root/"english"/"RPT_ENGLISH_TAHUN_2_2027_UNTUK_GURU.pdf"
        path.parent.mkdir(parents=True,exist_ok=True)
        b=BytesIO();c=canvas.Canvas(b,pagesize=(842,595),pageCompression=0)
        for page in range(12):
            c.setFont("Helvetica",13)
            c.drawString(30,500,"RPT English ORIGINAL page "+str(page+1))
            for n in range(22):
                c.drawString(30,450-n*16,"Source activity %03d on page %02d" % (n,page))
            c.showPage()
        c.save()
        path.write_bytes(b.getvalue())
        self.assertGreater(path.stat().st_size,8000)
        self.path=path
        image=BytesIO()
        Image.new("RGBA",(100,100),(0,90,60,180)).save(image,format="PNG")
        self.body={
            "subject":"english","year":2,
            "source_sha256":sha256(path.read_bytes()).hexdigest(),
            "school":"SK Sejahtera","teacher":"Cikgu Ali",
            "state":"Johor",
            "logo":base64.b64encode(image.getvalue()).decode("ascii"),
        }
        app=Flask(__name__)
        app.register_blueprint(create_private_rpt_blueprint(root=self.root))
        self.client=app.test_client()
        self.env={"CIKGULAJU_AUTHORITATIVE_API_TOKEN":"a"*64,
                  "CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1"}

    def tearDown(self):
        self.temp.cleanup()

    def post(self,payload=None,token=None):
        return self.client.post("/internal/rpt/v1/personalize",
            json=self.body if payload is None else payload,
            headers={"Authorization":"Bearer "+(token if token is not None else "a"*64)})

    def test_authenticated_render_keeps_original_pages(self):
        before=self.path.read_bytes()
        with patch.dict(os.environ,self.env):
            r=self.post()
        self.assertEqual(r.status_code,200,r.get_json(silent=True))
        self.assertEqual(r.mimetype,"application/pdf")
        self.assertEqual(r.headers["Cache-Control"],"no-store, private")
        pages=PdfReader(BytesIO(r.data)).pages
        self.assertEqual(len(pages),13)
        self.assertIn("SK Sejahtera",pages[0].extract_text())
        self.assertIn("2027",pages[0].extract_text())
        self.assertIn("Tahun 2",pages[0].extract_text())
        self.assertIn("Johor",pages[0].extract_text())
        self.assertIn("ORIGINAL page 1",pages[1].extract_text())
        self.assertIn("ORIGINAL page 12",pages[12].extract_text())
        self.assertEqual(before,self.path.read_bytes())

    def test_missing_token_and_changed_source_are_blocked(self):
        with patch.dict(os.environ,self.env):
            self.assertEqual(self.post(token="wrong").status_code,401)
            altered={**self.body,"source_sha256":"0"*64}
            r=self.post(payload=altered)
            self.assertEqual(r.status_code,409)
            self.assertNotIn(b"SK Sejahtera",r.data)
            invalid={**self.body,"year":1}
            self.assertEqual(self.post(payload=invalid).status_code,409)

    def test_no_arbitrary_paths_and_missing_pdf(self):
        with self.assertRaises(ValueError):
            select_source("../secret",2,root=self.root)
        with self.assertRaises(ValueError):
            validate_payload({**self.body,"subject":"psv"},root=self.root)


if __name__=="__main__":
    unittest.main()
