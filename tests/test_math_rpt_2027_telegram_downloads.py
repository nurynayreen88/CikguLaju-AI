"""Isolated tests for the paid-only temporary Matematik RPT PDF bridge."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from rpt_2027.english import telegram_downloads as english
from rpt_2027.matematik import telegram_downloads as math


class Response:
    ok = True

    def json(self):
        return {"ok": True}


class MathRPTTelegramTests(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.documents = []
        self.paid = False
        self.admin = False

        def send(cid, text, keyboard=None):
            self.messages.append((cid, text, keyboard))
            return text

        def send_document(cid, path, caption=""):
            self.documents.append((cid, path, caption))
            return Response()

        self.ns = {
            "callback": lambda cid, data: ("legacy", cid, data),
            "send": send,
            "send_document": send_document,
            "_is_admin": lambda cid: self.admin,
            "_access_info": lambda cid: {"active": self.paid},
        }
        self.assertTrue(english.install(self.ns))
        self.assertTrue(math.install(self.ns))

    @staticmethod
    def make_pdf(root, year):
        path = root / ("RPT_Matematik_Tahun_%d_2027_v28_SEMENTARA.pdf" % year)
        path.write_bytes(b"%PDF-1.7\n" + b"x" * 120000)
        return path

    def test_legacy_callbacks_untouched(self):
        self.assertEqual(self.ns["callback"](9, "home"), ("legacy", 9, "home"))

    def test_unpaid_cannot_download_even_when_file_exists(self):
        with TemporaryDirectory() as temp, patch.dict(os.environ, {"CIKGULAJU_RPT_MATH_PDF_DIR": temp}):
            self.make_pdf(Path(temp), 2)
            self.ns["callback"](9, "rpt2027_math_pdf_2")
        self.assertEqual(self.documents, [])
        self.assertIn("Akses Terhad", self.messages[-1][1])

    def test_paid_menu_and_exact_pdf_delivery(self):
        self.paid = True
        with TemporaryDirectory() as temp, patch.dict(os.environ, {"CIKGULAJU_RPT_MATH_PDF_DIR": temp}):
            path = self.make_pdf(Path(temp), 5)
            self.ns["callback"](9, "rpt2027_year_5")
            kb = self.messages[-1][2]
            callbacks = [button["callback_data"] for row in kb for button in row]
            self.assertIn("rpt2027_math_pdf_5", callbacks)
            result = self.ns["callback"](9, "rpt2027_math_pdf_5")
            self.assertTrue(result.ok)
            self.assertEqual(self.documents, [(9, str(path), "RPT Matematik Tahun 5 — 2027 v28 (DRAF/SEMENTARA)")])

    def test_missing_pdf_hidden_and_stale_button_fails_closed(self):
        self.paid = True
        with TemporaryDirectory() as temp, patch.dict(os.environ, {"CIKGULAJU_RPT_MATH_PDF_DIR": temp}):
            self.ns["callback"](9, "rpt2027_year_3")
            kb = self.messages[-1][2]
            self.assertFalse(any(
                button["callback_data"].startswith("rpt2027_math_pdf_")
                for row in kb for button in row
            ))
            self.ns["callback"](9, "rpt2027_math_pdf_3")
        self.assertFalse(self.documents)
        self.assertIn("belum tersedia", self.messages[-1][1])

    def test_invalid_year_and_header_rejected(self):
        self.admin = True
        with TemporaryDirectory() as temp, patch.dict(os.environ, {"CIKGULAJU_RPT_MATH_PDF_DIR": temp}):
            self.ns["callback"](9, "rpt2027_math_pdf_7")
            self.assertIn("tidak sah", self.messages[-1][1])
            path = self.make_pdf(Path(temp), 4)
            path.write_bytes(b"NOTPDF" + b"x" * 120000)
            self.assertFalse(math.pdf_ready(4))
            self.ns["callback"](9, "rpt2027_math_pdf_4")
        self.assertFalse(self.documents)

    def test_delivery_failure_does_not_claim_success(self):
        self.paid = True
        class Failed:
            ok = False

            def json(self):
                return {"ok": False}
        # Set transport before install, as the wrapper captures that function.
        self.ns = dict(self.ns)
        self.ns["callback"] = lambda cid, d: ("legacy", cid, d)
        self.ns["send_document"] = lambda *a, **kw: Failed()
        self.ns.pop("CIKGULAJU_RPT_MATEMATIK_2027_INSTALLED")
        self.assertTrue(math.install(self.ns))
        with TemporaryDirectory() as temp, patch.dict(os.environ, {"CIKGULAJU_RPT_MATH_PDF_DIR": temp}):
            self.make_pdf(Path(temp), 6)
            self.ns["callback"](9, "rpt2027_math_pdf_6")
        self.assertIn("belum mengesahkan", self.messages[-1][1])


if __name__ == "__main__":
    unittest.main()
