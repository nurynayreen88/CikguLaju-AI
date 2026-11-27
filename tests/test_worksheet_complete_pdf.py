import unittest
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

    def test_all_24_source_matches(self):
        records, index = ws._sources()
        self.assertEqual(len(records), 24)
        for key, rec in records.items():
            y, n = map(int, key.split("/"))
            rows = [r for r in source_records(y, "ENGLISH") if r["lesson"] == n]
            self.assertEqual(len(rows), 1)
            self.assertEqual(ws.resolve(y,n,rows[0]["unit"]), rec)
        self.assertIsNone(ws.resolve(3,1,"wrong"))
        self.assertIsNone(ws.resolve(3,17,"Every day"))
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
        response=MagicMock()
        response.status=200
        response.headers.get_content_type.return_value="application/pdf"
        response.read.return_value=self.raw
        opener=MagicMock()
        opener.open.return_value.__enter__.return_value=response
        ws._pdf.cache_clear()
        with patch.object(ws,"build_opener",return_value=opener):
            self.assertEqual(ws._pdf("validid_123456",sha256(self.raw).hexdigest(),len(self.raw)),self.raw)
            with self.assertRaises(ValueError):
                ws._pdf("validid_123456","0"*64,len(self.raw))
        ws._pdf.cache_clear()

if __name__ == "__main__":
    unittest.main()
