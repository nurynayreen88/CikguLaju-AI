"""Tests for paid-gated Pendidikan Islam RPT 2027 Telegram PDF route."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rpt_2027.pendidikan_islam import telegram_downloads as pi


class Response:
    ok = True

    def json(self):
        return {"ok": True}


class TestPIRPT2027(unittest.TestCase):
    def setUp(self):
        self.sent = []
        self.documents = []
        self.other = []
        self.ns = {
            "callback": lambda cid, d: self.other.append((cid, d)) or "previous",
            "send": lambda cid, message, kb=None: self.sent.append((cid, message, kb)) or "sent",
            "send_document": lambda cid, p, caption: self.documents.append((cid, p, caption)) or Response(),
            "_access_info": lambda cid: {"active": cid == 22},
            "_is_admin": lambda cid: cid == 1,
            "_telegram_delivery_ok_v25279": lambda response: response.ok and response.json()["ok"],
        }
        self.assertTrue(pi.install(self.ns))

    def test_other_subject_callback_unchanged(self):
        self.assertEqual(self.ns["callback"](22, "rpt2027_math_pdf_2"), "previous")
        self.assertEqual(self.other, [(22, "rpt2027_math_pdf_2")])

    def test_paid_gate_blocks_saved_callback(self):
        self.ns["callback"](99, "rpt2027_pi_pdf_2")
        self.assertFalse(self.documents)
        self.assertIn("Akses Terhad", self.sent[-1][1])

    def test_invalid_year_does_not_send(self):
        self.ns["callback"](1, "rpt2027_pi_pdf_1")
        self.assertFalse(self.documents)
        self.assertIn("tidak sah", self.sent[-1][1])

    def test_local_valid_pdf_delivered(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / (pi.FILE_TEMPLATE % 2)
            path.write_bytes(b"%PDF-" + b"0" * 100001)
            with patch.object(pi, "PDF_ROOT", Path(tmp)):
                self.assertTrue(pi.pdf_ready(2))
                self.assertFalse(pi.pdf_ready(3))
                result = self.ns["callback"](22, "rpt2027_pi_pdf_2")
                self.assertIsInstance(result, Response)
                self.assertEqual(self.documents[0][1], str(path))

    def test_missing_or_invalid_pdf_not_delivered(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / (pi.FILE_TEMPLATE % 2)
            path.write_bytes(b"NOTPDF" + b"0" * 100001)
            with patch.object(pi, "PDF_ROOT", Path(tmp)):
                self.ns["callback"](1, "rpt2027_pi_pdf_2")
                self.assertFalse(self.documents)
                self.assertIn("belum tersedia", self.sent[-1][1])

    def test_install_idempotent(self):
        original = self.ns["callback"]
        self.assertTrue(pi.install(self.ns))
        self.assertIs(original, self.ns["callback"])


if __name__ == "__main__":
    unittest.main()
