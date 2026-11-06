"""Read-only canonical Science Unit menu checks over real v25.82 source."""
import unittest
import tempfile
from pathlib import Path
from tools.audit_sains_25_82_delta_20261106 import load,SOURCES,ROOT
from web.sains_canonical_unit_preview_20261106 import (
    canonical_science_year,ScienceUnitSourceConflict,
)

class ScienceUnitPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.rows=load(SOURCES["v25.82"],ROOT,Path(cls.tmp.name))
    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
    def test_each_textbook_unit_once_all_years_2_6(self):
        expected={2:(51,8),3:(45,8),4:(79,9),5:(83,9),6:(84,12)}
        for year,(pdp_count,unit_count) in expected.items():
            with self.subTest(year=year):
                orig=[r for r in self.rows if r.get("year_label")==f"Tahun {year}"]
                after,units=canonical_science_year(orig,year,2027)
                self.assertEqual(len(after),pdp_count)
                self.assertEqual(len(units),unit_count)
                self.assertEqual(len({x[1] for x in units}),unit_count)
                self.assertEqual({r["pdp_sequence_code"] for r in orig},
                                 {r["pdp_sequence_code"] for r in after})
                self.assertEqual([(r["sk_code"],r["sp_code"],r["pdp_title"])
                                  for r in orig],
                                 [(r["sk_code"],r["sp_code"],r["pdp_title"])
                                  for r in after])
                self.assertEqual(
                    sorted({r["unit_title"] for r in after}),
                    sorted({u[1] for u in units}))
                self.assertEqual(
                    len({(r["unit_title"],r["pdp_sequence_code"]) for r in after}),
                    pdp_count)
                self.assertTrue(all(u[1].startswith("Unit ") for u in units))
                self.assertTrue(all(r["unit_code"]=="" for r in after))
                self.assertTrue(all(
                    r["_raw_unit_title_audit"]==original["unit_title"]
                    for r,original in zip(after,orig)))
    def test_y3_unit_three_contains_all_subtopics(self):
        orig=[r for r in self.rows if r.get("year_label")=="Tahun 3"]
        after,units=canonical_science_year(orig,3,2027)
        self.assertIn(("","Unit 3: Manusia"),units)
        items=[r for r in after if r["unit_title"]=="Unit 3: Manusia"]
        self.assertEqual({r["sk_code"] for r in items},{"3.1","3.2","3.3"})
    def test_y6_unit_12_does_not_use_overbroad_theme(self):
        orig=[r for r in self.rows if r.get("year_label")=="Tahun 6"]
        _,units=canonical_science_year(orig,6,2027)
        self.assertIn(("","Unit 12: Kestabilan dan Kekuatan"),units)
        self.assertNotIn(("","Unit 12: Teknologi dan Kehidupan Lestari"),units)
    def test_kp2027_year1_cannot_leak_legacy_sains(self):
        orig=[r for r in self.rows if r.get("year_label")=="Tahun 1"]
        with self.assertRaises(ScienceUnitSourceConflict):
            canonical_science_year(orig,1,2027)
    def test_mixed_subject_and_invalid_sk_fail_closed(self):
        orig=[r for r in self.rows if r.get("year_label")=="Tahun 2"]
        with self.assertRaises(ScienceUnitSourceConflict):
            canonical_science_year([{**orig[0],"subject":"Matematik"}],2,2027)
        with self.assertRaises(ScienceUnitSourceConflict):
            canonical_science_year([{**orig[0],"sk_code":"not verified"}],2,2027)

if __name__=="__main__":unittest.main()
