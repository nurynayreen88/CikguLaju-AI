"""Offline regression: five exact Year 2 Word lessons only."""
from pathlib import Path
from tempfile import TemporaryDirectory
import types
import unittest
from unittest.mock import patch

from docx import Document
from docx.shared import Cm, Pt

from web.english_y2_word_a4_runtime import OVERFLOW_LESSONS, _target, install


def word_text(doc):
    text=[p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for c in row.cells:
                text.extend(p.text for p in c.paragraphs)
    return "\n".join(text)


class Year2WordA4Tests(unittest.TestCase):
    def setUp(self):
        self.folder=TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/"test.docx"
        d=Document()
        d.add_heading("English Year 2",0)
        d.add_paragraph("Teacher models a specific book task. Pupils check and correct two errors.")
        t=d.add_table(rows=1,cols=2)
        t.cell(0,0).text="Activity"
        t.cell(0,1).text="Pupils write and revise the sentences, then explain one answer."
        d.save(self.path)
        self.calls=[]
        def writer(*args,**kwargs):
            self.calls.append((args,kwargs))
            return str(self.path)
        self.runtime=types.SimpleNamespace(create_word_file=writer)
        self.assertTrue(install(self.runtime))

    def test_five_target_lessons_retain_full_word_text(self):
        for n in sorted(OVERFLOW_LESSONS):
            with self.subTest(n=n):
                original=word_text(Document(self.path))
                result=self.runtime.create_word_file({"subject":"English","year":"Tahun 2","task":"rph","lesson_no":n},"rph",42)
                self.assertEqual(result,str(self.path))
                doc=Document(self.path)
                self.assertEqual(word_text(doc),original)
                self.assertAlmostEqual(doc.sections[0].top_margin.cm,.52,places=2)
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for p in cell.paragraphs:
                                for run in p.runs:
                                    self.assertAlmostEqual(run.font.size.pt,8.0,places=1)

    def test_unrelated_years_subjects_tasks_are_not_modified(self):
        invalid=[
            {"subject":"English","year":"Tahun 2","task":"rph","lesson_no":1},
            {"subject":"English","year":"Tahun 2","task":"rph","lesson_no":15},
            {"subject":"English","year":"Tahun 3","task":"rph","lesson_no":2},
            {"subject":"English","year":"Tahun 5","task":"rph","lesson_no":2},
            {"subject":"Matematik","year":"Tahun 2","task":"rph","lesson_no":2},
            {"subject":"English","year":"Tahun 2","task":"worksheet","lesson_no":2},
            {"subject":"English","year":"Tahun 2","task":"rph","lesson_no":True},
            {"subject":"English","year":"Tahun 2","task":"rph","lesson_no":2.5},
            {"subject":"English","year":"Tahun 2","task":"rph","lesson_no":"../2"},
            {"subject":"English","year":"Tahun 2","task":"rph","lesson_no":0,"textbook_lesson_no":2},
            None,
        ]
        baseline=self.path.read_bytes()
        for state in invalid:
            with self.subTest(state=state):
                self.assertFalse(_target(state))
                self.assertEqual(self.runtime.create_word_file(state,"rph",42),str(self.path))
                self.assertEqual(self.path.read_bytes(),baseline)

    def test_adapter_does_not_modify_credits_or_call_other_production_functions(self):
        original=self.runtime.create_word_file
        self.assertTrue(install(self.runtime))
        self.assertIs(original,self.runtime.create_word_file)
        self.assertFalse(hasattr(self.runtime,"_rph_rows"))
        self.assertFalse(hasattr(self.runtime,"state"))

    def test_compaction_failure_still_returns_original_document(self):
        with patch("web.english_y2_word_a4_runtime.compact_word_file",return_value=False) as mocked:
            path=self.runtime.create_word_file({"subject":"English","year":"Tahun 2","task":"rph","lesson_no":3},"rph",42)
            self.assertEqual(path,str(self.path))
            mocked.assert_called_once_with(path)


if __name__=="__main__":
    unittest.main()
