"""Offline smoke tests using real Word/PDF rendering and the shared quota boundary."""
from io import BytesIO
from zipfile import ZipFile
import unittest

from web.rph_document_renderer import ApprovedRPH
from web.rph_download_pipeline import prepare_approved_download


class RealDocumentPipelineTests(unittest.TestCase):
    def setUp(self):
        self.rph = ApprovedRPH(
            12, "English Year 2 - Lesson 12",
            "Learning objective: Pupils identify animals.\n"
            "Activity 1: Teacher displays animal pictures.\n"
            "Assessment: Pupils name three animals.",
            "approved:test-fixture",
        )
        self.account = {"authenticated": True, "telegram_user_id": 42,
                        "free_remaining": 3}
        self.debits = []

    def debit(self, url, key, uid, reference):
        self.debits.append((uid, reference))
        return {"ok": True, "remaining": 2}

    def test_real_pdf_and_docx(self):
        for fmt in ("pdf", "docx"):
            with self.subTest(fmt=fmt):
                result = prepare_approved_download(
                    self.rph, fmt, self.account, 42,
                    "https://example.supabase.co", "secret", debit=self.debit)
                self.assertTrue(result["allowed"])
                data = result["document"]
                self.assertGreater(len(data), 100)
                if fmt == "pdf":
                    self.assertTrue(data.startswith(b"%PDF-"))
                    self.assertIn(b"%%EOF", data[-128:])
                else:
                    with ZipFile(BytesIO(data)) as archive:
                        self.assertIsNone(archive.testzip())
                        self.assertIn("word/document.xml", archive.namelist())
        self.assertEqual(len(self.debits), 2)
        self.assertNotEqual(self.debits[0][1], self.debits[1][1])

    def test_real_paid_render_does_not_debit(self):
        account = {**self.account, "rakan_pembangun": True}
        result = prepare_approved_download(
            self.rph, "pdf", account, 42,
            "https://example.supabase.co", "secret", debit=self.debit)
        self.assertTrue(result["allowed"])
        self.assertEqual(self.debits, [])

    def test_real_render_with_zero_trial_does_not_return_bytes(self):
        account = {**self.account, "free_remaining": 0}
        result = prepare_approved_download(
            self.rph, "docx", account, 42,
            "https://example.supabase.co", "secret", debit=self.debit)
        self.assertFalse(result["allowed"])
        self.assertIsNone(result["document"])
        self.assertEqual(self.debits, [])


if __name__ == "__main__":
    unittest.main()
