"""Five editable BM KSSR 2027 source-verified Word downloads, paid only.

Uses synthetic account snapshots and repository-controlled Word source files.
Never reads production sessions, writes billing, or touches teacher profiles.
"""
from __future__ import annotations

from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path
import re
from unittest.mock import patch
import unittest

from docx import Document
from flask import Flask
from web.rpt_2027_all_http import create_all_rpt_blueprint
from web.rpt_2027_kssr_bm_word import YEARS, word_document

ROOT=Path(__file__).resolve().parents[1]
PREFIX="/api/rpt/2027/all/bahasa_melayu/"


class TestKSSRWordBMTahun2to6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=Flask(__name__)
        cls.app.register_blueprint(create_all_rpt_blueprint())
        cls.client=cls.app.test_client()

    def test_all_five_source_word_documents_have_exact_semantic_pdp_counts(self):
        expected={2:164,3:165,4:165,5:166,6:165}
        manifest=json.loads((ROOT/"rpt_2027/kssr_word_premium/manifest.json").read_text("utf-8"))
        self.assertFalse(manifest["academic_final"])
        self.assertTrue(manifest["original_pdf_manifest_untouched"])
        self.assertEqual(sum(v["pdp"] for v in manifest["files"].values()),825)
        for year in YEARS:
            with self.subTest(year=year):
                source=word_document(year)
                self.assertIsNotNone(source)
                path,digest=source
                self.assertEqual(sha256(path.read_bytes()).hexdigest(),digest)
                doc=Document(path)
                self.assertEqual(len(doc.tables),44)
                ids=[]
                for table in doc.tables:
                    for row in table.rows[1:]:
                        m=re.match(r"PdP\s+(\d{3})\b",row.cells[4].text)
                        if m:ids.append(int(m.group(1)))
                self.assertEqual(ids,list(range(1,expected[year]+1)))
                self.assertTrue(any("DRAF SEMAKAN" in p.text for p in doc.paragraphs))
                for table in doc.tables:
                    self.assertEqual(len(table.columns),5)
                item=manifest["files"][str(year)]
                self.assertEqual(item["source_html_sha256"],
                                 sha256((ROOT/item["source_html"]).read_bytes()).hexdigest())

    def test_authenticated_free_user_gets_pdf_not_word(self):
        with patch("web.rpt_2027_all_http._account",
                   return_value=({"telegram_user_id":22,
                                  "free_generations_remaining":10},None)), \
             patch("web.rpt_2027_all_http._has_paid_access",return_value=False):
            data=self.client.get("/api/rpt/2027/catalog").get_json()
            bm=next(x for x in data["subjects"] if x["code"]=="bahasa_melayu")
            for year in YEARS:
                meta=next(v for v in bm["years"] if v["year"]==year)
                self.assertTrue(meta["pdf_ready"])
                self.assertTrue(meta["download_enabled"])
                self.assertFalse(meta["docx_ready"])
                self.assertIsNone(meta["docx_url"])
                r=self.client.get(PREFIX+str(year)+".docx")
                self.assertEqual(r.status_code,403)
                self.assertIn("Rakan Pembangun",r.get_json()["error"])

    def test_paid_founder_and_active_subscription_download_all_five_docx(self):
        accounts=(
          {"telegram_user_id":23,"rakan_pembangun":True},
          {"telegram_user_id":24,"vip_until":(date.today()+timedelta(days=20)).isoformat()},
        )
        for account in accounts:
            with self.subTest(telegram_user_id=account["telegram_user_id"]), \
                 patch("web.rpt_2027_all_http._account",return_value=(account,None)):
                data=self.client.get("/api/rpt/2027/catalog").get_json()
                self.assertTrue(data["personalization_allowed"])
                bm=next(x for x in data["subjects"] if x["code"]=="bahasa_melayu")
                for year in YEARS:
                    meta=next(v for v in bm["years"] if v["year"]==year)
                    self.assertTrue(meta["docx_ready"])
                    self.assertEqual(meta["docx_url"],PREFIX+str(year)+".docx")
                    r=self.client.get(PREFIX+str(year)+".docx")
                    self.assertEqual(r.status_code,200)
                    self.assertEqual(r.data,word_document(year)[0].read_bytes())
                    self.assertIn("attachment",r.headers["Content-Disposition"])
                    self.assertIn("WORD.docx",r.headers["Content-Disposition"])
                    self.assertEqual(r.headers["X-RPT-Source-SHA256"],sha256(r.data).hexdigest())
                    self.assertEqual(r.headers["X-RPT-Academic-Status"],"DRAF_SEMAKAN")
                    self.assertEqual(r.headers["Cache-Control"],"no-store, private")

    def test_expired_account_denied_and_unreleased_formats_404(self):
        account={"telegram_user_id":25,
                 "vip_until":(date.today()-timedelta(days=1)).isoformat()}
        with patch("web.rpt_2027_all_http._account",return_value=(account,None)):
            self.assertEqual(self.client.get(PREFIX+"2.docx").status_code,403)
            self.assertEqual(self.client.get("/api/rpt/2027/all/sains/2.docx").status_code,404)
            self.assertEqual(self.client.get(PREFIX+"1.docx").status_code,404)
            self.assertEqual(self.client.get(PREFIX+"7.docx").status_code,404)


if __name__=="__main__":
    unittest.main()
