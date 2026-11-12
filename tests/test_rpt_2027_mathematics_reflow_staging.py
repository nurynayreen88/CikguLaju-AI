"""Math 2027 RPT new PDF layout from existing Year2–6 117-Lesson source."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
import fitz
from scripts.build_rpt_2027_mathematics_pdf_reflow_staging import math_records,build_all

class MathematicsReflowQA(unittest.TestCase):
    def test_5_years_each_117_source_lessons(self):
        for year in range(2,7):
            with self.subTest(year=year):
                rows=math_records(year)
                self.assertEqual(len(rows),117)
                self.assertEqual([x["id"] for x in rows], [f"{i:03d}" for i in range(1,118)])
                for row in rows:
                    self.assertTrue(row["sk"] and row["sp"] and row["unit"] and row["note"])
                    self.assertTrue(row["sp_display"].startswith(row["sp"]))
                    self.assertTrue(row["week"] and row["a_start"] and row["b_start"])

    def test_5_pdf_landscape_five_col(self):
        with tempfile.TemporaryDirectory() as t:
            files=build_all(t)
            self.assertEqual(len(files),5)
            for year,n,path in files:
                self.assertEqual(n,117)
                self.assertTrue(Path(path).exists())
                with fitz.open(path) as doc:
                    self.assertGreater(doc.page_count,1)
                    self.assertTrue(all(p.rect.width>p.rect.height for p in doc))
                    text="\n".join(p.get_text() for p in list(doc)[1:])
                    self.assertIn("Lesson 001",text)
                    self.assertIn("Lesson 117",text)
                    self.assertIn("MINGGU / TARIKH",text)
                    self.assertIn("CATATAN / BAHAN",text)

if __name__=="__main__":
    unittest.main()
