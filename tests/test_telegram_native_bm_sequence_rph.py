"""Native BM Word/PDF must use verified Telegram PdP sequence, not RPT row IDs."""
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from flask import Flask
from docx import Document
from tests.test_telegram_bm_hierarchy_web import seed_native_bm
from web_v1_dropdown_catalog import bm_sequence_token
from web.telegram_native_bm_sequence_rph_bridge import (
    _select, _state, create_native_bm_rph_blueprint, SourceUnavailable,
)


class NativeBMBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "master.db")
        seed_native_bm(self.db)
        self.runtime = Mock()
        self.runtime.DB_PATH = self.db
        self.runtime.CIKGULAJU_DB_V2600_ACTIVE = True
        def commit(s, mapped):
            s["grouped_sk_codes"] = [r["sk_code"] for r in mapped]
            s["grouped_sp_codes"] = [r["sp_code"] for r in mapped]
            s["sk_code"] = mapped[0]["sk_code"]
            s["sp_code"] = mapped[0]["sp_code"]
        self.runtime._commit_multi_sp.side_effect = commit
        self.runtime._local_rph_text.return_value = "Aktiviti PdP berdasarkan buku teks Bahasa Melayu.\n" * 25

        def word(s, content, unique):
            f = Path(tempfile.gettempdir()) / (unique + "_rph.docx")
            doc = Document()
            doc.add_paragraph("RPH Bahasa Melayu")
            doc.add_paragraph(content)
            doc.save(f)
            return str(f)
        self.runtime.create_word_file.side_effect = word
        self.token = bm_sequence_token(
            2, "Kekeluargaan", "1", "Keluargaku Sayang", "Ceria Pagi")
        app = Flask(__name__)
        app.register_blueprint(create_native_bm_rph_blueprint(self.runtime))
        self.client = app.test_client()
        self.env = {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
                    "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"x"*40}
        self.headers = {"Authorization":"Bearer "+"x"*40}
        self.query = {"year":"2","subject":"BM",
                      "unit":"Keluargaku Sayang","lesson":self.token}

    def tearDown(self):
        self.tmp.cleanup()

    def test_native_source_preserves_both_sps_and_correct_pages(self):
        s = _state(self.runtime,2,"Keluargaku Sayang",self.token,{
            "class":"2 Bestari","date":"2026-11-06",
            "time":"07:30 - 08:30","students":"30",
        })
        self.assertEqual(s["selected_sp_codes"], ["1.1.1","1.2.1"])
        self.assertEqual(s["rpt_theme"], "Kekeluargaan")
        self.assertEqual(s["textbook_ref"], "BT m/s 2–3")
        self.assertEqual(s["rph_date"], "06/11/2026")
        self.assertEqual(s["rph_class"], "2 Bestari")

    def test_rejects_wrong_unit_token_and_inactive_master(self):
        with self.assertRaises(SourceUnavailable):
            _select(self.runtime,2,"Keluargaku Sayang","b"+"0"*24)
        with self.assertRaises(SourceUnavailable):
            _select(self.runtime,2,"Unrelated",self.token)
        self.runtime.CIKGULAJU_DB_V2600_ACTIVE=False
        with self.assertRaises(SourceUnavailable):
            _select(self.runtime,2,"Keluargaku Sayang",self.token)

    def test_private_availability_and_actual_word_bytes(self):
        with patch.dict(os.environ,self.env):
            url="/internal/rph/v1/bm-sequence/availability"
            self.assertEqual(
                self.client.get(url,query_string=self.query).status_code,401)
            available=self.client.get(
                url,query_string=self.query,headers=self.headers)
            self.assertEqual(available.status_code,200,available.json)
            response=self.client.post(
                "/internal/rph/v1/bm-sequence/render",
                json={"selection":{"year":2,"subject":"BM",
                                   "unit":"Keluargaku Sayang",
                                   "lesson":self.token},
                      "teacher":{"class":"2 Bestari","date":"2026-11-06",
                                 "time":"07:30 - 08:30","students":"30"},
                      "format":"word"},
                headers=self.headers)
            self.assertEqual(response.status_code,200,response.json if response.is_json else response.data[:120])
            self.assertTrue(response.data.startswith(b"PK"))
            doc = Document(io.BytesIO(response.data))
            self.assertIn("RPH Bahasa Melayu",doc.paragraphs[0].text)


if __name__=="__main__":
    unittest.main()
