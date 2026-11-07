"""CI for 80 sourced, not-yet-assigned Sains 2027 DSKP SP appendix."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.audit_sains_rpt2027_uncovered_verified_sp_staging import audit_coverage
from scripts.build_rpt2027_sains_80_sp_gap_appendix_staging import supplementary_sains_rows, build_all, EXPECTED

class Sains80SPAppendixTests(unittest.TestCase):
    def test_all_80_official_sp_visible_without_invented_lesson(self):
        info=audit_coverage()
        covered=set()
        for year,(n,kps,topic) in EXPECTED.items():
            rows=supplementary_sains_rows(year,info)
            self.assertEqual(len(rows),n)
            self.assertEqual(sum(r["gap_kind"]=="KPS/MANIPULATIF" for r in rows),kps)
            self.assertEqual(sum(r["gap_kind"]=="KANDUNGAN TOPIK" for r in rows),topic)
            self.assertEqual(len({r["sp"] for r in rows}),n)
            for row in rows:
                self.assertIn(" — ",row["sp_display"])
                self.assertIn(" — ",row["sk_display"])
                self.assertFalse(row["assigned_to_existing_pdp"])
                self.assertFalse(row["academic_signoff"])
                self.assertFalse(row.get("week"))
                self.assertFalse(row.get("a_start"))
                self.assertFalse(row.get("b_start"))
                self.assertIn("RUJUKAN DB LEGACY",row["note"])
                covered.add((year,row["sp"]))
        self.assertEqual(len(covered),80)

    def test_three_review_pdfs_are_real_landscape_and_not_marked_ready(self):
        import fitz
        with TemporaryDirectory() as tmp:
            files=build_all(Path(tmp))
            self.assertEqual(len(files),3)
            for year,rows,path in files:
                self.assertEqual(len(rows),EXPECTED[year][0])
                self.assertIn("LAMPIRAN_DRAF",path.name)
                with fitz.open(path) as doc:
                    self.assertGreaterEqual(doc.page_count,2)
                    self.assertTrue(all(p.rect.width>p.rect.height for p in doc))
                    body="\n".join(p.get_text() for p in doc)
                    self.assertIn("RANCANGAN PENGAJARAN TAHUNAN 2027",body)
                    self.assertIn("BELUM",body.upper())
                    self.assertFalse(any(chr(0) in p.get_text() for p in doc))

if __name__=="__main__":
    unittest.main()
