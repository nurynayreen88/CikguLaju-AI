"""RBT 2026 sourced week-block labels are optional notes, not 2027 dates."""
import unittest
from scripts.build_rpt_2027_standard_preview import rbt_records

class RBTSourcedWeekNoteQA(unittest.TestCase):
    def test_rpt2026_sp_examples_are_annotated_without_fake_2027_dates(self):
        match_counts={}
        for year in (4,5,6):
            rows=rbt_records(year)
            matches=[r for r in rows if r.get("source_2026_sp_matched")]
            match_counts[year]=len(matches)
            self.assertEqual(len(rows),32)
            for r in rows:
                self.assertEqual(r["week"],"")
                for field in ("a_start","a_end","b_start","b_end"):
                    self.assertFalse(r[field])
                self.assertNotIn("Jadual RBT 2027 telah disahkan",r["note"])
            for r in matches:
                self.assertIn("Rujukan RPT 2026",r["note"])
                self.assertIn("BUKAN minggu/tarikh 2027",r["note"])
                self.assertFalse(r["rbt_2027_week_signoff"])
                self.assertTrue(r["source_2026_rpt_week_blocks"])
        for year in (4,5,6):
            self.assertGreater(match_counts[year],0, f"T{year}: SP source block not applied")
        
if __name__=="__main__":
    unittest.main()
