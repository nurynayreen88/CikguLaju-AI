"""Regression cases for malformed Word archives and PDF outputs."""
from io import BytesIO
from zipfile import ZipFile
import unittest

from web.rph_download_pipeline import prepare_approved_download

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def fake_zip(names):
    buf = BytesIO()
    with ZipFile(buf, "w") as z:
        for name in names:
            z.writestr(name, "<xml/>")
    return buf.getvalue()


class InvalidDocumentsDoNotDebit(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.account = {"authenticated": True, "telegram_user_id": 72,
                        "free_remaining": 5}

    def debit(self, *args):
        self.calls.append(args)
        return {"ok": True, "remaining": 4}

    def assert_rejected(self, fmt, payload, mime):
        with self.assertRaises(ValueError):
            prepare_approved_download(
                object(), fmt, self.account, 72,
                "https://example.supabase.co", "secret",
                debit=self.debit, renderer=lambda r, f: (payload, mime))
        self.assertEqual(self.calls, [])

    def test_word_archive_missing_document(self):
        self.assert_rejected("docx", fake_zip(["[Content_Types].xml"]), DOCX)

    def test_word_archive_missing_content_types(self):
        self.assert_rejected("docx", fake_zip(["word/document.xml"]), DOCX)

    def test_word_truncated_zip(self):
        self.assert_rejected("docx", b"PK\\x03\\x04garbage", DOCX)

    def test_pdf_without_header(self):
        self.assert_rejected("pdf", b"not-pdf", "application/pdf")


if __name__ == "__main__":
    unittest.main()
