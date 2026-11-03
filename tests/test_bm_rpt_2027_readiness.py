"""Unit checks for BM 2027 staging. Does NOT enable runtime."""
import unittest
from tools.qa_bm_2027_readiness import COUNTS, audit


class BM2027GateTests(unittest.TestCase):
    def test_rpt_structural_consistency(self):
        out=audit("structure")
        self.assertTrue(out["passed"], "\n".join(out["errors"][:25]))
        self.assertEqual(sum(v["rpt"] for v in out["summary"].values()),825)
        self.assertEqual(sum(v["html"] for v in out["summary"].values()),825)
        self.assertEqual(sum(v["weeks"] for v in out["summary"].values()),220)

    def test_ready_is_blocked_until_every_requirement_is_verified(self):
        out=audit("ready")
        self.assertFalse(out["passed"])
        self.assertIn("Global READY status has not been approved",out["errors"])
        self.assertTrue(any("gate" in err for err in out["errors"]))

    def test_expected_rpt_counts(self):
        self.assertEqual(COUNTS,{2:164,3:165,4:165,5:166,6:165})


if __name__=="__main__":
    unittest.main()
