"""RPT Word paid-only authorization gate: founder/active VIP, not trial credits.

All tests use synthetic authenticated account snapshots. No account DB writes,
payment processing, Telegram, quota decrement or external network.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from unittest.mock import patch
import unittest

from flask import Flask
from web.english_rpt_2027_http import _has_paid_access
from web.rpt_2027_all_http import create_all_rpt_blueprint
from web.kp2027_year1_rpt_combined import SUBJECTS, document

PREFIX="/api/rpt/2027/kp2027/tahun-1/gabungan/"


class RPTWordPaidOnlyGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app=Flask(__name__)
        app.register_blueprint(create_all_rpt_blueprint())
        cls.client=app.test_client()

    def test_rakan_pembangun_and_active_subscription_only(self):
        now=datetime.now(timezone.utc)
        profiles={
            "founder":{"telegram_user_id":11,"rakan_pembangun":True},
            "monthly_active":{"telegram_user_id":12,
                             "vip_expires_at":(now+timedelta(days=15)).isoformat()},
            "annual_active":{"telegram_user_id":13,
                            "vip_until":(date.today()+timedelta(days=20)).isoformat()},
            "trial":{"telegram_user_id":14,"free_generations_remaining":10},
            "expired":{"telegram_user_id":15,
                       "vip_expires_at":(now-timedelta(days=1)).isoformat()},
            "expired_date":{"telegram_user_id":16,
                           "vip_until":(date.today()-timedelta(days=1)).isoformat()},
            "fake_flag":{"telegram_user_id":17,"rakan_pembangun":"true"},
        }
        for label,account in profiles.items():
            with self.subTest(account=label):
                self.assertEqual(_has_paid_access(account),
                                 label in {"founder","monthly_active","annual_active"})

    def test_free_catalog_has_pdf_but_never_releases_word_endpoint(self):
        account={"telegram_user_id":21,"rakan_pembangun":False,
                 "free_generations_remaining":10}
        with patch("web.rpt_2027_all_http._account",return_value=(account,None)):
            catalogue=self.client.get("/api/rpt/2027/catalog").get_json()
            self.assertFalse(catalogue["personalization_allowed"])
            options=catalogue["kp2027_rpt_available"]
            self.assertEqual(len(options),3)
            for row in options:
                self.assertTrue(row["pdf_ready"])
                self.assertTrue(row["docx_ready"])
                self.assertTrue(row["download_enabled"])
                self.assertFalse(row["docx_download_enabled"])
                self.assertTrue(row["word_paid_only"])
            for code in SUBJECTS:
                with self.subTest(subject=code):
                    word=self.client.get(PREFIX+code+".docx")
                    self.assertEqual(word.status_code,403)
                    self.assertIn("berbayar",word.get_json()["error"])
                    self.assertEqual(word.headers["Cache-Control"],"no-store, private")
                    pdf=self.client.get(PREFIX+code+".pdf")
                    expected,name,digest=document(code,"pdf")
                    self.assertEqual(pdf.status_code,200)
                    self.assertEqual(pdf.data,expected)
                    self.assertEqual(pdf.headers["X-RPT-Source-SHA256"],digest)
                    self.assertIn("attachment",pdf.headers["Content-Disposition"])

    def test_founder_and_active_vip_get_original_word_and_pdf(self):
        accounts=(
            {"telegram_user_id":41,"rakan_pembangun":True},
            {"telegram_user_id":42,
             "vip_expires_at":(datetime.now(timezone.utc)+timedelta(days=5)).isoformat()},
            {"telegram_user_id":43,
             "vip_until":(date.today()+timedelta(days=5)).isoformat()},
        )
        # No personal profile in the synthetic test: the verified Word source
        # remains unchanged, while actual accounts may receive cover branding.
        with patch("web.kp2027_year1_rpt_personalize.for_download",
                   side_effect=lambda account,subject,fmt,content:(content,False)):
            for account in accounts:
                with self.subTest(account=account["telegram_user_id"]):
                    with patch("web.rpt_2027_all_http._account",
                               return_value=(account,None)):
                        catalogue=self.client.get("/api/rpt/2027/catalog").get_json()
                        self.assertTrue(catalogue["personalization_allowed"])
                        self.assertTrue(all(row["docx_download_enabled"]
                                            for row in catalogue["kp2027_rpt_available"]))
                        for code in SUBJECTS:
                            response=self.client.get(PREFIX+code+".docx")
                            expected,name,digest=document(code,"docx")
                            self.assertEqual(response.status_code,200)
                            self.assertEqual(response.data,expected)
                            self.assertEqual(response.mimetype,
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                            self.assertEqual(response.headers["X-RPT-Source-SHA256"],digest)
                            self.assertEqual(response.headers["X-RPT-Output-SHA256"],sha256(expected).hexdigest())
                            self.assertEqual(response.headers["X-RPT-Personalization-Allowed"],"1")
                            self.assertIn(name,response.headers["Content-Disposition"])
                            self.assertIn("attachment",response.headers["Content-Disposition"])
                            self.assertEqual(response.headers["Cache-Control"],"no-store, private")

    def test_word_inventory_has_only_verified_source_documents(self):
        import json
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        data=json.loads((root/"audits/rpt_2027_word_premium_inventory_20261123.json").read_text("utf-8"))
        self.assertEqual(data["ready_source_word_count"],26)
        self.assertEqual(data["kssr_bm_word"]["count"],5)
        self.assertEqual(data["kssr_bm_word"]["total_pdp"],825)
        self.assertEqual(data["kp2027_year1"]["count"],3)
        self.assertEqual(data["existing_sjk_word"]["count"],18)
        self.assertEqual(sum(item["count"] for item in data["existing_sjk_word"]["categories"]),18)
        self.assertEqual(data["pending_native_word_sources"][0]["scope_count"],51)
        self.assertEqual(data["status"],"SOURCE_INVENTORY_NOT_ACADEMIC_APPROVAL")
        self.assertTrue(data["entitlement"]["no_generation_credit_charge"])

    def test_anonymous_is_401_invalid_format_is_404_and_kssr_pdf_unchanged(self):
        with patch("web.rpt_2027_all_http._account",
                   side_effect=lambda:(None,({"error":"Authentication required"},401))):
            self.assertEqual(self.client.get(PREFIX+"matematik.docx").status_code,401)
        with patch("web.rpt_2027_all_http._account",
                   return_value=({"telegram_user_id":99},None)):
            self.assertEqual(self.client.get(PREFIX+"matematik.zip").status_code,404)
            self.assertEqual(self.client.get(PREFIX+"unknown.docx").status_code,404)
            # PDF-only KSSR subjects do not get a fake Word file.
            self.assertEqual(self.client.get("/api/rpt/2027/all/bahasa_arab/2.docx").status_code,404)


if __name__=="__main__":
    unittest.main()
