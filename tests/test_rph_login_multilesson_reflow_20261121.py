"""Guard source-preserving one-PdP layout migration for SJKC and Science DLP."""
import unittest
from docx import Document
from tools.rph_reflow_multilesson_login_20261121 import convert_sjkc, convert_dlp


def sjkc_fixture():
    d=Document()
    for text in ("RPH Matematik SJKC Tahun 3", "PdP 001 - Unit 1",
                 "Number sense", "Class / Time (blank)",
                 "SK 1.1 and SP 1.1.1 full originals",
                 "Original learning objective: count to ten",
                 "Original materials for Number sense",
                 "Original textbook references",
                 "Original reflection for SJKC maths"):
        d.add_paragraph(text)
    t=d.add_table(rows=6,cols=3)
    for r in range(6):
        for c in range(3):
            t.cell(r,c).text=(f"Original row {r} col {c}"
                              if r else f"Table header {c}")
    return d


def dlp_fixture():
    d=Document()
    for text in ("Daily Lesson Plan", "Science DLP Year 3", "Observe with senses"):
        d.add_paragraph(text)
    a=d.add_table(rows=8,cols=2)
    for r in range(8):
        a.cell(r,0).text=f"Label {r}"
        a.cell(r,1).text=f"Original science details {r}"
    b=d.add_table(rows=5,cols=3)
    for r in range(5):
        b.cell(r,0).text=f"Stage {r}"
        b.cell(r,1).text=f"Original teacher actions {r}"
        b.cell(r,2).text=f"Original pupil actions {r}"
    c=d.add_table(rows=1,cols=2)
    c.cell(0,0).text="Reflection"
    c.cell(0,1).text="Original reflection and follow up"
    return d


def all_text(doc):
    return "\n".join([p.text for p in doc.paragraphs]+
                     [c.text for t in doc.tables for r in t.rows for c in r.cells])


class TestSourcePreservingLayout(unittest.TestCase):
    def test_sjkc_maths_original_lesson_survives_in_two_tables(self):
        out=convert_sjkc(sjkc_fixture())
        self.assertEqual(len(out.tables),3)
        self.assertEqual(len(out.tables[0].cell(0,1).tables[0].rows),4)
        body=all_text(out)
        for phrase in ("SK 1.1 and SP 1.1.1 full originals",
                       "Original learning objective: count to ten",
                       "Original materials for Number sense",
                       "Original textbook references",
                       "Original reflection for SJKC maths",
                       "Original row 2 col 2", "Original row 5 col 2"):
            self.assertIn(phrase,body)

    def test_dlp_original_teacher_pupil_actions_survive(self):
        out=convert_dlp(dlp_fixture())
        self.assertEqual(len(out.tables),3)
        body=all_text(out)
        for phrase in ("Observe with senses", "Original science details 0",
                       "Original science details 7", "Original teacher actions 1",
                       "Original pupil actions 1", "Original teacher actions 4",
                       "Original pupil actions 4", "Original reflection and follow up"):
            self.assertIn(phrase,body)

    def test_unexpected_shapes_never_rewrite_source(self):
        with self.assertRaises(ValueError):
            convert_sjkc(dlp_fixture())
        with self.assertRaises(ValueError):
            convert_dlp(sjkc_fixture())


if __name__=="__main__":
    unittest.main()
