"""Regression guard for user-facing 2027 RPT developer-note removal."""
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import re
import unittest

import fitz

from web.rpt_private_notes import pdf_for_teacher


class PrivateRPTNoteTests(unittest.TestCase):
    def test_synthetic_pdf_cleaned_without_editing_original(self):
        pdf = fitz.open()
        p = pdf.new_page(width=900, height=595)
        p.insert_text((40, 75), "PdP 001 | SK 1.1 | SP 1.1.1", fontsize=10)
        p.insert_text((40, 115), "Pemetaan buku teks belum disahkan;", fontsize=10)
        p.insert_text((40, 130), "rujuk buku dan DSKP sebelum READY.", fontsize=10)
        p.insert_text((40, 165), "Bahan: Mushaf al-Quran; tidak mereka halaman buku teks.", fontsize=10)
        pdf.new_page(width=900, height=595).insert_text((40, 75), "PdP 002 | SK 1.2 | DRAF", fontsize=10)
        raw = pdf.tobytes()
        with TemporaryDirectory() as folder:
            source = Path(folder) / "tahun_4.pdf"
            source.write_bytes(raw)
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            result = pdf_for_teacher(source)
            self.assertIsInstance(result, BytesIO)
            cleaned = fitz.open(stream=result.getvalue(), filetype="pdf")
            text = "".join(page.get_text() for page in cleaned)
            self.assertNotIn("Pemetaan buku teks", text)
            self.assertNotIn("tidak mereka halaman buku teks", text)
            for preserve in ("PdP 001", "SK 1.1", "SP 1.1.1", "PdP 002", "SK 1.2", "DRAF", "Bahan: Mushaf al-Quran"):
                self.assertIn(preserve, text)
            self.assertEqual(len(cleaned), 2)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)

    def test_unmarked_pdf_is_returned_unchanged(self):
        pdf = fitz.open()
        pdf.new_page().insert_text((40, 100), "SK 2.1; SP 2.1.1; DRAF", fontsize=10)
        pdf.new_page()
        raw = pdf.tobytes()
        with TemporaryDirectory() as folder:
            source = Path(folder) / "rpt.pdf"
            source.write_bytes(raw)
            self.assertEqual(pdf_for_teacher(source), source)
            self.assertEqual(source.read_bytes(), raw)

    def test_real_islamic_year4_pdf_if_present(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "rpt_2027/web_2027_pdfs/pendidikan_islam/tahun_4.pdf"
        if not path.is_file():
            self.skipTest("Original, 56-manifest RPT not present")
        original = path.read_bytes()
        cleaned = pdf_for_teacher(path)
        self.assertIsInstance(cleaned, BytesIO)
        a = fitz.open(stream=original, filetype="pdf")
        b = fitz.open(stream=cleaned.getvalue(), filetype="pdf")
        self.assertEqual(len(a), len(b))
        before = "".join(page.get_text() for page in a)
        after = "".join(page.get_text() for page in b)
        self.assertIn("DRAF SEMAKAN", after)
        self.assertIn("Pemetaan buku teks belum", before)
        self.assertNotIn("Pemetaan buku teks belum", after)
        self.assertNotIn("tidak mereka halaman buku teks", after)
        before_pdp = re.findall(r"PdP\s+(\d{3})", before)
        after_pdp = re.findall(r"PdP\s+(\d{3})", after)
        self.assertEqual(before_pdp, after_pdp)
        self.assertEqual(len(set(after_pdp)), 151)


if __name__ == "__main__":
    unittest.main()
