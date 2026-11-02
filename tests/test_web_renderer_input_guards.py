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


if __name__ == "__main__":
    unittest.main()
