"""Staging-only Matematik RPH callback contract. No Telegram API or database."""
import importlib.util
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "rph_standalone" / "matematik" / "staging_preview.py"
SPEC = importlib.util.spec_from_file_location("math_rph_v35_staging", MODULE)
math = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(math)


class Success:
    ok = True

    def json(self):
        return {"ok": True}


class StagingMathPreviewContract(unittest.TestCase):
    def setUp(self):
        self.paid = False
        self.admin = False
        self.messages = []
        self.documents = []
        self.ns = {
            "callback": lambda cid, data: ("existing", cid, data),
            "send": lambda cid, message: self.messages.append((cid, message)),
            "send_document": lambda cid, path, caption: self.documents.append((cid, path, caption)) or Success(),
            "_access_info": lambda cid: {"active": self.paid},
            "_is_admin": lambda cid: self.admin,
        }

    def test_default_not_installed_without_explicit_staging_flag(self):
        with patch.dict(os.environ, {math.STAGING_FLAG: ""}):
            self.assertFalse(math.install(self.ns, "/missing.zip"))
        self.assertNotIn("CIKGULAJU_MATH_RPH_V35_STAGING_INSTALLED", self.ns)

    def test_staging_nonpreview_callback_is_preserved(self):
        with patch.dict(os.environ, {math.STAGING_FLAG: "1"}):
            self.assertTrue(math.install(self.ns, "/missing.zip"))
        self.assertEqual(self.ns["callback"](42, "home"), ("existing", 42, "home"))

    def test_unpaid_and_forged_buttons_blocked_before_any_file_read(self):
        with patch.dict(os.environ, {math.STAGING_FLAG: "1"}):
            self.assertTrue(math.install(self.ns, "/missing.zip"))
        self.ns["callback"](42, "mathrph_v35_preview_y3_l043_pdf")
        self.assertEqual(self.documents, [])
        self.assertIn("disahkan", self.messages[-1][1])
        self.ns["callback"](42, "mathrph_v35_preview_y3_l999_pdf")
        self.assertEqual(self.documents, [])
        self.assertIn("Lesson", self.messages[-1][1])

    def test_paid_missing_archive_fails_closed_without_old_rph_fallback(self):
        self.paid = True
        with patch.dict(os.environ, {math.STAGING_FLAG: "1"}):
            self.assertTrue(math.install(self.ns, "/missing.zip"))
        self.ns["callback"](42, "mathrph_v35_preview_y5_l001_pdf")
        self.assertEqual(self.documents, [])
        self.assertIn("tidak tersedia", self.messages[-1][1])

    def test_invalid_year_lesson_and_file_format_are_rejected(self):
        invalid = [(1, 1, "pdf"), (7, 1, "pdf"), (2, 0, "pdf"),
                   (6, 118, "pdf"), (5, 1, "exe"), (True, 1, "pdf")]
        for y, n, fmt in invalid:
            with self.subTest(year=y, lesson=n, fmt=fmt):
                with self.assertRaises(ValueError):
                    math.extract_rph_bytes("/does-not-matter.zip", y, n, fmt)

    def test_invalid_zip_path_fails_closed(self):
        with self.assertRaises(math.PreviewUnavailable):
            math.verify_archive(None)
        with TemporaryDirectory() as temp:
            path = Path(temp) / "fake.zip"
            path.write_bytes(b"%PDF-not-a-zip")
            with self.assertRaises(math.PreviewUnavailable):
                math.verify_archive(str(path))

    def test_no_database_subscription_or_quota_mutation(self):
        self.ns["_sb_request"] = lambda *a, **kw: self.fail("DB access forbidden")
        self.ns["deduct_trial"] = lambda *a, **kw: self.fail("Trial mutation forbidden")
        with patch.dict(os.environ, {math.STAGING_FLAG: "1"}):
            self.assertTrue(math.install(self.ns, "/missing.zip"))
        self.paid = True
        self.ns["callback"](42, "mathrph_v35_preview_y6_l117_docx")
        self.assertFalse(self.documents)


if __name__ == "__main__":
    unittest.main()
