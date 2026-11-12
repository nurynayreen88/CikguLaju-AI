"""Ensure Science previews are only 387 DSKP SP entries, not fake RPT lessons."""
import tempfile
import unittest
from pathlib import Path
import fitz
from scripts.build_rpt_2027_science_dskp_index_not_annual_plan import science_source,build_all

class ScienceStandardIndexQA(unittest.TestCase):
    def test_source_exactly_387_SP_not_RPT(self):
        items=science_source()
        expected={2:31,3:30,4:110,5:107,6:109}
        self.assertEqual({k:len(v) for k,v in items.items()},expected)
        for year,rows in items.items():
            self.assertEqual([r["id"] for r in rows], [f"{i:03d}" for i in range(1,len(rows)+1)])
            for r in rows:
                self.assertFalse(r["week"])
                self.assertFalse(r.get("a_start"))
                self.assertTrue(r["sp_display"].startswith(r["sp"]+" — "))
                self.assertTrue(r["sk_display"].startswith(r["sk"]+" — "))
                self.assertIn("BUKAN RPT PdP",r["note"])

    def test_five_visual_staging_source_index_pdfs(self):
        with tempfile.TemporaryDirectory() as temp:
            results=build_all(temp)
            self.assertEqual(len(results),5)
            for year,n,p in results:
                self.assertTrue(Path(p).is_file())
                with fitz.open(p) as doc:
                    self.assertGreater(doc.page_count,1)
                    self.assertTrue(all(x.rect.width>x.rect.height for x in doc))
                    text="\n".join(x.get_text() for x in list(doc)[1:])
                    self.assertIn("INDEKS DSKP SAHAJA",text)
                    self.assertIn("BUKAN RPT",text)
                    self.assertIn("SK",text)
                    self.assertIn("SP",text)
if __name__=="__main__":
    unittest.main()
