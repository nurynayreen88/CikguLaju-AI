"""Unit tests for isolated RPT PDF Telegram callback integration."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from rpt_2027.english import telegram_downloads


class TelegramRPTTests(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.documents = []
        self.active = False
        self.admin = False

        class Response:
            ok = True
            def json(self):
                return {"ok": True}

        def send(cid, message, kb=None):
            self.messages.append((cid, message, kb))
            return message

        def send_document(cid, path, caption=""):
            self.documents.append((cid, path, caption))
            return Response()

        self.namespace = {
            "callback": lambda cid, data: ("previous", cid, data),
            "send": send, "send_document": send_document,
            "_is_admin": lambda cid: self.admin,
            "_access_info": lambda cid: {"active": self.active},
        }
        self.assertTrue(telegram_downloads.install(self.namespace))

    def test_dlp_menu_and_pdf_word_delivery_for_published_years(self):
        callback = self.namespace["callback"]
        callback(123, "rpt2027_dlp:science_dlp:3:pdf")
        self.assertIn("Akses Terhad", self.messages[-1][1])
        self.active = True
        for year in (2, 3, 4, 5, 6):
            callback(123, f"rpt2027_year_{year}")
            buttons = [button["callback_data"] for row in self.messages[-1][2] for button in row]
            for code in ("science_dlp", "mathematics_dlp"):
                for fmt in ("pdf", "docx"):
                    key = f"rpt2027_dlp:{code}:{year}:{fmt}"
                    self.assertIn(key, buttons)
                    callback(123, key)
                    self.assertTrue(self.documents[-1][1].endswith(f"_Year_{year}.{fmt}"))
                    self.assertIn(f"Year {year}", self.documents[-1][2])
        callback(123, "rpt2027_dlp:science_dlp:pdf")
        self.assertTrue(self.documents[-1][1].endswith("_Year_2.pdf"))
        callback(123, "rpt2027_dlp:science_dlp:3:../pdf")
        callback(123, "rpt2027_dlp:science_dlp:1:pdf")
        self.assertEqual(len(self.documents), 21)

    def test_sjkc_paid_users_receive_pdf_and_word_for_each_year(self):
        from rpt_2027.sjkc.bahasa_cina.documents import document_path

        callback = self.namespace["callback"]
        callback(123, "rpt2027_sjkc:2:docx")
        self.assertIn("Akses Terhad", self.messages[-1][1])
        self.assertEqual(self.documents, [])
        self.active = True
        for year in range(2, 7):
            callback(123, f"rpt2027_year_{year}")
            buttons = {button["callback_data"]: button["text"]
                       for row in self.messages[-1][2] for button in row}
            self.assertIn(f"rpt2027_language:bahasa_cina_sk:{year}", buttons)
            for fmt in ("pdf", "docx"):
                key = f"rpt2027_sjkc:{year}:{fmt}"
                self.assertIn("Bahasa Cina (SJKC)", buttons[key])
                callback(123, key)
                self.assertEqual(Path(self.documents[-1][1]), document_path(year, fmt))
        for key in ("rpt2027_sjkc:1:pdf", "rpt2027_sjkc:6:../pdf", "rpt2027_sjkc:6:zip"):
            callback(123, key)
            self.assertIn("tidak sah", self.messages[-1][1])
        self.assertEqual(len(self.documents), 10)

    def test_bm_sjk_years_two_through_six_paid_only_and_distinct_from_sk_and_cina(self):
        from rpt_2027.sjkc.bahasa_melayu.documents import document_path

        callback = self.namespace["callback"]
        for year in range(2, 7):
            callback(123, f"rpt2027_bm_sjk:{year}:pdf")
            self.assertIn("Akses Terhad", self.messages[-1][1])
        self.assertEqual(self.documents, [])
        self.active = True
        for year in range(2, 7):
            callback(123, f"rpt2027_year_{year}")
            buttons = {b["callback_data"]: b["text"] for row in self.messages[-1][2] for b in row}
            for fmt in ("pdf", "docx"):
                key = f"rpt2027_bm_sjk:{year}:{fmt}"
                self.assertIn("Bahasa Melayu (SJK)", buttons[key])
                self.assertIn(f"rpt2027_sjkc:{year}:{fmt}", buttons)
                callback(123, key)
                self.assertEqual(Path(self.documents[-1][1]), document_path(year, fmt))
                self.assertIn(f"Tahun {year}", self.documents[-1][2])
        for key in ("rpt2027_bm_sjk:1:pdf", "rpt2027_bm_sjk:7:pdf", "rpt2027_bm_sjk:3:zip"):
            callback(123, key)
            self.assertIn("tidak sah", self.messages[-1][1])
        self.assertEqual(len(self.documents), 10)

    def test_bm_sjk_year_six_references_follow_printed_activity_pages(self):
        import json

        from rpt_2027.sjkc.bahasa_melayu.documents import document_path

        source = document_path(6, "docx").with_name("year_6_kuala_lumpur.json")
        lessons = json.loads(source.read_text(encoding="utf-8"))["lessons"]
        topics = {lesson["topic"]: lesson["textbook_page"] for lesson in lessons}
        self.assertEqual(topics["Jagalah Kesihatan Mental"], "33")
        self.assertEqual(topics["Promosi Minda Sihat"], "34–35")
        activities = {lesson["pkjr"]["activity"]: lesson["pkjr"]["pages"]
                      for lesson in lessons if "pkjr" in lesson}
        self.assertEqual(activities[8], "10–11")
        self.assertEqual(activities[9], "12")

    def test_sains_sjkc_years_two_through_six_pdf_and_word_are_paid_only(self):
        from rpt_2027.sjkc.sains.documents import document_path

        callback = self.namespace["callback"]
        for year in (2, 3, 4, 5, 6):
            callback(123, f"rpt2027_sains_sjkc:{year}:docx")
            self.assertIn("Akses Terhad", self.messages[-1][1])
        self.assertEqual(self.documents, [])

        self.active = True
        for year in (2, 3, 4, 5, 6):
            callback(123, f"rpt2027_year_{year}")
            buttons = {b["callback_data"]: b["text"] for row in self.messages[-1][2] for b in row}
            for fmt in ("pdf", "docx"):
                key = f"rpt2027_sains_sjkc:{year}:{fmt}"
                self.assertIn("Sains (SJKC)", buttons[key])
                callback(123, key)
                self.assertEqual(Path(self.documents[-1][1]), document_path(year, fmt))
        callback(123, "rpt2027_sains_sjkc:1:pdf")
        self.assertIn("tidak sah", self.messages[-1][1])
        self.assertEqual(len(self.documents), 10)

    def test_sjkc_delivery_requires_telegram_confirmation(self):
        self.active = True
        self.namespace["_telegram_delivery_ok_v25279"] = lambda result: False
        self.namespace["callback"](123, "rpt2027_sjkc:3:pdf")
        self.assertEqual(len(self.documents), 1)
        self.assertIn("belum mengesahkan", self.messages[-1][1])

    def test_other_callbacks_are_unchanged(self):
        self.assertEqual(self.namespace["callback"](123, "quick"), ("previous", 123, "quick"))

    def test_unpaid_cannot_open_or_download(self):
        self.namespace["callback"](123, "rpt2027_year_2")
        self.namespace["callback"](123, "rpt2027_en_pdf_6")
        self.assertFalse(self.documents)
        self.assertTrue(all("Akses Terhad" in msg[1] for msg in self.messages))

    def test_paid_download_exact_file_without_using_trials(self):
        self.active = True
        with TemporaryDirectory() as folder:
            pdf = Path(folder) / "RPT_ENGLISH_TAHUN_6_2027_UNTUK_GURU.pdf"
            pdf.write_bytes(b"%PDF-1.7\\ntest")
            with patch.object(telegram_downloads, "PDF_ROOT", Path(folder)):
                self.namespace["callback"](123, "rpt2027_year_6")
                self.namespace["callback"](123, "rpt2027_en_pdf_6")
        self.assertEqual(len(self.documents), 1)
        self.assertEqual(self.documents[0][1], str(pdf))
        self.assertNotIn("RPH", self.documents[0][2])
        self.assertIn("English", self.messages[0][1])

    def test_missing_file_does_not_return_other_year(self):
        self.admin = True
        with TemporaryDirectory() as folder, patch.object(telegram_downloads, "PDF_ROOT", Path(folder)):
            self.namespace["callback"](123, "rpt2027_en_pdf_2")
        self.assertEqual(self.documents, [])
        self.assertIn("belum tersedia", self.messages[-1][1])

    def test_invalid_year_rejected(self):
        self.active = True
        self.namespace["callback"](123, "rpt2027_en_pdf_7")
        self.assertEqual(self.documents, [])
        self.assertIn("tidak sah", self.messages[-1][1])

    def test_legacy_year_one_falls_back(self):
        self.admin = True
        self.assertEqual(self.namespace["callback"](123, "rpt2027_year_1"), ("previous", 123, "rpt2027_year_1"))

    def test_additional_languages_show_preparation_status_without_document(self):
        callback = self.namespace["callback"]
        callback(123, "rpt2027_language:bahasa_iban:2")
        self.assertIn("Akses Terhad", self.messages[-1][1])
        self.active = True
        callback(123, "rpt2027_year_2")
        buttons = {button["callback_data"]: button["text"]
                   for row in self.messages[-1][2] for button in row}
        for code in ("bahasa_iban", "bahasa_kadazandusun", "bahasa_semai",
                     "bahasa_cina_sk", "bahasa_tamil_sk"):
            selection = f"rpt2027_language:{code}:2"
            self.assertIn("Dalam Penyediaan", buttons[selection])
            callback(123, selection)
            self.assertIn("dalam penyediaan", self.messages[-1][1])
        callback(123, "rpt2027_language:bahasa_iban:1")
        self.assertIn("tidak sah", self.messages[-1][1])
        self.assertEqual(self.documents, [])

    def test_failure_not_reported_as_success(self):
        self.active = True
        class FailedResponse:
            ok = False
            def json(self):
                return {"ok": False}
        self.namespace["send_document"] = lambda *a, **kw: FailedResponse()
        # Installer captured the original transport; use a new namespace.
        self.namespace.pop("CIKGULAJU_RPT_ENGLISH_2027_INSTALLED")
        self.namespace["callback"] = lambda cid, data: None
        telegram_downloads.install(self.namespace)
        with TemporaryDirectory() as folder:
            (Path(folder) / "RPT_ENGLISH_TAHUN_2_2027_UNTUK_GURU.pdf").write_bytes(b"%PDF-1.7")
            with patch.object(telegram_downloads, "PDF_ROOT", Path(folder)):
                self.namespace["callback"](123, "rpt2027_en_pdf_2")
        self.assertIn("belum mengesahkan", self.messages[-1][1])


if __name__ == "__main__":
    unittest.main()
