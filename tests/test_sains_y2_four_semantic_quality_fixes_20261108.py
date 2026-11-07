"""Source-grounded Year2 four-PdP semantic and safety regression.

Uses official owner DSKP Year2 wording for SP 4.1.3, 8.1.4, 9.1.4, 9.2.1.
Checking editorial source quality is not a teacher/panitia approval.
"""
from __future__ import annotations

import unittest

from web.sains_y2_51_activities_draf_20261107 import BANK
from web.sains_rph_quality_release_gate_20261108 import approved_count


class Year2FourSourceContentRepairs(unittest.TestCase):
    def test_51_source_sp_bank_stays_unique_no_academic_ready(self):
        self.assertEqual(len(BANK),51)
        self.assertEqual(len({row["hook"] for row in BANK.values()}),51)
        self.assertEqual(approved_count(),0)

    def test_413_frog_egg_habitat_scientifically_distinct_from_hen_nest(self):
        case=BANK["4.1.3"]
        self.assertIn("ayam di sarang",case["hook"])
        self.assertIn("telur katak di air",case["hook"])
        self.assertIn("banyak dan sedikit",case["pbd"])
        self.assertIn("jangan reka bilangan tepat",case["safety"])

    def test_814_controls_variables_and_uses_two_actual_comparisons(self):
        case=BANK["8.1.4"]
        for keyword in ("saiz gula berbeza","gula saiz sama","dikacau atau tidak"):
            self.assertIn(keyword,case["teacher1"])
        for keyword in ("satu faktor setiap kali","jisim gula","isipadu air","suhu"):
            self.assertIn(keyword,case["teacher2"])
        self.assertIn("masa pelarutan",case["pupil2"])
        self.assertIn("dua ujian terkawal",case["pbd"])
        self.assertIn("jangan",case["safety"].lower())

    def test_914_canonical_water_cycle_no_wrong_awam_word(self):
        case=BANK["9.1.4"]
        self.assertNotIn("awam",case["hook"].lower())
        for keyword in ("laut","wap air","awan","hujan","sungai"):
            self.assertIn(keyword,case["hook"].lower())
            self.assertIn(keyword,case["materials"].lower())
            self.assertIn(keyword,case["pbd"].lower())
        self.assertIn("menyusun lima kad",case["pupil1"])
        self.assertIn("jangan guna pemanasan",case["safety"].lower())

    def test_921_air_existence_without_mouth_or_shared_bag(self):
        case=BANK["9.2.1"]
        self.assertIn("dikibas",case["teacher1"])
        self.assertIn("tanpa menggunakan mulut",case["teacher1"])
        self.assertIn("jangan menyarung beg pada kepala",case["safety"].lower())
        self.assertIn("dua bukti",case["pbd"].lower())
        self.assertNotIn("ditiup",case["teacher1"].lower())


if __name__=="__main__":
    unittest.main()
