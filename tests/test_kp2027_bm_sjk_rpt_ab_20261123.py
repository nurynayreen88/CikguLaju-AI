"""2027 A/B RPT skeleton alignment with no invented lesson dates or hours."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "audits/kp2027_bm_sjk_rpt_2027_ab_calendar_unallocated_20261123.json"
DRAFT = ROOT / "audits/kp2027_bm_sjk_tahun1_52_rph_editorial_qa_20261123.json"


class RPTCalendarGuard(unittest.TestCase):
    def test_groups_and_source_integrity(self):
        a = json.loads(CAL.read_text(encoding="utf-8"))
        b = json.loads(DRAFT.read_text(encoding="utf-8"))
        self.assertEqual(a["status"], "QA_HOLD_RPT_ANNUAL_NOT_COMPLETE")
        self.assertFalse(a["publishable"])
        self.assertEqual(a["ready_rph"], 0)
        self.assertEqual(set(a["groups"]), {"A","B"})
        self.assertEqual(a["owner_target"]["last_curricular_pdp_on_or_before"],
                         "2027-11-05")
        self.assertIn("moe.gov.my", a["calendar_reference"]["official_page"])
        expected = [r["proposed_pdp"] for r in b["records"]]
        self.assertEqual(expected, list(range(1, 53)))
        for grp in ("A","B"):
            g = a["groups"][grp]
            self.assertEqual(g["mula"],"2027-01-04")
            self.assertEqual(g["akhir"],
                             "2027-12-02" if grp=="A" else "2027-12-03")
            self.assertEqual(g["jumlah_hari_persekolahan"],201 if grp=="A" else 203)
            self.assertEqual(len(g["segmen"]),4)
            self.assertEqual(len(g["cuti_penggal"]),3)
            self.assertEqual(len(g["pdp_cadangan"]),52)
            self.assertEqual([r["pdp_cadangan"] for r in g["pdp_cadangan"]],expected)
            self.assertEqual([r["sk"] for r in g["pdp_cadangan"]],
                             [r["sk_code"] for r in b["records"]])
            self.assertEqual([r["sp"] for r in g["pdp_cadangan"]],
                             [r["sp_code"] for r in b["records"]])
            self.assertTrue(all(r["tarikh"] is None and r["masa"] is None and
                                r["kelas"] is None and
                                r["semakan_pedagogi"]=="QA_HOLD_NOT_READY"
                                for r in g["pdp_cadangan"]))
            for lo,hi in g["segmen"]:
                self.assertLessEqual(lo,hi)
                self.assertTrue(lo.startswith("2027-"))
                self.assertTrue(hi.startswith("2027-"))
        self.assertNotIn('"minggu"', CAL.read_text(encoding="utf-8"))


if __name__=="__main__":
    unittest.main()
