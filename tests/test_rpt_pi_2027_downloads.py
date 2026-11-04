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


    def test_committed_pdf_assets(self):
        import hashlib
        expected = {
            2: ("3482cfa8cedb117dd97a933a76bca8653c458deb3bceabe43e4cfa1d5ab40c1c", 779461),
            3: ("6f147535617bca5aeec4e6e1836fa9a604247607af088665ffa1e0ecb3162619", 1003642),
            4: ("624bb845ed947aa2b62b8d2151a64fda6a12232146ce5fb6ece8212b00d91e3e", 1093409),
            5: ("0da43a8582ea9533ee2a3487223489ecc2772333a46b5efcf6573a1cce11f4cc", 1038690),
            6: ("641da5417d7d010a979920ab6f0cbec601026588fecd3aa77906d8d0844a8025", 1064164),
        }
        for year, (digest, size) in expected.items():
            with self.subTest(year=year):
                data = pi.pdf_path(year).read_bytes()
                self.assertTrue(data.startswith(b"%PDF-"))
                self.assertEqual(len(data), size)
                self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
                self.assertTrue(pi.pdf_ready(year))

    def test_english_rpt_menu_shows_pi_option_for_paid_only(self):
        from rpt_2027.english import telegram_downloads as english
        self.assertTrue(english.install(self.ns))
        self.ns["callback"](22, "rpt2027_year_2")
        keyboard = self.sent[-1][2]
        data = [button["callback_data"] for row in keyboard for button in row]
        self.assertIn("rpt2027_pi_pdf_2", data)
        self.sent.clear()
        self.ns["callback"](99, "rpt2027_year_2")
        self.assertIn("Akses Terhad", self.sent[-1][1])


if __name__ == "__main__":
    unittest.main()
