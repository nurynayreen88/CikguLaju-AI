import unittest
import json
import os
from unittest.mock import patch
from hashlib import sha256
from types import SimpleNamespace
from flask import Flask
from web.unified_rph_web import create_blueprint, source_records
from web import worksheet_complete_pdf as ws

class WorksheetTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        self.client = app.test_client()
        row = next(x for x in source_records(3, "ENGLISH") if x["lesson"] == 1)
        self.query = {"year": 3, "subject": "ENGLISH", "unit": row["unit"], "lesson": row["token"]}
        self.raw = b"%PDF-1.7\n" + b"X"*1000

    def account(self):
        return patch("web.unified_rph_web._account", return_value=(
            {"telegram_user_id": 1, "authenticated": True, "free_remaining": 1}, None))

    def test_all_26_source_matches(self):
        records, index = ws._sources()
        self.assertEqual(len(records), 26)
        for key, rec in records.items():
            y, n = map(int, key.split("/"))
            rows = [r for r in source_records(y, "ENGLISH") if r["lesson"] == n]
            self.assertEqual(len(rows), 1)
            self.assertEqual(ws.resolve(y,n,rows[0]["unit"]), rec)
        self.assertIsNone(ws.resolve(3,1,"wrong"))
        self.assertIsNotNone(ws.resolve(3,17,"Every day"))
        self.assertIsNotNone(ws.resolve(3,18,"Every day"))
        self.assertIsNone(ws.resolve(3,19,"Every day"))
        self.assertIsNone(ws.resolve(4,1,"Welcome!"))
        self.assertIsNone(ws.resolve(True,1,"Welcome!"))

    def test_one_button_and_download_no_debit(self):
        bridge = "web.native_telegram_extra_materials_20261106."
        with (self.account(), patch.object(ws, "_pdf", return_value=self.raw),
              patch(bridge+"english_workbook_metadata",return_value=None),
              patch(bridge+"english_student_book_metadata",return_value=None),
              patch(bridge+"english_audio_tracks",return_value=[])):
            reply = self.client.get("/api/web/rph/extra-materials",query_string=self.query)
            self.assertEqual(reply.status_code, 200)
            items = [x for x in reply.json["items"] if x["type"] == "worksheet"]
            self.assertEqual(len(items),1)
            self.assertEqual(items[0]["action"],"Download PDF")
            self.assertNotIn("drive",items[0]["url"])
            response = self.client.get(items[0]["url"])
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.data,self.raw)
            self.assertEqual(response.mimetype,"application/pdf")
            self.assertIn("L001.pdf",response.headers["Content-Disposition"])
            self.assertEqual(response.headers["Cache-Control"],"no-store, private")

    def test_denied_and_wrong_selection(self):
        url="/api/web/rph/worksheet-pdf"
        with patch("web.unified_rph_web._account",return_value=(None,({"error":"Login"},401))):
            self.assertEqual(self.client.get(url,query_string=self.query).status_code,401)
        with self.account(), patch.object(ws,"_pdf") as fetch:
            self.assertEqual(self.client.get(url,query_string={**self.query,"unit":"wrong"}).status_code,404)
            self.assertEqual(self.client.get(url,query_string={**self.query,"paired":"1"}).status_code,404)
            fetch.assert_not_called()

    def test_failed_source_does_not_hide_existing_workbook(self):
        bridge="web.native_telegram_extra_materials_20261106."
        with (self.account(),patch.object(ws,"_pdf",side_effect=OSError("offline")),
              patch(bridge+"english_workbook_metadata",return_value="Workbook"),
              patch(bridge+"english_student_book_metadata",return_value=None),
              patch(bridge+"english_audio_tracks",return_value=[])):
            reply=self.client.get("/api/web/rph/extra-materials",query_string=self.query)
            self.assertEqual(reply.status_code,200)
            self.assertFalse(any(x["type"]=="worksheet" for x in reply.json["items"]))
            self.assertTrue(any(x["type"]=="workbook" for x in reply.json["items"]))

    def test_byte_integrity(self):
        from unittest.mock import MagicMock
        digest = sha256(self.raw).hexdigest()
        response=MagicMock()
        response.status=200
        response.headers.get_content_type.return_value="application/json"
        response.read.return_value=json.dumps([{
            "asset_sha256":digest,"size_bytes":len(self.raw),
            "pdf_bytes":"\\x"+self.raw.hex()}]).encode()
        opener=MagicMock()
        opener.open.return_value.__enter__.return_value=response
        ws._pdf.cache_clear()
        with patch.dict(os.environ,{"SUPABASE_URL":"https://example.supabase.co","SUPABASE_SECRET_KEY":"sb_secret_test"}), patch.object(ws,"build_opener",return_value=opener):
            self.assertEqual(ws._pdf("validid_123456",digest,len(self.raw)),self.raw)
            req=opener.open.call_args.args[0]
            self.assertIn("/rest/v1/cikgulaju_worksheet_pdf_assets?",req.full_url)
            self.assertIn(digest,req.full_url)
            self.assertNotIn("validid_123456",req.full_url)
            self.assertEqual(req.get_header("Apikey"),"sb_secret_test")
            self.assertIsNone(req.get_header("Authorization"))
            with self.assertRaises(ValueError):
                ws._pdf("validid_123456","0"*64,len(self.raw))
            ws._pdf.cache_clear()
            response.read.return_value=json.dumps([{
                "asset_sha256":digest,"size_bytes":len(self.raw),
                "pdf_bytes":"\\x"+(self.raw[:-1]+b"Y").hex()}]).encode()
            with self.assertRaises(ValueError):
                ws._pdf("validid_123456",digest,len(self.raw))
        ws._pdf.cache_clear()

class BMWorksheetTests(unittest.TestCase):
    def setUp(self):
        from web import bm_worksheet_complete_pdf as bm
        self.bm = bm
        self.token = "b" + "1"*24
        self.unit = "Hidup Berjiran"
        self.identity = {"available":True,"year":2,"subject":"BM",
                         "unit":self.unit,"token":self.token,
                         "topic":"Majlis Pengikat Kemesraan",
                         "standards":[{"sk":"2.2","sp":"2.2.1"}]}

    def test_exact_native_identity_only(self):
        from unittest.mock import MagicMock
        opener=MagicMock()
        response=opener.open.return_value.__enter__.return_value
        response.status=200
        with patch.object(self.bm,"_backend",return_value=("https://example.test","secret")):
            response.read.return_value=json.dumps(self.identity).encode()
            self.assertIsNotNone(self.bm.resolve_bm(2,self.unit,self.token,opener=opener))
            for invalid in [{"topic":"Other"}, {"token":"b"+"0"*24},
                            {"standards":[{"sk":"2.1","sp":"2.2.1"}]},
                            {"standards":[{"sk":"2.2","sp":"2.2.1"},{"sk":"3.1","sp":"3.1.1"}]}]:
                response.read.return_value=json.dumps({**self.identity,**invalid}).encode()
                self.assertIsNone(self.bm.resolve_bm(2,self.unit,self.token,opener=opener))
            self.assertIsNone(self.bm.resolve_bm(2,"Hari Minggu dengan Keluarga",self.token,opener=opener))

    def test_bm_one_button_and_attachment(self):
        app=Flask(__name__)
        app.register_blueprint(create_blueprint())
        client=app.test_client()
        query={"year":2,"subject":"BM","unit":self.unit,"lesson":self.token}
        raw=b"%PDF-1.7\n"+b"X"*1000
        filename="CIKGULAJU_LATIHAN_BM_T2_MAJLIS_PENGIKAT_KEMESRAAN.pdf"
        with patch("web.unified_rph_web._account",return_value=(
                {"telegram_user_id":1,"authenticated":True,"free_remaining":1},None)):
            with patch.object(self.bm,"complete_bm_pdf",return_value=(raw,filename)):
                result=client.get("/api/web/rph/extra-materials",query_string=query)
                self.assertEqual(result.status_code,200)
                self.assertEqual(len(result.json["items"]),1)
                item=result.json["items"][0]
                self.assertEqual(item["type"],"worksheet")
                self.assertEqual(item["action"],"Download PDF")
                answer=client.get(item["url"])
                self.assertEqual(answer.status_code,200)
                self.assertEqual(answer.data,raw)
                self.assertIn(filename,answer.headers["Content-Disposition"])
            with patch.object(self.bm,"complete_bm_pdf",return_value=None):
                self.assertEqual(client.get("/api/web/rph/extra-materials",query_string=query).json["items"],[])
                self.assertEqual(client.get("/api/web/rph/worksheet-pdf",query_string=query).status_code,404)

if __name__ == "__main__":
    unittest.main()
