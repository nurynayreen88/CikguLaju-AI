"""No live Telegram requests; verify the real menu hooks are patched safely."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

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
            _english_primary_year_number_v2517=lambda y: int(str(y).replace("Tahun ", "")),
        )

    def test_year2_lesson4_exposes_download_and_page(self):
        ss = {"year": "Tahun 2", "subject": "English", "lesson_no": 4}
        with patch("web.english_y2_verified_workbook_runtime.resolve_lesson",
                   side_effect=lambda lesson: {"source_page_start": 60, "source_page_end": 60} if lesson == 4 else None):
            self.assertTrue(install(self.runtime))
            self.assertIn("activity", self.runtime._available_materials_v2528(ss))
            self.assertEqual(self.runtime._en_book_pages_v25232(ss, "activity"), [60])

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
