"""Sains Tahun 3 DSKP full-SP coverage QA; never treat SP as RPH count."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CROSSWALK=ROOT/"audits"/"sains_y3_dskp_sp_crosswalk_20261106.json"


class SainsYear3DSKPCrosswalkTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(CROSSWALK.read_text("utf-8"))

    def test_60_vs_45_are_codes_not_lesson_counts(self):
        d=self.data
        self.assertEqual(len(d["dskp_codes"]),60)
        self.assertEqual(len(set(d["dskp_codes"])),60)
        self.assertEqual(len(d["checkpoint_codes"]),45)
        self.assertEqual(len(set(d["checkpoint_codes"])),45)
        self.assertEqual(len(d["missing_codes"]),15)
        self.assertEqual(set(d["missing_codes"]),
                         set(d["dskp_codes"])-set(d["checkpoint_codes"]))
        self.assertEqual(d["counts"]["missing_content_related_sp"],3)
        self.assertEqual(d["status"],"DRAF_READONLY_NO_PRODUCTION_CHANGE")

    def test_content_gaps_require_source_page_evidence(self):
        d=self.data
        miss={r["sp"]:r for r in d["missing_content_sp_candidates"]}
        self.assertEqual(set(miss),{"3.2.5","3.3.3","3.3.4"})
        self.assertEqual(miss["3.2.5"]["textbook_printed_page_cues"],[41])
        self.assertEqual(miss["3.3.3"]["textbook_printed_page_cues"],[52])
        self.assertEqual(miss["3.3.4"]["textbook_printed_page_cues"],[51,54])
        for row in miss.values():
            self.assertTrue(row["evidence"])
            self.assertGreater(row["dskp_printed_page"],0)

    def test_kps_and_safety_are_not_assumed_missing_lessons(self):
        d=self.data
        process=d["missing_science_process_or_lab_sp"]
        self.assertEqual(len(process),12)
        self.assertEqual(set(process),
                         set(d["missing_codes"])-{"3.2.5","3.3.3","3.3.4"})
        self.assertTrue(all(c.startswith(("1.","2.")) for c in process))
        self.assertIn("NOT automatically",d["interpretation"])


if __name__=="__main__":
    unittest.main()
