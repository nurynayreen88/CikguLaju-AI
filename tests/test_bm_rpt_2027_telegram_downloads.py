"""Focused safeguards for BM RPT 2027 PDFs and Telegram callback."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from rpt_2027.bahasa_melayu import telegram_downloads as bm


class BM2027TelegramTests(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.documents = []
        self.active = False
        self.admin = False

        class Response:
            ok = True
            def json(self):
                return {"ok": True}

        self.ns = {
            "callback": lambda cid, data: ("previous", cid, data),
            "send": lambda cid, body, keyboard=None: self.messages.append((cid, body, keyboard)),
            "send_document": lambda cid, path, caption="": self.documents.append((cid, path, caption)) or Response(),
            "_access_info": lambda cid: {"active": self.active},
            "_is_admin": lambda cid: self.admin,
        }
        self.assertTrue(bm.install(self.ns))

    def _sample(self, directory, year=3, valid=True):
        p = Path(directory) / (bm.FILE_TEMPLATE % year)
        p.write_bytes((b"%PDF-1.7\n" if valid else b"HELLO\n") + b"X" * 52000)
        return p

    def test_unrelated_callback_unchanged(self):
        self.assertEqual(self.ns["callback"](33, "quick"), ("previous", 33, "quick"))

    def test_unpaid_cannot_download_existing_pdf(self):
        with TemporaryDirectory() as d:
            self._sample(d)
            with patch.object(bm, "PDF_ROOT", Path(d)):
                self.ns["callback"](33, "rpt2027_bm_pdf_3")
        self.assertFalse(self.documents)
        self.assertIn("Akses Terhad", self.messages[-1][1])

    def test_paid_receives_only_exact_year_and_draft_caption(self):
        self.active = True
        with TemporaryDirectory() as d:
            pdf = self._sample(d, 4)
            with patch.object(bm, "PDF_ROOT", Path(d)):
                self.ns["callback"](33, "rpt2027_bm_pdf_4")
        self.assertEqual(len(self.documents), 1)
        self.assertEqual(self.documents[0][1], str(pdf))
        self.assertIn("DRAF", self.documents[0][2])
        self.assertNotIn("RPH", self.documents[0][2])

    def test_missing_bad_or_invalid_year_fail_closed(self):
        self.admin = True
        with TemporaryDirectory() as d, patch.object(bm, "PDF_ROOT", Path(d)):
            self.ns["callback"](33, "rpt2027_bm_pdf_6")
            self.assertFalse(self.documents)
            self._sample(d, 6, valid=False)
            self.assertFalse(bm.pdf_ready(6))
            self.ns["callback"](33, "rpt2027_bm_pdf_6")
            self.ns["callback"](33, "rpt2027_bm_pdf_7")
        self.assertFalse(self.documents)
        self.assertIn("tidak sah", self.messages[-1][1])

    def test_empty_pdf_filename_rejected(self):
        for bad in (None, 1, 7, "2"):
            with self.assertRaises(ValueError):
                bm.pdf_path(bad)

    def test_idempotent_install(self):
        f = self.ns["callback"]
        self.assertTrue(bm.install(self.ns))
        self.assertIs(self.ns["callback"], f)

    def test_year_menu_only_shows_bm_when_pdf_present(self):
        from rpt_2027.english import telegram_downloads as english
        self.active = True
        with patch.object(english, "bm_pdf_ready", lambda year, ns=None: year == 3), \
             patch.object(english, "math_pdf_ready", lambda year, ns=None: False), \
             patch.object(english, "pi_pdf_ready", lambda year: False):
            english.install(self.ns)
            self.ns["callback"](33, "rpt2027_year_3")
            kb = self.messages[-1][2]
            vals = [b["callback_data"] for row in kb for b in row]
            self.assertIn("rpt2027_bm_pdf_3", vals)
            self.assertNotIn("rpt2027_math_pdf_3", vals)
            self.assertNotIn("rpt2027_pi_pdf_3", vals)


if __name__ == "__main__":
    unittest.main()
