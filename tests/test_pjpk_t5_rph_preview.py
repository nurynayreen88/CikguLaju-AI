"""A4 HTML preview smoke checks; does not certify physical one-page fit."""
import html
import json
import tempfile
import unittest
from pathlib import Path
from scripts.pjpk_t5_rph_preview import render, preview_all
from scripts.pjpk_t5_complete_rph_audit import JSON_PATH

class RPHPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))["records"]
    def test_all_three_previews_generated(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(preview_all(d), 3)
            self.assertEqual(len(list(Path(d).glob("*.html"))), 3)
    def test_stored_activity_text_is_preserved(self):
        for row in self.rows:
            rendered = render(row)
            for activity in row["activities"]:
                self.assertIn(html.escape(activity["heading"]), rendered)
                self.assertIn(html.escape(activity["body"]), rendered)
    def test_a4_print_styles_and_draft_label(self):
        output = render(self.rows[0])
        self.assertIn("size:A4 portrait", output)
        self.assertIn("BELUM DILULUSKAN UNTUK PRODUKSI", output)
    def test_teacher_fields_are_escaped(self):
        output = render(self.rows[0], {"class": "<script>alert(1)</script>"})
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)
    def test_reject_production_ready_mutation(self):
        row = dict(self.rows[0], production_ready=True)
        with self.assertRaises(ValueError):
            render(row)

if __name__ == "__main__":
    unittest.main()
