"""No live Telegram requests; verify the real menu hooks are patched safely."""
import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pypdf import PdfReader

from web.english_y2_verified_workbook_runtime import install


class WorkbookRuntimeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        path = Path(self.tmp.name) / "books/english/y12_workbook_041_080.pdf"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"%PDF-1.4\n")
        self.runtime = SimpleNamespace(
            _available_materials_v2528=lambda ss: ["rph", "textbook"],
            _en_book_pages_v25232=lambda ss, key: [9],
            _local_book_chunk_v25234=lambda ss, key, page: None,
            _english_primary_year_number_v2517=lambda y: int(str(y).replace("Tahun ", "")),
        )

    def test_year2_lesson4_exposes_download_and_page(self):
        ss = {"year": "Tahun 2", "subject": "English", "lesson_no": 4}
        with patch("web.english_y2_verified_workbook_runtime.resolve_lesson",
                   side_effect=lambda lesson: {"source_page_start": 60, "source_page_end": 60} if lesson == 4 else None):
            self.assertTrue(install(self.runtime))
            self.assertIn("activity", self.runtime._available_materials_v2528(ss))
            self.assertEqual(self.runtime._en_book_pages_v25232(ss, "activity"), [60])

    def test_missing_year4_pdf_part_is_not_offered(self):
        ss = {"year": "Tahun 4", "subject": "English", "lesson_no": 2}
        with patch("web.english_y2_verified_workbook_runtime._REPO_ROOT", Path(self.tmp.name)):
            install(self.runtime)
            self.assertNotIn("activity", self.runtime._available_materials_v2528(ss))

    def test_year3_missing_pdf_is_not_offered(self):
        ss = {"year": "Tahun 3", "subject": "English", "lesson_no": 1}
        with patch("web.english_y2_verified_workbook_runtime._REPO_ROOT", Path(self.tmp.name)):
            install(self.runtime)
            self.assertNotIn("activity", self.runtime._available_materials_v2528(ss))

    def test_year3_welcome_sends_verified_page_through_both_handlers(self):
        def capture(cid, path, label):
            self.assertEqual(cid, 12)
            self.assertTrue(label.endswith("m/s 3"))
            self.assertEqual(len(PdfReader(BytesIO(Path(path).read_bytes())).pages), 1)
            return {"ok": True}

        legacy = Mock(return_value=False)
        self.runtime._send_reference_material_v2528 = legacy
        self.runtime._send_reference_material = legacy
        self.runtime._send_document_before_v25277 = Mock(side_effect=capture)
        self.runtime._telegram_delivery_ok_v25279 = lambda result: result["ok"]
        install(self.runtime)
        ss = {"year": "Tahun 3", "subject": "English", "lesson_no": 7}
        self.assertIn("activity", self.runtime._available_materials_v2528(ss))
        self.assertTrue(self.runtime._send_reference_material_v2528(12, ss, "activity"))
        self.assertTrue(self.runtime._send_reference_material(12, ss, "activity"))
        self.assertFalse(self.runtime._send_reference_material(12, ss, "textbook"))
        legacy.assert_called_once_with(12, ss, "textbook")
        self.assertEqual(self.runtime._send_document_before_v25277.call_count, 2)

    def test_year4_verified_pdf_page_is_used(self):
        install(self.runtime)
        ss = {"year": "Tahun 4", "subject": "English", "lesson_no": 2}
        self.assertIn("activity", self.runtime._available_materials_v2528(ss))
        self.assertEqual(self.runtime._en_book_pages_v25232(ss, "activity"), [2])

    def test_unverified_and_other_years_unchanged(self):
        with patch("web.english_y2_verified_workbook_runtime.resolve_lesson", return_value=None):
            install(self.runtime)
            self.assertNotIn("activity", self.runtime._available_materials_v2528(
                {"year": "Tahun 2", "subject": "English", "lesson_no": 5}))
            self.assertNotIn("activity", self.runtime._available_materials_v2528(
                {"year": "Tahun 3", "subject": "English", "lesson_no": 4}))
            self.assertEqual(self.runtime._en_book_pages_v25232(
                {"year": "Tahun 3", "subject": "English", "lesson_no": 4}, "activity"), [9])


if __name__ == "__main__":
    unittest.main()
