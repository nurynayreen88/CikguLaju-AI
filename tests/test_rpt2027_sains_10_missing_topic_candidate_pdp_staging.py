"""Five truly absent Sains topics are addressed by ten sourced-SP draft blocks."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from scripts.build_rpt2027_sains_10_missing_topic_candidate_pdp_staging import candidate_rows_by_year,build_all

class Sains10MissingTopicBlocksTests(unittest.TestCase):
    def test_ten_blocks_cover_exactly_21_missing_verified_sp(self):
        years=candidate_rows_by_year()
        self.assertEqual({year:len(rows) for year,rows in years.items()},{4:4,5:4,6:2})
        codes=set()
        for year,rows in years.items():
            for row in rows:
                self.assertFalse(row["teacher_signoff"])
                self.assertTrue(row["proposed_not_official_pdp"])
                self.assertIn("buku teks m/s",row["note"])
                self.assertFalse(row["week"])
                self.assertFalse(row["a_start"])
                self.assertIn("Aktiviti guru:",row["note"])
                self.assertIn("Aktiviti murid:",row["note"])
                self.assertIn("PBD:",row["note"])
                for code in row["sp"].split(" / "):
                    self.assertNotIn((year,code),codes)
                    self.assertIn(code+" — ",row["sp_display"])
                    codes.add((year,code))
        self.assertEqual(len(codes),21)

    def test_three_pdf_are_landscape_and_contain_unapproved_draft(self):
        import fitz
        with TemporaryDirectory() as temp:
            files=build_all(Path(temp))
            self.assertEqual(len(files),3)
            for year,count,file in files:
                self.assertEqual(count,{4:4,5:4,6:2}[year])
                self.assertIn("CADANGAN_DRAF",file.name)
                with fitz.open(file) as doc:
                    self.assertGreaterEqual(doc.page_count,2)
                    self.assertTrue(all(p.rect.width>p.rect.height for p in doc))
                    text="\n".join(p.get_text() for p in doc)
                    self.assertIn("PDP CADANGAN",text.upper())
                    self.assertIn("AKTIVITI",text.upper())
                    self.assertFalse(any(chr(0) in p.get_text() for p in doc))

if __name__=="__main__":
    unittest.main()
