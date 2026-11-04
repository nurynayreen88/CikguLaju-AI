"""Proof Word A4 changes only newly provisionally exposed English Y4/Y5 RPH.

No app import and no user database interaction.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import types
import unittest
from docx import Document
from docx.shared import Cm

from web.english_y4_y5_draft_word_a4_runtime import _target, install


def word_text(path):
    d=Document(str(path))
    result=[p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            for cell in row.cells:
                result.extend(p.text for p in cell.paragraphs)
    return "\n".join(result)


class Y4Y5DraftWordA4Scope(unittest.TestCase):
    def setUp(self):
        self.dir=TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.file=Path(self.dir.name)/"rph.docx"
        d=Document()
        d.add_paragraph("Teacher plans tasks, pupils complete lesson activities")
        t=d.add_table(rows=2,cols=2)
        t.cell(0,0).text="RPH"
        t.cell(0,1).text="Lesson-specific pupil response"
        t.cell(1,0).text="PBD"
        t.cell(1,1).text="Teacher checks individual evidence"
        d.save(self.file)

    def test_matching_162_only(self):
        for year, n in ((4,16),(4,30),(4,160),(5,1),(5,90),(5,141),(5,159)):
            self.assertTrue(_target({"year":f"Year {year}","subject":"English",
                                     "lesson_no":n,"task":"rph"}),(year,n))
        for year, n in ((4,1),(4,15),(4,31),(4,159),
                        (5,16),(5,34),(5,88),(5,160),(6,30),(1,30),(3,30)):
            self.assertFalse(_target({"year":f"Year {year}","subject":"English",
                                      "lesson_no":n,"task":"rph"}),(year,n))
        for st in ({"year":"Year 4","subject":"Matematik","lesson_no":16,"task":"rph"},
                   {"year":"Year 5","subject":"Sains","lesson_no":90,"task":"rph"},
                   {"year":"Year 5","subject":"English","lesson_no":90,"task":"worksheet"},
                   {"year":"Year 4","subject":"English","lesson_no":"../16","task":"rph"},
                   {"year":"Year 5","subject":"English","lesson_no":True,"task":"rph"}):
            self.assertFalse(_target(st),st)

    def test_compaction_is_text_preserving_and_non_target_bytes_unchanged(self):
        calls=[]
        def prior(*args,**kwargs):
            calls.append(args)
            return str(self.file)
        runtime=types.SimpleNamespace(create_word_file=prior,
                    callback=lambda *_:"unchanged",quota=lambda:10)
        self.assertTrue(install(runtime))
        self.assertTrue(install(runtime))
        before=word_text(self.file)
        result=runtime.create_word_file({"subject":"English","year":"Year 5",
                                         "lesson_no":90,"task":"rph"},"source",1)
        self.assertEqual(result,str(self.file))
        self.assertEqual(word_text(self.file),before)
        self.assertAlmostEqual(Document(self.file).sections[0].top_margin.cm,0.52,places=1)
        old=self.file.read_bytes()
        runtime.create_word_file({"subject":"English","year":"Year 5",
                                  "lesson_no":88,"task":"rph"},"source",1)
        self.assertEqual(self.file.read_bytes(),old)
        runtime.create_word_file({"subject":"English","year":"Year 4",
                                  "lesson_no":159,"task":"rph"},"source",1)
        self.assertEqual(self.file.read_bytes(),old)
        self.assertEqual(len(calls),3)
        self.assertEqual(runtime.quota(),10)
        self.assertEqual(runtime.callback("menu"),"unchanged")


if __name__=="__main__":
    unittest.main()
