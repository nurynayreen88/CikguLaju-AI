"""Regression tests for verified Year 2 Workbook source PDF selection."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from resources.english.y2.workbook_download_router import resolve_lesson


class WorkbookDownloadRouterTests(unittest.TestCase):
    def test_lesson_four_points_to_verified_workbook_part(self):
        with TemporaryDirectory() as directory:
            part = Path(directory) / "books/english/y12_workbook_041_080.pdf"
            part.parent.mkdir(parents=True)
            part.write_bytes(b"%PDF-1.4\n")
            row = resolve_lesson(4, root=directory)
            self.assertIsNotNone(row)
            self.assertEqual(row["relative_path"], "books/english/y12_workbook_041_080.pdf")
            self.assertEqual(row["part_page_start"], 20)
            self.assertEqual(row["source_page_start"], 60)

    def test_missing_file_does_not_offer_broken_download(self):
        with TemporaryDirectory() as directory:
            self.assertIsNone(resolve_lesson(4, root=directory))

    def test_unverified_lesson_is_not_assigned_workbook(self):
        with TemporaryDirectory() as directory:
            self.assertIsNone(resolve_lesson(5, root=directory))
            self.assertIsNone(resolve_lesson(True, root=directory))


if __name__ == "__main__":
    unittest.main()
