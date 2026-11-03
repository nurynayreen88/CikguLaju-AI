"""Offline Year 6 Word A4 adapter tests. Never imports app.py or accesses user DB."""
from pathlib import Path
from tempfile import TemporaryDirectory
import types
import unittest

from docx import Document
from docx.shared import Cm, Pt

from web.english_y6_word_a4_runtime import (
    _is_year6_english_rph, compact_word_file, install,
)


def all_text(doc):
    result = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                result.extend(p.text for p in cell.paragraphs)
    return result


class Year6WordA4Tests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "English_Y6_L015.docx"
        doc = Document()
        sec = doc.sections[0]
        sec.page_width = Cm(21)
        sec.page_height = Cm(29.7)
        sec.top_margin = Cm(.75)
        sec.bottom_margin = Cm(.75)
        doc.add_heading("DAILY LESSON PLAN", 1)
        table = doc.add_table(rows=3, cols=2)
        table.cell(0, 0).text = "Learning objective"
        table.cell(0, 1).text = "Ten imaginary sandwich ingredients, spell eight familiar words correctly."
        table.cell(1, 0).text = "Main activities"
        table.cell(1, 1).text = "Teacher models a Silly Sandwich; pupils list, illustrate, label and explain."
        table.cell(2, 0).text = "PBD"
        table.cell(2, 1).text = "Check ingredient list and two imaginative choices."
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.font.size = Pt(8.5)
        doc.save(self.path)
        self.calls = []
        def original(*args, **kwargs):
            self.calls.append((args, kwargs))
            return str(self.path)
        self.runtime = types.SimpleNamespace(create_word_file=original)

    def test_only_year6_rph_is_targeted(self):
        self.assertTrue(_is_year6_english_rph({"subject":"English","year":"Tahun 6","task":"rph"}))
        self.assertTrue(_is_year6_english_rph({"subject":"Bahasa Inggeris","year":"6","task":"RPH"}))
        self.assertFalse(_is_year6_english_rph({"subject":"Matematik","year":"Tahun 6","task":"rph"}))
        self.assertFalse(_is_year6_english_rph({"subject":"English","year":"Tahun 5","task":"rph"}))
        self.assertFalse(_is_year6_english_rph({"subject":"English","year":"Tahun 6","task":"worksheet"}))
        self.assertFalse(_is_year6_english_rph(None))

    def test_year6_compacts_without_losing_activities_or_pbd(self):
        before = all_text(Document(self.path))
        self.assertTrue(install(self.runtime))
        result = self.runtime.create_word_file(
            {"subject":"English","year":"Tahun 6","task":"rph"}, "draft", 123
        )
        self.assertEqual(result, str(self.path))
        self.assertEqual(len(self.calls), 1)
        after = Document(self.path)
        self.assertEqual(before, all_text(after))
        self.assertAlmostEqual(after.sections[0].top_margin.cm, 0.52, places=1)
        self.assertAlmostEqual(after.sections[0].left_margin.cm, 0.95, places=1)
        self.assertAlmostEqual(after.tables[0].cell(0,1).paragraphs[0].runs[0].font.size.pt,8.0)
        self.assertEqual(len(after.tables), 1)

    def test_not_targeted_years_and_tasks_keep_identical_docx_bytes(self):
        self.assertTrue(install(self.runtime))
        for state in (
            {"subject":"English","year":"Tahun 2","task":"rph"},
            {"subject":"English","year":"Tahun 5","task":"rph"},
            {"subject":"English","year":"Tahun 6","task":"worksheet"},
            {"subject":"Sains","year":"Tahun 6","task":"rph"},
        ):
            with self.subTest(state=state):
                before=self.path.read_bytes()
                self.runtime.create_word_file(state, "draft", 123)
                self.assertEqual(before,self.path.read_bytes())

    def test_invalid_docx_preserves_original_and_does_not_block_delivery(self):
        self.path.write_bytes(b"not a real Word file")
        before=self.path.read_bytes()
        self.assertFalse(compact_word_file(self.path))
        self.assertEqual(before,self.path.read_bytes())
        self.assertTrue(install(self.runtime))
        self.assertEqual(
            self.runtime.create_word_file({"subject":"English","year":"6","task":"rph"},"",123),
            str(self.path))
        self.assertEqual(self.path.read_bytes(),before)

    def test_install_idempotent_and_no_generator_twice(self):
        self.assertTrue(install(self.runtime))
        self.assertTrue(install(self.runtime))
        self.runtime.create_word_file({"subject":"English","year":"Tahun 6","task":"rph"},"",1)
        self.assertEqual(len(self.calls),1)
        self.assertFalse(install(types.SimpleNamespace()))

if __name__=="__main__":
    unittest.main()
