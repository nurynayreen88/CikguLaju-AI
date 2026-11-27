"""No credentials, private bytes or real quota changes in these tests."""
import base64
import hashlib
import io
import json
import os
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from web import kp2027_alam_5p_templates as a
from test_kp2027_alam_private_web import AlamFlaskContract

BASE="/api/kp2027/sk/tahun-1/alam-dan-manusia/5p"

class ArchiveTests(unittest.TestCase):
    def test_archive_pinning(self):
        data=b"test"
        b=base64.b64encode(data).decode()
        with patch.object(a,"PART_LENGTHS",[len(b)]),patch.object(a,"ARCHIVE_BYTES",len(data)),patch.object(a,"ARCHIVE_SHA",hashlib.sha256(data).hexdigest()):
            self.assertEqual(a.decode_archive([{"part_no":1,"content_base64":b}]),data)
            for bad in ([],[{"part_no":2,"content_base64":b}],[{"part_no":1,"content_base64":"A"*len(b)}]):
                with self.assertRaises(a.PilotUnavailable):a.decode_archive(bad)

    def test_document_index_and_hash(self):
        data=b"%PDF-1.7\n"+b"0"*1500
        raw=io.BytesIO()
        records=[{"rpt_pdp":n,"filename":f"CIKGULAJU_ALAM_KP2027_T1_PDP{n:03d}_5P_QA","pdf_sha256":hashlib.sha256(data).hexdigest(),"sp":"1.1.1"} for n in range(1,94)]
        with ZipFile(raw,"w") as z:
            z.writestr("manifest.json",json.dumps({"records":records}))
            z.writestr("PDF/"+records[-1]["filename"]+".pdf",data)
        self.assertEqual(a.select_document(raw.getvalue(),93,"pdf"),data)
        for n,fmt in ((0,"pdf"),(94,"pdf"),(True,"pdf"),(93,"zip"),(1,"pdf")):
            with self.assertRaises(a.PilotUnavailable):a.select_document(raw.getvalue(),n,fmt)

class FivePRouteTests(AlamFlaskContract):
    def test_separate_route_guards(self):
        client,mocks=self.client(paid=False)
        with patch.dict(os.environ,{a.FLAG:"0"}):
            self.assertEqual(client.get(BASE+"/available").status_code,404)
        with patch.dict(os.environ,{a.FLAG:"1"}),patch.object(a,"render",return_value=b"%PDF-1.7\n"+b"0"*1500) as fetch:
            self.assertEqual(client.post(BASE+"/download",json={"pdp":93,"format":"pdf"}).status_code,403)
            self.assertEqual(client.post(BASE+"/download",json={"pdp":94,"format":"pdf"},headers={"Origin":"https://cikgulaju-web.onrender.com"}).status_code,404)
            self.assertEqual(mocks[4].call_count,0)
            self.assertEqual(fetch.call_count,0)
            r=client.post(BASE+"/download",json={"pdp":93,"format":"pdf"},headers={"Origin":"https://cikgulaju-web.onrender.com"})
            self.assertEqual(r.status_code,200)
            self.assertEqual(r.headers["X-RPH-Trial-Remaining"],"9")
            self.assertEqual(mocks[4].call_count,1)
            self.assertIn("PDP093_5P",r.headers["Content-Disposition"])
            fetch.side_effect=a.PilotUnavailable("bad")
            self.assertEqual(client.post(BASE+"/download",json={"pdp":93,"format":"pdf"},headers={"Origin":"https://cikgulaju-web.onrender.com"}).status_code,503)
            self.assertEqual(mocks[4].call_count,1)
            from web.kp2027_alam_5p_personalize import LayoutError
            fetch.side_effect=LayoutError("Refleksi tidak muat")
            self.assertEqual(client.post(BASE+"/download",json={"pdp":93,"format":"pdf","reflection_mode":"manual","reflection":"ujian"},headers={"Origin":"https://cikgulaju-web.onrender.com"}).status_code,400)
            self.assertEqual(mocks[4].call_count,1)
            mocks[2].return_value=None
            self.assertEqual(client.get(BASE+"/available").status_code,401)
