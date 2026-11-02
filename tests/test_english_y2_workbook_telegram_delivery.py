"""Isolated tests; no live Telegram calls or database writes."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from resources.english.y2.workbook_telegram_delivery import send_verified_workbook


class WorkbookTelegramDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        part = Path(self.temp.name) / "books/english/y12_workbook_041_080.pdf"
        part.parent.mkdir(parents=True)
        part.write_bytes(b"%PDF-1.4\n")

    def test_verified_lesson_four_sends_existing_pdf(self):
        sent = []
        def sender(chat_id, file, caption):
            sent.append((chat_id, file.read(), caption))
            return SimpleNamespace(ok=True, json=lambda: {"ok": True})
        self.assertTrue(send_verified_workbook(42, 4, sender, root=self.temp.name))
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][0], 42)
        self.assertTrue(sent[0][1].startswith(b"%PDF"))
        self.assertIn("Lesson 4", sent[0][2])

    def test_unverified_lesson_never_sends(self):
        sent = []
        self.assertFalse(send_verified_workbook(42, 5, lambda *args: sent.append(args), root=self.temp.name))
        self.assertEqual(sent, [])

    def test_failed_telegram_ack_is_not_success(self):
        def sender(*args):
            return SimpleNamespace(ok=False, json=lambda: {"ok": False})
        self.assertFalse(send_verified_workbook(42, 4, sender, root=self.temp.name))

    def test_opaque_response_is_not_assumed_success(self):
        self.assertFalse(send_verified_workbook(42, 4, lambda *args: object(), root=self.temp.name))


if __name__ == "__main__":
    unittest.main()
