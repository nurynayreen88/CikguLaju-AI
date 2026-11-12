"""RBT 2026 week-block source evidence: never auto-approve 2027 dates.

Published 2026 RPT groups several SP into one multi-week block.
Codes are checked against sourced DSKP and draft 2027 records remain blank.
"""
import json
import re
import unittest
from collections import defaultdict
from pathlib import Path
from scripts.build_rpt_2027_standard_preview import rbt_records

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "audits/rbt_t4_t6_rpt2026_23_sp_week_block_source_evidence_20261107.json"
CROSSWALK = ROOT / "rpt_2027/rbt"

class RBTPublished2026WeekBlockSourceQA(unittest.TestCase):
    def test_seven_sourced_groups_all_23_standard_codes_belong_to_original_dskp(self):
        data = json.loads(LEDGER.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "SOURCE_2026_WEEK_BLOCK_EVIDENCE_ONLY_NOT_2027_SCHEDULE")
        self.assertEqual(data["group_count"], 7)
        self.assertEqual(data["listed_year_sp_codes"], 23)
        self.assertEqual(data["production_changes"], 0)
        self.assertEqual(len(data["records"]), 7)
        buckets = defaultdict(set)
        for group in data["records"]:
            year = group["year"]
            self.assertIn(year, (4, 5, 6))
            self.assertTrue(1 <= group["start_week_2026"] <= group["end_week_2026"] <= 44)
            self.assertIn("/basic", group["source_url"])
            self.assertEqual(len(group["sp_codes"]), len(set(group["sp_codes"])))
            self.assertTrue(group["sp_codes"])
            dskp = json.loads((CROSSWALK / (
                f"dskp_full_standard_texts_y{year}_20261107_DRAF.json"
            )).read_text(encoding="utf-8"))
            for code in group["sp_codes"]:
                self.assertRegex(code, r"^\d+\.\d+\.\d+$")
                self.assertIn(code, dskp["sp"])
                self.assertNotIn(code, buckets[year],
                                 "Same 2026 SP cannot appear in two evidence groups")
                buckets[year].add(code)
        self.assertEqual({year: len(codes) for year, codes in buckets.items()},
                         {4: 6, 5: 10, 6: 7})

    def test_2027_rbt_dates_stay_empty_even_when_2026_source_is_known(self):
        for year in (4, 5, 6):
            rows = rbt_records(year)
            self.assertEqual(len(rows), 32)
            for row in rows:
                self.assertEqual(row["week"], "")
                for field in ("a_start", "a_end", "b_start", "b_end"):
                    self.assertFalse(row.get(field))
                self.assertNotIn("APPROVED", row.get("schedule_status", ""))

if __name__ == "__main__":
    unittest.main()
