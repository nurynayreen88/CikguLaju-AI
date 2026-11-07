"""Read-only Sains DSKP coverage gap result: tests never call unsafe runtime."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"staging/rpt_2027_seragam_2026/sains_verified_sp_coverage_gap_20261107_DRAF.json"

class SainsRPT2027VerifiedSPGapQA(unittest.TestCase):
    def test_report_contains_only_source_verified_uncovered_standard_inventory(self):
        self.assertTrue(REPORT.exists(),"Run staging Sains SP audit before this test")
        r=json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(r["status"],"STAGING_ONLY_UNCOVERED_STANDARDS_NOT_PLANNED_LESSONS")
        self.assertTrue(r["read_only"])
        self.assertFalse(r["full_2027_rpt_ready"])
        self.assertTrue(r["no_runtime_changes"])
        counts=r["counts"]
        self.assertEqual(counts["historical_source_pdp"],342)
        self.assertEqual(counts["verified_unique_dskp_sp_year2to6"],422)
        self.assertIs(counts["uncovered_is_a_pdp_count"],False)
        self.assertGreaterEqual(counts["uncovered_unique_sp_in_historical_pdp"],80)
        self.assertEqual(set(r["years"]),set(map(str,range(2,7))))
        covered=0;uncovered=0
        for year,scope in r["years"].items():
            n=scope["distinct_sp_not_seen_in_pdp"]
            self.assertEqual(n,len(scope["missing_verified_standards_NOT_PDP"]))
            self.assertEqual(scope["available_distinct_sp"],
                             scope["pdp_distinct_sp_covered"]+n)
            self.assertEqual(scope["sourced_pdp_count"],
                             scope["pdp_distinct_sp_covered"]+scope["repeated_sp_slots_in_pdp"])
            codes=set()
            for item in scope["missing_verified_standards_NOT_PDP"]:
                code=item["sp_code"]
                self.assertNotIn(code,codes)
                codes.add(code)
                self.assertIn(item["source"],("VERIFIED_V26_00_CURRICULUM_STANDARDS",
                                              "KPM_DSKP_ORIGINAL_SUPPLEMENTAL_PDF"))
                self.assertGreater(len(item["sp_text"]),8)
                self.assertGreaterEqual(len(item["sk_text"]),5)
            covered+=scope["pdp_distinct_sp_covered"]
            uncovered+=n
        self.assertEqual(uncovered,counts["uncovered_unique_sp_in_historical_pdp"])
        self.assertEqual(covered+uncovered,422)

if __name__=="__main__":
    unittest.main()
