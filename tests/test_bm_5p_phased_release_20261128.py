import os
import unittest
from io import BytesIO
from unittest.mock import patch
import fitz
from docx import Document
from web import kp2027_bm_5p_release as gate, kp2027_bm_5p as five

class TestBMPhasedRelease(unittest.TestCase):
    def test_default_and_initial_review_never_release(self):
        self.assertEqual(len(gate.reviewed_records()),24)
        for flag in ("0","1"):
            with patch.dict(os.environ,{gate.FLAG:flag}):
                self.assertEqual(gate.released_groups(),{"A":[],"B":[]})
                self.assertFalse(gate.is_released("A",1))
        with patch.dict(os.environ,{gate.FLAG:"1"}),patch.object(gate,"reviewed_records",side_effect=ValueError("drift")):
            self.assertEqual(gate.released_groups(),{"A":[],"B":[]})

    def test_all_corrected_candidates_render(self):
        for (g,n),row in gate.reviewed_records().items():
            for fields in ({},{"teacher_class":"1 Bestari","teacher_date":"2027-03-02","teacher_start":"08:00","teacher_end":"09:00","teacher_students":"30","reflection_mode":"manual","reflection":"Murid memerlukan latihan susulan."}):
                with self.subTest(group=g,lesson=n,personalized=bool(fields)):
                    source,c,raw,profile=five.prepare(g,n,fields,reviewed=True)
                    self.assertEqual(c["phases"],row["proposed_phases"])
                    self.assertEqual(source["criteria"],row["source_criteria"])
                    doc=Document(BytesIO(five.render(g,n,"word",fields,reviewed=True)))
                    self.assertEqual(len(doc.tables),1)
                    self.assertEqual(len(doc.tables[0].rows),21)
                    with fitz.open(stream=five.render(g,n,"pdf",fields,reviewed=True),filetype="pdf") as pdf:
                        self.assertEqual(len(pdf),1)
                        self.assertAlmostEqual(pdf[0].rect.width,595.28,places=1)
                        self.assertAlmostEqual(pdf[0].rect.height,841.89,places=1)
                        self.assertIn("Penilaian",pdf[0].get_text())

if __name__=="__main__":
    unittest.main()
