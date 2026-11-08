"""Ensure primary PDF DSKP conflict audit never gives automatic RPH approval."""
import unittest

from tools.audit_matematik_v60_dskp_primary_20261108 import audit_dskp_primary


class PrimaryDSKPSourceAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit_dskp_primary()

    def test_reference_pdf_codes_and_year2_printing_normalization(self):
        counts = {int(year): item["dskp_distinct_sp_codes"]
                  for year, item in self.report["years"].items()}
        self.assertEqual(counts, {2: 70, 3: 102, 4: 85, 5: 72, 6: 38})
        self.assertEqual(self.report["years"]["2"]["native_absent_codes"], [])

    def test_found_actual_canonical_conflicts_not_inferred_from_weeks(self):
        counts = {int(year): item["native_pdp_requiring_review"]
                  for year, item in self.report["years"].items()}
        self.assertEqual(counts, {2: 0, 3: 0, 4: 11, 5: 25, 6: 62})
        self.assertEqual(self.report["affected_native_pdp_total"], 98)
        self.assertEqual(self.report["distinct_absent_code_year_pairs"], 65)

    def test_v60_code_inventory_matches_every_reference_dskp(self):
        self.assertTrue(all(not row["v60_absent_codes"]
                            for row in self.report["years"].values()))

    def test_year6_legacy_code_not_mistaken_for_official_sp(self):
        y6 = self.report["years"]["6"]
        self.assertIn("1.5.1", y6["native_absent_codes"])
        self.assertNotIn("1.2.1", y6["native_absent_codes"])
        self.assertEqual(y6["dskp_distinct_sp_codes"], 38)

    def test_semantic_mismatch_even_when_sp_exists_in_primary_dskp(self):
        self.assertEqual(self.report["known_semantic_conflict_count"], 2)
        self.assertEqual(self.report["known_distinct_pdp_requiring_review_minimum"], 100)
        cases = {x["pdp_code"]: x
                 for x in self.report["code_present_but_semantically_conflicting_known_cases"]}
        self.assertEqual(set(cases), {"MT6-PDP-004", "MT6-PDP-006"})
        self.assertEqual(cases["MT6-PDP-004"]["native_title"], "Pembundaran Nombor")
        self.assertIsNone(cases["MT6-PDP-004"]["candidate_sp"])
        self.assertEqual(cases["MT6-PDP-006"]["native_title"], "Pola Nombor")
        self.assertEqual(cases["MT6-PDP-006"]["candidate_sp"], "1.1.2")
        self.assertTrue(all(x["approved"] is False for x in cases.values()))

    def test_all_conflicts_remain_unapproved_and_no_production_changes(self):
        self.assertFalse(self.report["academic_signoff"])
        self.assertFalse(self.report["runtime_e2e_passed"])
        self.assertFalse(self.report["production_modified"])
        self.assertEqual(self.report["release_decision"], "HOLD")
        self.assertEqual(len(self.report["affected_pdp"]), 98)
        self.assertTrue(all(row["approved"] is False
                            for row in self.report["affected_pdp"]))


if __name__ == "__main__":
    unittest.main()
