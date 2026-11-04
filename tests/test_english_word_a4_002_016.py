"""Two scoped A4 Word fixes: Year4 Lesson002 and Year6 Lesson016 only."""
from pathlib import Path
from tempfile import TemporaryDirectory
import types
import unittest

from docx import Document
from docx.shared import Pt
from web.english_y4_l002_word_a4_runtime import _target as y4_target, install as install_y4
from web.english_y6_word_a4_runtime import _lesson16_choice, install as install_y6, compact_word_file


def _full_text(path):
    doc=Document(str(path))
    result=[p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                result.extend(p.text for p in cell.paragraphs)
    return "\n".join(result)


class ScopedEnglishWordA4(unittest.TestCase):
    def test_y4_only_l002_source_valid_and_no_other_year(self):
        self.assertTrue(y4_target({"subject":"English","year":"Year 4",
                                   "lesson_no":2,"task":"rph"}))
        for n in (1,3,30,160):
            self.assertFalse(y4_target({"subject":"English","year":"Year 4",
                                        "lesson_no":n,"task":"rph"}))
        for state in ({"subject":"English","year":"Year 5","lesson_no":2,"task":"rph"},
                      {"subject":"English","year":"Year 1","lesson_no":2,"task":"rph"},
                      {"subject":"BM","year":"Year 4","lesson_no":2,"task":"rph"},
                      {"subject":"English","year":"Year 4","lesson_no":2,"task":"worksheet"},
                      {"subject":"English","year":"Year 4","lesson_no":True,"task":"rph"},
                      {"subject":"English","year":"Year 4","lesson_no":2,
                       "sp_code":"9.9.9","task":"rph"}):
            self.assertFalse(y4_target(state),state)

    def test_y6_l016_only_uses_7_5pt(self):
        self.assertTrue(_lesson16_choice({"subject":"English","year":"Year 6",
                                           "lesson_no":16,"task":"rph"}))
        for year,n in ((1,16),(4,16),(5,16),(6,15),(6,17),(6,160)):
            self.assertFalse(_lesson16_choice({"subject":"English","year":f"Year {year}",
                                                "lesson_no":n,"task":"rph"}))

    def test_exact_styles_text_preservation_and_non_target(self):
        with TemporaryDirectory() as d:
            path=Path(d)/"rph.docx"
            calls=[]
            def previous(state,*a,**kw):
                doc=Document()
                doc.styles["Normal"].font.size=Pt(10)
                doc.add_paragraph("Source-backed actions and PBD must not be removed.")
                table=doc.add_table(rows=1,cols=2)
                table.cell(0,0).text="Teacher: instruct"
                table.cell(0,1).text="Pupils: complete matching task"
                doc.save(path)
                calls.append((state["year"],state["lesson_no"]))
                return str(path)
            rt=types.SimpleNamespace(create_word_file=previous,
                                     quota=lambda:10,callback=lambda:"home")
            self.assertTrue(install_y6(rt))
            self.assertTrue(install_y4(rt))
            self.assertTrue(install_y6(rt))
            self.assertTrue(install_y4(rt))
            targets=[("Year 4",2,8.0),("Year 4",3,10.0),
                     ("Year 6",16,7.5),("Year 6",17,8.0),
                     ("Year 5",16,10.0),("Year 1",16,10.0)]
            for year,n,points in targets:
                result=rt.create_word_file({"subject":"English","year":year,
                                            "lesson_no":n,"task":"rph"})
                self.assertEqual(result,str(path))
                txt=_full_text(path)
                self.assertIn("Source-backed actions",txt)
                self.assertIn("Pupils: complete matching task",txt)
                font=Document(str(path)).styles["Normal"].font.size.pt
                self.assertAlmostEqual(font,points,delta=0.06)
            self.assertEqual(len(calls),len(targets))
            self.assertEqual(rt.quota(),10)
            self.assertEqual(rt.callback(),"home")

    def test_invalid_font_size_fails_closed_without_overwriting(self):
        with TemporaryDirectory() as d:
            path=Path(d)/"file.docx"
            doc=Document(); doc.add_paragraph("Original source")
            doc.save(path)
            before=path.read_bytes()
            self.assertFalse(compact_word_file(path,point_size=3))
            self.assertEqual(path.read_bytes(),before)
            self.assertFalse(compact_word_file(path,point_size=True))
            self.assertEqual(path.read_bytes(),before)


if __name__=="__main__":
    unittest.main()
