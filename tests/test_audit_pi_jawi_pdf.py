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


    def make_grid_pdf(self, path, *, shifted=False, split_header=False):
        doc = fitz.open()
        page = doc.new_page(width=595.28, height=841.89)
        page.insert_text((72, 72), "RPH Pendidikan Islam — grid geometry fixture")
        for index in range(4):
            left = 33 + (7 if shifted and index == 2 else 0)
            top = 100 + index * 100
            if index == 0 and split_header:
                # Two RTL head panels, physically split at the shared border.
                page.draw_line((left, top), (left + 205, top))
                page.draw_line((left + 205, top), (left + 530, top))
                page.draw_line((left, top + 65), (left + 205, top + 65))
                page.draw_line((left + 205, top + 65), (left + 530, top + 65))
            else:
                page.draw_rect(fitz.Rect(left, top, left + 530, top + 65))
        doc.save(str(path))
        doc.close()

    def test_aligned_vector_grid_passes_separate_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "aligned.pdf"
            self.make_grid_pdf(path, split_header=True)
            result = audit.inspect_pdf(path)
            self.assertTrue(result["structural_pass"])
            self.assertEqual(result["pages"][0]["grid_alignment"]["status"], "ALIGNED")
            self.assertGreaterEqual(result["pages"][0]["grid_alignment"]["full_width_rule_count"], 8)
            self.assertEqual(result["jawi_visual_approval"], "NOT_ASSESSED")

    def test_one_shifted_box_detected_without_claiming_visual_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shifted.pdf"
            self.make_grid_pdf(path, shifted=True, split_header=True)
            result = audit.inspect_pdf(path)
            self.assertTrue(result["structural_pass"])  # Legacy A4/text gate unchanged
            grid = result["pages"][0]["grid_alignment"]
            self.assertEqual(grid["status"], "MISALIGNED")
            self.assertGreaterEqual(grid["left_edge_drift_pt"], 6)
            self.assertGreaterEqual(grid["right_edge_drift_pt"], 6)

    def test_text_only_pdf_never_gets_false_grid_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "no-grid.pdf"
            self.make_pdf(path, text="RPH")
            result = audit.inspect_pdf(path)
            self.assertTrue(result["structural_pass"])
            self.assertEqual(result["pages"][0]["grid_alignment"]["status"], "NOT_ASSESSED")

    def test_strict_cli_grid_gate_fails_closed_for_non_grid_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "no-grid.pdf"
            self.make_pdf(path, text="RPH")
            import subprocess
            import sys
            result = subprocess.run(
                [sys.executable, str(MODULE), str(path), "--require-aligned-grid"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn('"status": "NOT_ASSESSED"', result.stdout)



if __name__ == "__main__":
    unittest.main()
