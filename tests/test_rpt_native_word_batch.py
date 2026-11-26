import unittest
from unittest.mock import patch
from pathlib import Path
from hashlib import sha256
from tempfile import TemporaryDirectory
from web import rpt_native_word_batch as batch
from web.rpt_2027_all_http import create_all_rpt_blueprint
from flask import Flask

class PrivateBatchTests(unittest.TestCase):
    def test_scope_and_default_off(self):
        self.assertEqual(len(batch.PINS),31)
        self.assertFalse(any(k.startswith(("bahasa_melayu:","english:","bahasa_arab:","pendidikan_islam:")) for k in batch.PINS))
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"0"}):
            self.assertFalse(batch.enabled())
    def test_source_digest_gate(self):
        with TemporaryDirectory() as folder, patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}):
            root=Path(folder)
            source=root/"web_2027_pdfs"/"muzik"/"tahun_2.pdf"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"%PDF-"+b"x"*8000)
            with patch.dict(batch.PINS,{"muzik:2":sha256(source.read_bytes()).hexdigest()}):
                self.assertTrue(batch.eligible("muzik",2,source,root=root))
                source.write_bytes(b"%PDF-"+b"y"*8000)
                self.assertFalse(batch.eligible("muzik",2,source,root=root))
    def test_entitlement_before_generation(self):
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint())
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}), patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9,"free_generations_remaining":10},None)), patch("web.rpt_2027_all_http.native_word.document") as generate:
            response=app.test_client().get("/api/rpt/2027/all/muzik/2.docx")
            self.assertEqual(response.status_code,403)
            generate.assert_not_called()
    def test_paid_attachment(self):
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint())
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}), patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9,"rakan_pembangun":True},None)), patch("web.rpt_2027_all_http._staged_file",return_value=Path("example.pdf")), patch("web_v1_telegram_auth_routes._config",return_value={}), patch("web.rpt_2027_all_http.native_word.document",return_value=(b"mock-docx","digest")):
            response=app.test_client().get("/api/rpt/2027/all/muzik/2.docx")
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.data,b"mock-docx")
            self.assertIn("attachment",response.headers["Content-Disposition"])
            self.assertEqual(response.headers["Cache-Control"],"no-store, private")
if __name__=="__main__": unittest.main()
