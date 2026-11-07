"""58? No: exactly 56 RPT PDF drafts across 12 subjects, paid-gated.

Synthetic files and monkeypatched account lookups; never touch production
user records or actual trial credits.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from web.rpt_2027_all_http import (
    SUBJECTS,expected_pairs,catalog_data,create_all_rpt_blueprint,pdf_path,pdf_ready
)

class WebRPT2027FiftySixQA(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.pdf=b"%PDF-"+b"x"*9000
        self.base=self.root/"web_2027_pdfs"
        self.base.mkdir()
        files={}
        for key in sorted(expected_pairs()):
            code,year=key.split(":")
            rel=f"{code}/tahun_{year}.pdf"
            dest=self.base/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(self.pdf)
            files[key]={"path":rel,"sha256":hashlib.sha256(self.pdf).hexdigest(),
                        "bytes":len(self.pdf),"pages":2,"status":"DRAF"}
        self.manifest={
            "version":1,"year":2027,"status":"DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL",
            "count":56,"files":files,
        }
        self._save()
        self.app=Flask(__name__)
        self.app.register_blueprint(create_all_rpt_blueprint(root=self.root))
        self.client=self.app.test_client()
    def tearDown(self):
        self.tmp.cleanup()
    def _save(self):
        (self.base/"manifest.json").write_text(json.dumps(self.manifest),encoding="utf-8")
    def test_all_56_files_and_12_subjects_only(self):
        data=catalog_data(root=self.root,allowed=True)
        self.assertEqual(len(data["subjects"]),12)
        self.assertEqual(data["total_rpt"],56)
        self.assertEqual(data["available_rpt"],56)
        self.assertEqual(sum(len(x["years"]) for x in data["subjects"]),66)
        self.assertEqual(data["total_display_choices"],66)
        self.assertEqual(data["year1_coming_soon"],10)
        self.assertTrue(all(y["download_enabled"] and y["pdf_ready"]
                            for s in data["subjects"] for y in s["years"] if y["year"]>=2))
        self.assertEqual(len([y for s in data["subjects"] for y in s["years"]
                              if y["year"]==1]),10)
        self.assertTrue(all(not y["download_enabled"] and not y["pdf_ready"]
                            and y["status"].startswith("KP2027")
                            for s in data["subjects"] for y in s["years"] if y["year"]==1))
        self.assertEqual(set(SUBJECTS["rbt"][1]),{4,5,6})
        self.assertEqual(set(SUBJECTS["sejarah"][1]),{4,5,6})
        self.assertNotIn("sains:1",expected_pairs())
        self.assertTrue(pdf_ready("sains",6,root=self.root))
        self.assertFalse(pdf_ready("sains",1,root=self.root))
        self.assertNotIn(1,[r["year"] for x in data["subjects"] if x["code"]=="rbt" for r in x["years"]])
        self.assertNotIn(1,[r["year"] for x in data["subjects"] if x["code"]=="sejarah" for r in x["years"]])
        with self.assertRaises(ValueError):
            pdf_path("rbt",2,root=self.root)

    def test_manifest_sha_tampering_blocks_only_corrupt_pdf(self):
        self.manifest["files"]["sains:6"]["sha256"]="0"*64
        self._save()
        data=catalog_data(root=self.root,allowed=True)
        self.assertEqual(data["available_rpt"],55)
        self.assertFalse(pdf_ready("sains",6,root=self.root))
        self.assertTrue(pdf_ready("sains",5,root=self.root))

    def test_incomplete_manifest_not_misrepresented_as_56_ready(self):
        del self.manifest["files"]["english:3"]
        self._save()
        self.assertEqual(catalog_data(root=self.root,allowed=True)["available_rpt"],0)

    def test_paid_user_downloads_exact_pdf_no_trial_credit_change(self):
        paid={"telegram_user_id":42,"authenticated":True,"rakan_pembangun":True}
        with (patch("web.rpt_2027_all_http._account",return_value=(paid,None)),
              patch("web.rpt_2027_all_http._has_paid_access",return_value=True)):
            catalog=self.client.get("/api/rpt/2027/catalog")
            self.assertEqual(catalog.status_code,200)
            self.assertEqual(catalog.get_json()["available_rpt"],56)
            pdf=self.client.get("/api/rpt/2027/all/bahasa_arab/6.pdf")
            self.assertEqual(pdf.status_code,200)
            self.assertEqual(pdf.data,self.pdf)
            self.assertEqual(pdf.mimetype,"application/pdf")
            self.assertIn("attachment",pdf.headers["Content-Disposition"])
            self.assertEqual(pdf.headers["Cache-Control"],"no-store, private")

    def test_unpaid_user_sees_all_but_cannot_download(self):
        trial={"telegram_user_id":42,"authenticated":True,"free_remaining":10}
        with (patch("web.rpt_2027_all_http._account",return_value=(trial,None)),
              patch("web.rpt_2027_all_http._has_paid_access",return_value=False)):
            catalog=self.client.get("/api/rpt/2027/catalog")
            self.assertEqual(catalog.status_code,200)
            self.assertEqual(catalog.get_json()["available_rpt"],56)
            self.assertFalse(catalog.get_json()["allowed"])
            result=self.client.get("/api/rpt/2027/all/english/2.pdf")
            self.assertEqual(result.status_code,403)

    def test_unauthenticated_blocked_and_invalid_year_404(self):
        from flask import jsonify
        with patch("web.rpt_2027_all_http._account",
                   side_effect=lambda:(None,(jsonify({"error":"Login required"}),401))):
            self.assertEqual(self.client.get("/api/rpt/2027/catalog").status_code,401)
        with (patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":42},None)),
              patch("web.rpt_2027_all_http._has_paid_access",return_value=True)):
            self.assertEqual(self.client.get("/api/rpt/2027/all/rbt/2.pdf").status_code,404)
            self.assertEqual(self.client.get("/api/rpt/2027/all/sains/1.pdf").status_code,404)
            self.assertEqual(self.client.get("/api/rpt/2027/all/english/1.pdf").status_code,404)
            self.assertEqual(self.client.get("/api/rpt/2027/all/../../etc/passwd").status_code,404)

if __name__=="__main__":
    unittest.main()
