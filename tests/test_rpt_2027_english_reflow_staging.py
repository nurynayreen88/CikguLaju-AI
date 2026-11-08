"""English Year 2–6 new format only; never replaces published 2027 PDFs."""
import tempfile
import unittest
from pathlib import Path
import fitz
from scripts.build_rpt_2027_english_pdf_reflow_staging import english_records,build_all


class EnglishFiveColumnQA(unittest.TestCase):
    def test_all_800_english_lessons_from_original_pdf(self):
        count=0
        for y in range(2,7):
            rows=english_records(y)
            self.assertEqual(len(rows),160)
            self.assertEqual([r["id"] for r in rows],
                             [f"{i:03d}" for i in range(1,161)])
            self.assertEqual(rows[0]["week"],"M01")
            self.assertEqual(rows[-1]["week"],"M40")
            self.assertTrue(all(r["sk"] and r["sp"] and r["sk_display"] and r["sp_display"]
                                for r in rows))
            for row in rows:
                self.assertTrue(row["unit"])
                self.assertTrue(row["note"])
                self.assertTrue(row["display_id"].startswith("Lesson "))
            count+=len(rows)
        self.assertEqual(count,800)

    def test_five_reflows_have_5_columns_and_all_lessons(self):
        with tempfile.TemporaryDirectory() as temp:
            outputs=build_all(temp)
            self.assertEqual(len(outputs),5)
            for y,number,p in outputs:
                self.assertEqual(number,160)
                self.assertTrue(Path(p).is_file())
                with fitz.open(p) as doc:
                    self.assertGreater(doc.page_count,2)
                    self.assertTrue(all(pg.rect.width>pg.rect.height for pg in doc))
                    text="\n".join(pg.get_text() for pg in list(doc)[1:])
                    self.assertIn("Lesson 001",text)
                    self.assertIn("Lesson 160",text)
                    self.assertIn("M01",text)
                    self.assertIn("M40",text)
                    for expected in ("WEEK / DATE","UNIT / TOPIC / LESSON",
                                     "CONTENT STANDARD","LEARNING STANDARD",
                                     "NOTES / MATERIALS"):
                        self.assertIn(expected,text)
                    self.assertNotIn("MINGGU / TARIKH",text)
                    self.assertNotIn("CATATAN / BAHAN",text)


if __name__=="__main__":
    unittest.main()
