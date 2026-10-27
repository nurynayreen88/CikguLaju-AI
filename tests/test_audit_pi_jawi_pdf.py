"""Regression checks for read-only PI PDF structural auditing."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

try:
    import fitz
except ImportError:
    fitz = None

MODULE = Path(__file__).resolve().parents[1] / "tools" / "audit_pi_jawi_pdf.py"
spec = importlib.util.spec_from_file_location("audit_pi_jawi_pdf", MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


@unittest.skipIf(fitz is None, "PyMuPDF is required")
class AuditPiJawiPdfTests(unittest.TestCase):
    def make_pdf(self, path, width=595.28, height=841.89, text=None):
        doc = fitz.open()
        page = doc.new_page(width=width, height=height)
        if text:
            page.insert_text((72, 72), text)
        doc.save(str(path))
        doc.close()

    def test_empty_a4_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.pdf"
            self.make_pdf(path)
            result = audit.inspect_pdf(path)
            self.assertFalse(result["structural_pass"])
            self.assertEqual(result["jawi_visual_approval"], "NOT_ASSESSED")

    def test_text_a4_passes_structure_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rph.pdf"
            self.make_pdf(path, text="Rancangan Pengajaran Harian")
            result = audit.inspect_pdf(path)
            self.assertTrue(result["structural_pass"])
            self.assertEqual(result["page_count"], 1)
            self.assertEqual(result["jawi_visual_approval"], "NOT_ASSESSED")

    def test_non_a4_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "letter.pdf"
            self.make_pdf(path, width=612, height=792, text="RPH")
            self.assertFalse(audit.inspect_pdf(path)["structural_pass"])

    def test_invalid_pdf_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.pdf"
            path.write_bytes(b"not a pdf")
            with self.assertRaises(ValueError):
                audit.inspect_pdf(path)


if __name__ == "__main__":
    unittest.main()
