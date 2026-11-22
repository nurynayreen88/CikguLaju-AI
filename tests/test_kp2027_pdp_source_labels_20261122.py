"""Source-pinned Unit → PdP metadata; private approval list stays authoritative."""
import json
from pathlib import Path
import unittest
from web.kp2027_pdp_catalog import math_approved_items, alam_approved_items
from web import kp2027_math_canary_web as math, kp2027_alam_private_web as alam


class Kp2027PdpHierarchy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.labels = json.loads((Path(__file__).resolve().parents[1] /
            "web/kp2027_pdp_source_labels_v1.json").read_text(encoding="utf-8"))

    def test_source_metadata_has_real_pdf_provenance_and_exact_sp_coverage(self):
        self.assertEqual(self.labels["version"], 1)
        self.assertEqual(self.labels["source_pdf_sha256"]["MATH"],
                         "9fb7007dc8b22027dcc0d2dea4466a8fc1ac7fa8ba4c1fa2c88825a4eb9a5dde")
        self.assertEqual(self.labels["source_pdf_sha256"]["ALAM"],
                         "d0c3dfc7c2e92cc9963b3d6b9a4f66222fc7ecc46397d768c0d43c746c14d3ba")
        self.assertEqual(len(self.labels["sp_labels"]["MATH"]), 30)
        self.assertEqual(len(self.labels["sp_labels"]["ALAM"]), 64)
        self.assertEqual(len({x["unit"] for x in self.labels["sp_labels"]["MATH"].values()}),24)
        self.assertEqual(len({x["unit"] for x in self.labels["sp_labels"]["ALAM"].values()}),8)
        all_math = {math.expected_entry(group,n)["sp"]
                    for group,total in (("A",125),("B",124)) for n in range(1,total+1)}
        all_alam = {alam.expected_entry(n)["sp"] for n in range(1,65)}
        self.assertEqual(all_math, set(self.labels["sp_labels"]["MATH"]))
        self.assertEqual(all_alam, set(self.labels["sp_labels"]["ALAM"]))

    def test_every_math_pdp_in_both_groups_has_real_unit_and_title(self):
        groups = {"A": list(range(1,126)), "B": list(range(1,125))}
        items = math_approved_items(groups, math._CATALOG)
        self.assertEqual([len(items[k]) for k in ("A","B")],[125,124])
        self.assertEqual(items["A"][0]["unit"],"Nombor Bulat hingga 100 — Nilai Nombor")
        self.assertEqual(items["A"][0]["tajuk"],"Kenal Nombor")
        self.assertEqual(items["A"][-1]["tajuk"],"Menyelesaikan Masalah Data Harian")
        self.assertEqual(items["B"][-1]["no"],124)
        self.assertNotEqual(items["A"][31]["sp"],items["B"][31]["sp"])
        self.assertNotEqual(items["A"][31]["tajuk"],items["B"][31]["tajuk"])
        for group in ("A","B"):
            for item in items[group]:
                self.assertTrue(item["unit"] and item["tajuk"] and item["sp"])
                self.assertTrue(item["tajuk"][0].isupper())

    def test_alam_maps_all_64_to_exact_eight_source_units(self):
        items=alam_approved_items(list(range(1,65)),alam.CATALOG["items"])
        self.assertEqual(len(items),64)
        self.assertEqual(items[0]["tajuk"],"Anggota Badan Saya")
        self.assertEqual(items[37]["unit"],"Inspirasi Alam")
        self.assertEqual(items[37]["tajuk"],"Kehendak Berbeza daripada Keperluan")
        self.assertEqual(items[-1]["unit"],"Pentas Adiwira")
        self.assertEqual(items[-1]["tajuk"],"Pentas Adiwira Cilik")

    def test_only_approved_subset_is_shown_no_extra_pdp(self):
        approved=math_approved_items({"A":[1,11,125],"B":[1,124]},math._CATALOG)
        self.assertEqual([p["no"] for p in approved["A"]],[1,11,125])
        self.assertEqual([p["no"] for p in approved["B"]],[1,124])
        self.assertEqual([p["no"] for p in alam_approved_items([1,2,38],alam.CATALOG["items"])],
                         [1,2,38])
        for invalid in ({"A":[1,1],"B":[]},{"A":[126],"B":[]},{"A":[],"B":[125]},
                        {"A":[],"B":[],"Z":[1]}):
            with self.subTest(groups=invalid),self.assertRaises(ValueError):
                math_approved_items(invalid,math._CATALOG)
        for invalid in ([65],[1,1],[0]):
            with self.subTest(numbers=invalid),self.assertRaises(ValueError):
                alam_approved_items(invalid,alam.CATALOG["items"])


if __name__=="__main__":
    unittest.main()
