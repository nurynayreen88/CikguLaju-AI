"""Validate fail-closed input guards before rendering RPH files."""
import unittest
from web.rph_document_renderer import ApprovedRPH, render_approved_rph


class RendererInputTests(unittest.TestCase):
    def test_rejects_malformed_values_without_rendering(self):
        cases = [
            ApprovedRPH(True, "Lesson", "Content", "approved"),
            ApprovedRPH(1, "Lesson", "Content", None),
            ApprovedRPH(1, None, "Content", "approved"),
            ApprovedRPH(1, "Lesson", None, "approved"),
            ApprovedRPH(1, "Lesson", "Content", " "),
        ]
        for item in cases:
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    render_approved_rph(item, "docx")

    def test_rejects_oversized_content_and_unsupported_format(self):
        valid = ApprovedRPH(1, "Lesson", "Content", "approved")
        with self.assertRaises(ValueError):
            render_approved_rph(valid, "txt")
        with self.assertRaises(ValueError):
            render_approved_rph(ApprovedRPH(1, "X" * 301, "Content", "approved"), "docx")
        with self.assertRaises(ValueError):
            render_approved_rph(ApprovedRPH(1, "Lesson", "X" * 100001, "approved"), "pdf")


if __name__ == "__main__":
    unittest.main()
