"""Smoke-test school identity cover on actual RPT 2027 PDFs from the repository.

No output files are committed and no source PDF is rewritten.
"""
from io import BytesIO
from hashlib import sha256
from pathlib import Path
import unittest

from pypdf import PdfReader
from web.native_rpt_telegram_api import RPT, ROOT, select_source
from web.rpt_pdf_cover_renderer import personalized_pdf

PUBLISHED = ("english", "bahasa_melayu", "matematik",
             "pendidikan_islam", "pjpk")


class ActualSourceSchoolCoverTests(unittest.TestCase):
    def test_exact_original_rpt_pages_survive_school_cover(self):
        verified = 0
        for code in PUBLISHED:
            for year in range(2, 7):
                with self.subTest(subject=code, year=year):
                    path = select_source(code, year)
                    before = path.read_bytes()
                    self.assertTrue(before.startswith(b"%PDF-"))
                    original = PdfReader(BytesIO(before), strict=False)
                    self.assertGreater(len(original.pages), 0)
                    cover = personalized_pdf(path, RPT[code][0] +
                        " — Tahun " + str(year), 2027,
                        {"school": "SK Taman Sejahtera",
                         "state": "Johor", "teacher": "Cikgu Rozita", "logo": None})
                    self.assertTrue(cover.getvalue().startswith(b"%PDF-"))
                    final = PdfReader(cover, strict=False)
                    self.assertEqual(len(final.pages), len(original.pages) + 1)
                    first = final.pages[0].extract_text()
                    self.assertIn("SK Taman Sejahtera", first)
                    self.assertIn("2027", first)
                    self.assertIn("Tahun " + str(year), first)
                    self.assertEqual(
                        (float(final.pages[1].mediabox.width),
                         float(final.pages[1].mediabox.height)),
                        (float(original.pages[0].mediabox.width),
                         float(original.pages[0].mediabox.height)))
                    self.assertEqual(path.read_bytes(), before)
                    verified += 1
        self.assertEqual(verified, 25)


if __name__ == "__main__":
    unittest.main()
