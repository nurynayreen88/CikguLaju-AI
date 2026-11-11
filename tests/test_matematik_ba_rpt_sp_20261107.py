"""Staging index review for RPT/SP evidence, not final RPH verification."""
import csv
from pathlib import Path
from collections import Counter
import unittest

BASE = Path(__file__).resolve().parents[1] / "audits"


def rows(name):
    with (BASE / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class RptSpCrosswalkTests(unittest.TestCase):
    def test_585_v28_reference_lessons(self):
        records = rows("matematik_ba_v28_rpt_585_sp_index_20261107.csv")
        self.assertEqual(len(records), 585)
        self.assertEqual(Counter(x["year"] for x in records),
                         {str(y): 117 for y in range(2, 7)})
        self.assertEqual(len(set(x["v28_lesson_id"] for x in records)), 585)
        self.assertTrue(all(x["rpt_sp_codes"] for x in records))
        self.assertTrue(all(
            x["v41_semantic_match_status"] == "NOT_VERIFIED_AGAINST_V41_RPH"
            for x in records))

    def test_72_legacy_crosswalks_are_unapproved(self):
        records = rows("matematik_ba_t2_v27_to_v28_sp_candidates_20261107.csv")
        self.assertEqual(len(records), 72)
        self.assertTrue(all(x["mapping_status"] != "APPROVED" for x in records))
        self.assertTrue(all(x["legacy_t2_v27_rph_id"] for x in records))
        for x in records:
            ids = [i for i in x["candidate_v28_lesson_ids_by_sp"].split(";") if i]
            self.assertEqual(len(ids), int(x["candidate_count"]))
            self.assertTrue(all(i.startswith("T2-L") for i in ids))


if __name__ == "__main__":
    unittest.main()
