from io import BytesIO
import re
import unittest
from docx import Document
from docx.oxml.ns import qn
import pymupdf
from staging.matematik_sjkc.tahun_2 import rph as y2
from staging.matematik_sjkc.tahun_3 import rph as y3
from tools.sjkc_math_shared_layout_qa_20261124 import word_for, pdf_for_qa


def compact(s):
    return re.sub(r"\s+", "", s)


class SjkcSharedLayout(unittest.TestCase):
    def test_all_192_word_layouts(self):
        for year, source in ((2,y2),(3,y3)):
            for lesson in source.lessons():
                with self.subTest(year=year,pdp=lesson["pdp"]):
                    result = Document(BytesIO(word_for(year, lesson)))
                    self.assertEqual(len(result.tables),2)
                    hero, grid = result.tables
                    self.assertEqual(sum(c.width for c in hero.rows[0].cells),
                                     sum(c.width for c in grid.rows[0].cells))
                    self.assertGreater(hero.cell(0,0).width,hero.cell(0,1).width)
                    self.assertTrue(hero.cell(0,0).paragraphs[0].runs[0].bold)
                    self.assertIn(lesson["topic"],hero.cell(0,0).text)
                    self.assertNotIn("PdP",hero.cell(0,0).text)
                    self.assertEqual([p.text for p in hero.cell(0,1).paragraphs],
                                     ["班级 Kelas：","日期 Tarikh：","时间 Masa：","学生人数 Bilangan Murid："])
                    main = next(row.cells[1] for row in grid.rows if row.cells[0].text=="主要活动")
                    self.assertEqual(sum(bool(p.runs and p.runs[0].bold) for p in main.paragraphs),3)
                    self.assertEqual(grid.rows[-1].cells[0].text,"教学反思")
                    text = "\n".join(c.text for row in grid.rows for c in row.cells)
                    for code in lesson["sp"]:
                        self.assertIn(code,text)

    def test_sample_pdf_from_same_word(self):
        teacher = {"class":"3A","date":"04/01/2027","time":"08:00–09:00",
                   "students":"28","reflection":"学生完成练习，教师继续指导。"}
        for year, source in ((2,y2),(3,y3)):
            for idx in (0,16,95):
                lesson = source.lessons()[idx]
                with self.subTest(year=year,pdp=lesson["pdp"]):
                    word = word_for(year,lesson,teacher)
                    doc = Document(BytesIO(word))
                    with pymupdf.open(stream=pdf_for_qa(word),filetype="pdf") as pdf:
                        self.assertEqual(len(pdf),1)
                        page = pdf[0]
                        self.assertAlmostEqual(page.rect.width,595.28,delta=2)
                        self.assertAlmostEqual(page.rect.height,841.89,delta=2)
                        txt = compact(page.get_text())
                        for row in doc.tables[1].rows:
                            self.assertIn(compact(row.cells[1].text),txt)
                        for value in teacher.values():
                            self.assertIn(compact(value),txt)
                        for block in page.get_text("blocks"):
                            self.assertGreaterEqual(block[0],0)
                            self.assertLessEqual(block[2],page.rect.width)
                            self.assertLessEqual(block[3],page.rect.height)

if __name__=="__main__":
    unittest.main()
