"""Non-destructive Alam Tahun 1 KP2027 RPT-to-RPH source audit gate."""
import json
from collections import Counter
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDIT = json.loads((ROOT / "audits/kp2027_alam_t1_rpt93_source64_83sp_qa29_20261122.json").read_text("utf-8"))
CATALOG = json.loads((ROOT / "web/kp2027_alam_v10_catalog.json").read_text("utf-8"))


class AlamRPTSourceMappingQA(unittest.TestCase):
    def test_rpt_count_and_source_coverage(self):
        self.assertEqual(AUDIT["status"], "ACADEMIC_QA_ONLY_DO_NOT_PUBLISH")
        self.assertEqual(len(AUDIT["mappings"]), 93)
        self.assertEqual([m["rpt_pdp"] for m in AUDIT["mappings"]], list(range(1, 94)))
        self.assertEqual(len(set(m["sp"] for m in AUDIT["mappings"])), 83)
        self.assertEqual(len(CATALOG["items"]), 64)
        source_codes = {code for item in CATALOG["items"].values() for code in item["codes"]}
        self.assertEqual(len(source_codes), 83)
        self.assertEqual(source_codes, {m["sp"] for m in AUDIT["mappings"]})
        self.assertEqual(sum(len(item["codes"]) == 2 for item in CATALOG["items"].values()), 19)

    def test_exact_source_mapping_and_no_assumed_publication(self):
        status = Counter()
        source_ids = []
        qa_ids = []
        for m in AUDIT["mappings"]:
            src = m["source_rph"]
            self.assertIn(str(src), CATALOG["items"])
            item = CATALOG["items"][str(src)]
            self.assertIn(m["sp"], item["codes"])
            self.assertEqual(m["source_codes"], item["codes"])
            self.assertRegex(m["week_a"], r"^M[0-9]{2}$")
            self.assertRegex(m["week_b"], r"^M[0-9]{2}$")
            status[m["mapping_reason"]] += 1
            if m["mapping_reason"] == "existing_source":
                self.assertEqual(m["sp"], item["sp"])
                self.assertEqual(m["output_status"], "APPROVED_SOURCE")
                self.assertIsNone(m["draft_qa_rph"])
                source_ids.append(src)
            else:
                self.assertEqual(m["output_status"], "QA_ONLY_NOT_PUBLISHED")
                self.assertEqual(m["draft_qa_rph"], m["rpt_pdp"])
                qa_ids.append(m["rpt_pdp"])
                if m["mapping_reason"] == "qa_split":
                    self.assertNotEqual(m["sp"], item["sp"])
                elif m["mapping_reason"] == "qa_reinforcement":
                    self.assertEqual(m["sp"], item["sp"])
        self.assertEqual(status, Counter({"existing_source": 64, "qa_split": 20, "qa_reinforcement": 9}))
        self.assertEqual(sorted(source_ids), list(range(1, 65)))
        self.assertEqual(qa_ids, [2,5,10,11,16,20,21,26,29,32,36,39,41,45,48,50,55,57,60,65,67,70,74,76,79,83,85,88,92])

    def test_catalog_readonly_source_and_no_web_release_side_effect(self):
        self.assertEqual(AUDIT["checks"]["missing_sp_count"], 0)
        self.assertEqual(AUDIT["checks"]["qa_candidate_count"], 29)
        self.assertTrue(AUDIT["qa_zip_drive_id"])
        self.assertTrue(AUDIT["mapping_sheet_drive_id"])
        # This test intentionally reads audit files only; it does not mutate assets,
        # curriculum content, Supabase, quota, payment or runtime download routes.


if __name__ == "__main__":
    unittest.main()
