"""Aquatic V2 source regression; no live routing or calendar changes."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"rph_standalone/pjpk/akuatik_v2_darat_t1_t6_20261124.json"
MANIFEST=ROOT/"rpt_2027/pjpk/pjpk_2027_rpt_manifest.json"

class AquaticV2Source(unittest.TestCase):
    def setUp(self):
        self.root=json.loads(SOURCE.read_text(encoding="utf-8"))
        self.records=self.root["records"]

    def test_all_years_distinct_and_not_published(self):
        self.assertEqual(self.root["status"],"QA_NOT_PUBLISHED")
        self.assertEqual(len(self.records),18)
        self.assertEqual(len({(r["year"],r["source_id"]) for r in self.records}),18)
        self.assertEqual([sum(r["year"]==y for r in self.records) for y in range(1,7)],[2,4,2,2,5,3])
        for r in self.records:
            self.assertFalse(r["ready"])
            self.assertEqual(r["variant"],"V2_DARAT")
            self.assertEqual(set(r["metadata"].values()),{""})
            self.assertTrue(all(r[k] for k in ("objective","criteria","induction","bbm","safety","pbd","closure","remedial","extension","reflection")))
            self.assertEqual(len(r["activities"]),3)
            self.assertTrue(all(a["title"] and a["body"] for a in r["activities"]))
            self.assertIn(r["criteria"],r["pbd"])
            self.assertIn("Kemahiran psikomotor di air belum ditaksir",r["pbd"])
            self.assertIn("Kemahiran dalam air belum ditaksir",r["reflection"])
            self.assertIn("Tiada kolam, rendaman, tahan nafas",r["safety"])
            self.assertIn("Aktiviti Darat",r["title"])

    def test_numbered_kssr_original_standards_unchanged(self):
        rows=json.loads(MANIFEST.read_text(encoding="utf-8"))["records"]
        for r in self.records:
            if r["year"] not in (3,4):
                continue
            original=next(x for x in rows if x["subject"]=="PJ" and x["year"]==r["year"] and x["pdp"]==int(r["source_id"]))
            s=r["source_standard_reference"]
            self.assertEqual(set(s["psychomotor"]+s["cognitive"]+s["affective"]),set(original["sp"]))
            self.assertEqual(set(s["sk"]),set(original["sk"]))
        for r in self.records:
            if r["year"] in (2,5,6):
                self.assertEqual(r["status"],"QA_SUPPLEMENT_NO_RPT_SLOT")
                self.assertFalse(r["source_id"].isdigit())

if __name__=="__main__":
    unittest.main()
