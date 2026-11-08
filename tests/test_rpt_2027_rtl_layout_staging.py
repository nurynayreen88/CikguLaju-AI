"""RPT 2027 direction regression: table RTL for Jawi PI/Arabic only.

The cover and 5-column schema stay unchanged. Data by PdP is never reversed;
only physical placement of logical columns is mirrored.
"""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from rpt_2027.common.format_2026_layout_preview import build_preview


def item(n):
    return {
        "id":f"{n:03d}","week":"M02",
        "a_start":"2027-01-10","a_end":"2027-01-14",
        "b_start":"2027-01-11","b_end":"2027-01-15",
        "unit":"Bidang: القرءان",
        "topic":"درس القراءة العربية",
        "sk":"1.1","sp":"1.1.1",
        "note":"Rujukan buku teks (DRAF).",
    }


class TableDirectionRegression(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()

    def pdf(self,sub):
        import fitz
        file=self.path/(sub+".pdf")
        build_preview(sub,4,[item(1),item(2)],file,max_span_rows=2)
        doc=fitz.open(file)
        self.assertEqual(doc.page_count,2)
        text=doc[0].get_text("text")
        for label in ("LOGO SEKOLAH","NAMA SEKOLAH","NAMA GURU"):
            self.assertIn(label,text)
        return doc

    def positions(self,page):
        x={}
        for label in ("MINGGU / TARIKH","UNIT / TAJUK / PDP",
                      "SK","SP","CATATAN / BAHAN"):
            hits=page.search_for(label)
            self.assertTrue(hits,(label,page.get_text()[:300]))
            x[label]=hits[0].x0
        return x

    def test_pi_and_arabic_are_true_right_to_left_five_columns(self):
        for subject in ("pendidikan_islam","bahasa_arab"):
            with self.subTest(subject=subject),self.pdf(subject) as pdf:
                p=pdf[1]
                x=self.positions(p)
                self.assertLess(x["CATATAN / BAHAN"],x["SP"])
                self.assertLess(x["SP"],x["SK"])
                self.assertLess(x["SK"],x["UNIT / TAJUK / PDP"])
                self.assertLess(x["UNIT / TAJUK / PDP"],x["MINGGU / TARIKH"])
                self.assertGreater(x["MINGGU / TARIKH"],650)
                self.assertIn("PdP 001",p.get_text())
                self.assertIn("PdP 002",p.get_text())
                self.assertEqual(p.get_text().count("M02"),1,
                                 "Merged week must stay in rightmost column")
                self.assertIn("1.1.1",p.get_text())
                self.assertEqual(len(p.search_for("MINGGU / TARIKH")),1)

    def test_other_subjects_remain_left_to_right(self):
        with self.pdf("english") as pdf:
            x=self.positions(pdf[1])
            self.assertLess(x["MINGGU / TARIKH"],x["UNIT / TAJUK / PDP"])
            self.assertLess(x["UNIT / TAJUK / PDP"],x["SK"])
            self.assertLess(x["SK"],x["SP"])
            self.assertLess(x["SP"],x["CATATAN / BAHAN"])


if __name__=="__main__":
    unittest.main()
