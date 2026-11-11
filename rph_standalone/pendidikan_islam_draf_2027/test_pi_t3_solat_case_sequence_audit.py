"""No overlap of 18 numbered solat cases across 3 Year3 PdPs."""
import unittest
from pi_t3_solat_case_sequence_audit import audit


class PIT3SolatSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=audit()

    def test_correct_range_progression_without_inventing_fiqh(self):
        r=self.report
        self.assertTrue(r["t3_pdp_051_055_059_ranges_sequential"])
        self.assertEqual(r["listed_case_numbers_covered_once"],18)
        self.assertEqual([(x["range_start"],x["range_end"]) for x in r["rows"]],
                         [(1,6),(7,12),(13,18)])
        self.assertTrue(r["catalog_year3_l059_objective_repaired"])
        self.assertFalse(r["rpt_2027_source_modified"])
        self.assertFalse(r["expert_fiqh_approved"])
        self.assertEqual(r["teacher_ready"],0)
        self.assertEqual(r["release"],"NO_GO")


if __name__=="__main__":
    unittest.main()
