"""Regression tests: English-style local Matematik RPT 2027 PDF delivery."""
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from rpt_2027.english import telegram_downloads as english
from rpt_2027.matematik import telegram_downloads as math


# Exact Drive originals; these assets are intentionally shipped in GitHub.
ASSETS = {
    2: (423969, "f619dd8d92fd994aa3349fd7e72c98b1e0b28faa29752ea977fbad4916fdb60d"),
    3: (462291, "11788fdb5b0646688f178287b3672ac8bc4264c9b3fbce7fbee62ab08bfa3091"),
    4: (560146, "1eaba7a6b3eca4b1b74e25966fefddd2d787eeef6897b1fa95a506b01de7efad"),
    5: (465086, "be1618dd3fa4c5675510d39cadf763c3d7e4e887bf0ff845dc8c92d72774fd95"),
    6: (462072, "78289b9c4dd1cbce6b669ecc8030512432f3bbc915ca874f0c88aec3b86752d2"),
}


class Response:
    ok = True

    def json(self):
        return {"ok": True}


class MatematikRPTTests(unittest.TestCase):
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

    def test_all_five_committed_pdfs_match_drive_originals(self):
        for year, (expected_size, expected_sha256) in ASSETS.items():
            with self.subTest(year=year):
                path = math.pdf_path(year)
                self.assertEqual(path.parent, math.PDF_ROOT)
                self.assertTrue(math.pdf_ready(year))
                self.assertEqual(path.stat().st_size, expected_size)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected_sha256)
                self.assertIn("v28_SEMENTARA.pdf", path.name)

    def test_legacy_callback_untouched(self):
        self.assertEqual(self.ns["callback"](9, "home"), ("legacy", 9, "home"))

    def test_unpaid_cannot_download_committed_pdf(self):
        self.ns["callback"](9, "rpt2027_math_pdf_2")
        self.assertEqual(self.documents, [])
        self.assertIn("Akses Terhad", self.messages[-1][1])

    def test_paid_year_menu_and_exact_committed_pdf(self):
        self.paid = True
        self.ns["callback"](9, "rpt2027_year_5")
        kb = self.messages[-1][2]
        callbacks = [button["callback_data"] for row in kb for button in row]
        self.assertIn("rpt2027_math_pdf_5", callbacks)
        result = self.ns["callback"](9, "rpt2027_math_pdf_5")
        self.assertTrue(result.ok)
        self.assertEqual(self.documents, [
            (9, str(math.pdf_path(5)),
             "RPT Matematik Tahun 5 — 2027 v28 (DRAF/SEMENTARA)")
        ])

    def test_admin_can_download(self):
        self.admin = True
        self.ns["callback"](9, "rpt2027_math_pdf_3")
        self.assertEqual(self.documents[0][1], str(math.pdf_path(3)))

    def test_missing_pdf_hidden_and_old_button_fails_closed(self):
        self.paid = True
        with TemporaryDirectory() as temp, patch.object(math, "PDF_ROOT", Path(temp)):
            self.ns["callback"](9, "rpt2027_year_3")
            kb = self.messages[-1][2]
            self.assertFalse(any(
                button["callback_data"].startswith("rpt2027_math_pdf_")
                for row in kb for button in row
            ))
            self.ns["callback"](9, "rpt2027_math_pdf_3")
        self.assertFalse(self.documents)
        self.assertIn("belum tersedia", self.messages[-1][1])

    def test_invalid_year_and_pdf_header_rejected(self):
        self.admin = True
        self.ns["callback"](9, "rpt2027_math_pdf_7")
        self.assertIn("tidak sah", self.messages[-1][1])
        with TemporaryDirectory() as temp, patch.object(math, "PDF_ROOT", Path(temp)):
            path = self.make_pdf(Path(temp), 4)
            path.write_bytes(b"NOTPDF" + b"x" * 120000)
            self.assertFalse(math.pdf_ready(4))
            self.ns["callback"](9, "rpt2027_math_pdf_4")
        self.assertFalse(self.documents)

    def test_telegram_delivery_failure_not_reported_as_success(self):
        self.paid = True

        class Failed:
            ok = False

            def json(self):
                return {"ok": False}

        # Install anew because the wrapper captures send_document.
        self.ns = dict(self.ns)
        self.ns["callback"] = lambda cid, data: ("legacy", cid, data)
        self.ns["send_document"] = lambda *args, **kwargs: Failed()
        self.ns.pop("CIKGULAJU_RPT_MATEMATIK_2027_INSTALLED")
        self.assertTrue(math.install(self.ns))
        self.ns["callback"](9, "rpt2027_math_pdf_6")
        self.assertIn("belum mengesahkan", self.messages[-1][1])

    def test_no_supabase_access_or_environment_variable_needed(self):
        self.paid = True

        def fail_db(*args, **kwargs):
            self.fail("RPT PDF should not query Supabase")

        self.ns["_sb_request"] = fail_db
        path = math.pdf_path(2)
        with patch.dict(os.environ, {"CIKGULAJU_RPT_MATH_PDF_DIR": "/nonexistent"}):
            self.assertEqual(math.pdf_path(2), path)
            self.ns["callback"](9, "rpt2027_math_pdf_2")
        self.assertEqual(self.documents[0][1], str(path))


if __name__ == "__main__":
    unittest.main()
