"""Read-only safety and format checks for PSV staged RPH A4 preview.

This does not enable Telegram or approve any draft.
Run: python -m unittest tests.test_psv_preview_a4
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

from docx import Document
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "rph_standalone" / "psv" / "preview_a4.py"
spec = importlib.util.spec_from_file_location("psv_preview_a4", SCRIPT)
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class PSVPreviewQA(unittest.TestCase):
    def test_all_210_source_files_parse_to_five_teaching_stages(self):
        files = []
        for year in range(2, 7):
            for pdp in range(1, 43):
                item = preview.load(year, pdp, preview=True)
                with self.subTest(year=year, pdp=pdp):
                    self.assertEqual(item["year"], year)
                    self.assertEqual(item["pdp"], pdp)
                    self.assertIn("DRAF", item["metadata"]["Status"])
                    self.assertTrue(item["metadata"]["SK"])
                    self.assertTrue(item["metadata"]["SP"])
                    self.assertTrue(item["objective"])
                    self.assertEqual(len(item["stages"]), 7)
                    stages = [label for label, _ in item["stages"][:5]]
                    self.assertTrue(stages[0].startswith("Set induksi"))
                    self.assertTrue(stages[1].startswith("Aktiviti 1"))
                    self.assertTrue(stages[2].startswith("Aktiviti 2"))
                    self.assertTrue(stages[3].startswith("Pengukuhan/Pentaksiran"))
                    self.assertTrue(stages[4].startswith("Penutup"))
                files.append(item["source"])
        self.assertEqual(len(set(files)), 210)

    def test_user_facing_export_refuses_draft_and_invalid_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            for year in range(2, 7):
                with self.subTest(year=year):
                    with self.assertRaisesRegex(ValueError, "DRAF"):
                        preview.render(year, 1, dest)
            self.assertFalse(list(dest.iterdir()))
        for year, pdp in ((1, 1), (7, 1), (5, 0), (5, 43)):
            with self.subTest(year=year, pdp=pdp):
                with self.assertRaises(ValueError):
                    preview.load(year, pdp, preview=True)

    def test_five_representative_word_pdf_previews_are_a4(self):
        cases = ((2, 1), (3, 30), (4, 39), (5, 39), (6, 39))
        with tempfile.TemporaryDirectory() as tmp:
            for year, pdp in cases:
                with self.subTest(year=year, pdp=pdp):
                    docx_path, pdf_path = preview.render(year, pdp, Path(tmp), preview=True)
                    self.assertTrue(docx_path.is_file())
                    self.assertTrue(pdf_path.is_file())
                    d = Document(docx_path)
                    self.assertAlmostEqual(d.sections[0].page_width.cm, 21, delta=0.1)
                    self.assertAlmostEqual(d.sections[0].page_height.cm, 29.7, delta=0.1)
                    pages = PdfReader(str(pdf_path)).pages
                    self.assertEqual(len(pages), 1)
                    text = pages[0].extract_text()
                    self.assertIn(f"TAHUN {year}", text)
                    self.assertIn(f"PdP {pdp:03d}", text)
                    self.assertNotIn("DRAF SEMAK", text)


if __name__ == "__main__":
    unittest.main()
