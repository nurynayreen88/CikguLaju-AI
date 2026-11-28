"""Freeze historical Sains 342-source coverage evidence, not official KPM syllabus."""
import unittest

from scripts.audit_rpt2027_sains_342_missing_front_units_20261110 import coverage_report
from scripts.build_rpt_2027_sains_342_actual_source_staging import source_records


class Sains342FrontUnitCoverage(unittest.TestCase):
    def test_early_unit_source_gaps_and_no_false_academic_signoff(self):
        result = coverage_report()
        self.assertFalse(result["release_ready"])
        expected = {2: [1, 2], 3: [1, 2], 4: [1], 5: [1], 6: [1]}
        counts = {2: 51, 3: 45, 4: 79, 5: 83, 6: 84}
        self.assertEqual(result["scope"], "342 historical Sains PdP staging candidate ONLY")
        for year in range(2, 7):
            with self.subTest(year=year):
                item = result["years"][str(year)]
                self.assertEqual(item["early_unit_labels_absent_from_342_source"], expected[year])
                self.assertEqual(item["first_unit"], max(expected[year]) + 1)
                self.assertEqual(item["first_source_pdp"], "001")
                self.assertEqual(item["pdp_count"], counts[year])
                self.assertEqual(item["source_m01_pdp_count"], 2)
                self.assertFalse(item["academic_release_ready"])
                self.assertEqual(item["unverified_source_pdp_count"], counts[year])
        self.assertEqual(sum(v["pdp_count"] for v in result["years"].values()), 342)
        self.assertTrue(result["year1_transition_unchanged"])

    def test_original_sains_records_remain_unmodified_by_read_only_audit(self):
        before = source_records()
        coverage_report()
        after = source_records()
        self.assertEqual(before, after)
        self.assertFalse(any(row.get("academic_release_approved")
                             for rows in after.values() for row in rows))


if __name__ == "__main__":
    unittest.main()
