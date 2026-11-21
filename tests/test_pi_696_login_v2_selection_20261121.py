"""Fail-closed migration from PI 696 v1 to owner-approved login-gallery v2."""
import io
import os
import unittest
from unittest.mock import patch
from docx import Document

from web import pi_696_private_bundle as pi


class TestPILoginLayoutV2(unittest.TestCase):
    def test_current_production_stays_v1_until_explicit_feature_switch(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(pi.V2_FLAG, None)
            self.assertEqual(pi._edition(), "v1")
            with patch.dict(os.environ, {pi.V2_FLAG: "0"}):
                self.assertEqual(pi._edition(), "v1")
            with patch.dict(os.environ, {pi.V2_FLAG: "1"}):
                self.assertEqual(pi._edition(), "v2")

    def test_new_source_hash_and_size_are_pinned_not_public(self):
        self.assertEqual(pi.ARCHIVES["v1"]["bytes"], 44284495)
        self.assertEqual(pi.ARCHIVES["v2"]["bytes"], 49779272)
        self.assertEqual(len(pi.ARCHIVES["v2"]["sha256"]), 64)
        self.assertNotEqual(pi.ARCHIVES["v2"]["sha256"], pi.ARCHIVES["v1"]["sha256"])
        self.assertTrue(pi.ARCHIVES["v2"]["object"].startswith("rph-premium/pi-2027/v2/"))

    def test_teacher_details_fill_only_the_left_grid_of_jawi_hero(self):
        source = Document()
        header = source.add_table(rows=1, cols=2)
        header.cell(0, 0).text = "Mata Pelajaran: Pendidikan Islam"
        teacher_grid = header.cell(0, 1).add_table(rows=4, cols=2)
        for idx, text in enumerate(("کلس", "تاريخ", "ماس", "بيلڠن موريد")):
            teacher_grid.cell(idx, 0).text = text
        details = source.add_table(rows=2, cols=2)
        details.cell(0, 0).text = "ستاندرد کاندوڠن"
        details.cell(0, 1).text = "1.1 Original SK content"
        activity = source.add_table(rows=2, cols=2)
        activity.cell(0, 0).text = "اکتيۏيتي اوتام"
        activity.cell(0, 1).text = "Original lesson activity content"
        activity.cell(1, 0).text = "رفليكسي (مانوال)"
        buf = io.BytesIO()
        source.save(buf)
        original = buf.getvalue()
        filled = pi._personalize_word(original, {
            "class": "4 Bestari", "date": "12/01/2027",
            "time": "08:00 - 09:00", "students": "30",
            "reflection": "24 murid mencapai objektif.",
        })
        # Source bytes and academic content stay unmodified.
        self.assertEqual(buf.getvalue(), original)
        result = Document(io.BytesIO(filled))
        self.assertEqual(result.tables[1].cell(0, 1).text, "1.1 Original SK content")
        self.assertEqual(result.tables[2].cell(0, 1).text, "Original lesson activity content")
        grid = result.tables[0].cell(0, 1).tables[0]
        for idx, value in enumerate(("4 Bestari", "12/01/2027", "08:00 - 09:00", "30")):
            self.assertIn(value, grid.cell(idx, 1).text)
        self.assertEqual(grid.cell(0, 0).text, "کلس")
        self.assertIn("24 murid mencapai objektif.", result.tables[2].cell(1, 1).text)

    def test_empty_teacher_details_do_not_reformat_source(self):
        with patch.object(pi, "_file", return_value=b"same original source"):
            result = pi.request_private_document(
                2, "35", "word", {"class": "", "date": "",
                                 "time": "", "students": "", "reflection": ""}, {})
        self.assertEqual(result.getvalue(), b"same original source")

    def test_v2_pdf_puts_latin_values_in_separate_empty_left_cells(self):
        try:
            import fitz
        except ImportError:
            self.skipTest("PyMuPDF not installed")
        document = fitz.open()
        document.new_page(width=595, height=842)
        source = document.tobytes()
        edited = pi._fill_pdf_fields(source, {
            "class": "4 Bestari", "date": "12/01/2027",
            "time": "08:00 - 09:00", "students": "30",
            "reflection": "",
        }, edition="v2")
        page = fitz.open(stream=edited, filetype="pdf")[0]
        expected = ["4 Bestari", "12/01/2027", "08:00 - 09:00", "30"]
        for idx, word in enumerate(expected):
            matching = page.search_for(word)
            self.assertEqual(len(matching), 1)
            box = matching[0]
            self.assertGreaterEqual(box.x0, 39)
            self.assertLessEqual(box.x1, 123)
            self.assertGreaterEqual(box.y0, 42 + 21.82 * idx)
            self.assertLessEqual(box.y1, 63 + 21.82 * idx)


if __name__ == "__main__":
    unittest.main()
