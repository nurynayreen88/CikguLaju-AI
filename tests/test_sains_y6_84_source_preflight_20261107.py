"""Read-only regression checks of Science Year6 84-SP staging preflight."""
import copy
import unittest

from tools.audit_sains_342_pdp_release_gate_20261106 import analyze
from tools.audit_sains_y6_84_source_preflight_20261107 import (
    GROUPS, EXPECTED_SP, RISK_NOTES, preflight,
)

class TestYear6Preflight(unittest.TestCase):
    def test_exact_84_2021_dskp_code_inventory(self):
        rows,_=analyze()
        report=preflight(rows)
        self.assertEqual(len(report),84)
        self.assertEqual(len(EXPECTED_SP),84)
        self.assertEqual(sum(GROUPS.values()),84)
        self.assertEqual(report[0]["pdp_code"],"SCI-Y6-PDP-001")
        self.assertEqual(report[-1]["pdp_code"],"SCI-Y6-PDP-084")
        self.assertTrue(all(x["release_decision"]=="HOLD" for x in report))
        self.assertTrue(all(x["academic_quality_percent"]=="" for x in report))

    def test_no_false_ready_or_wrong_code(self):
        original,_=analyze()
        items=copy.deepcopy(original)
        first=next(x for x in items if x["tahun"]==6)
        first["keputusan"]="READY"
        with self.assertRaises(ValueError):
            preflight(items)
        first["keputusan"]="HOLD"
        first["sp"]="2.1.2"
        with self.assertRaises(ValueError):
            preflight(items)

    def test_safety_critical_units_flagged(self):
        self.assertIn("kultur",RISK_NOTES["3.1"].lower())
        self.assertIn("makanan",RISK_NOTES["8.2"].lower())
        self.assertIn("matahari",RISK_NOTES["10.1"].lower())
        self.assertIn("pembiakan",RISK_NOTES["2.1"].lower())

if __name__=="__main__":
    unittest.main()
