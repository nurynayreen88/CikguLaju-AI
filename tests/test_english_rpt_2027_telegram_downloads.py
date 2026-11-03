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
