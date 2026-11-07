"""Regression of 3 source multi-SP Science Year3 original non-BA PBD sheets."""
import unittest

from tools.render_sains_y3_3_secondary_sp_pbd_20261107 import (
    TASKS, ORDER, verify_source, stem
)
from tools.sains_buku_aktiviti_mapping_20261107 import load_activity_books

class TestYear3SecondarySPPBD(unittest.TestCase):
    def test_exact_three_secondary_kpm_sp_and_primary_ba(self):
        self.assertTrue(verify_source())
        self.assertEqual(ORDER,("3.2.5","3.3.3","3.3.4"))
        self.assertEqual([TASKS[x]["pdp"] for x in ORDER],
                         ["SCI-Y3-PDP-006","SCI-Y3-PDP-010","SCI-Y3-PDP-011"])
        y3=load_activity_books()[3]
        for sp in ORDER:
            t=TASKS[sp]
            self.assertEqual(t["primary"],y3[t["pdp"]]["sp"])
            self.assertNotEqual(t["primary"],sp)
            self.assertIn(sp.replace(".","_"),stem(sp))
            self.assertTrue(all(t[f"a{i}"] for i in range(1,4)))
            self.assertEqual(len(t["criteria"]),3)

    def test_specific_untaught_bio_sp_evidence(self):
        self.assertIn("kelas makanan",TASKS["3.2.5"]["sp_text"].lower())
        self.assertIn("makanan tercerna yang tidak diperlukan",TASKS["3.3.3"]["sp_text"].lower())
        self.assertIn("pencernaan",TASKS["3.3.4"]["sp_text"].lower())
        self.assertIn("dubur",TASKS["3.3.3"]["a3"].lower()+
                          " ".join(TASKS["3.3.3"]["criteria"]).lower())
        self.assertIn("lisan",TASKS["3.2.5"]["a3"])
        self.assertIn("lisan",TASKS["3.3.4"]["a3"])

    def test_no_false_grade_or_medical_exposure(self):
        for t in TASKS.values():
            self.assertIn("peribadi",t["safety"])
            self.assertTrue(t["prep"])
            self.assertTrue(t["criteria"])

if __name__=="__main__":
    unittest.main()
