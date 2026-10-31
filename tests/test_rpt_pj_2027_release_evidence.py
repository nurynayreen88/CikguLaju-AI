import json
import unittest
from pathlib import Path

from rpt_pj_2027_calendar import read_calendar_csv
from rpt_pj_2027_release_policy import calendar_release_status

ROOT = Path(__file__).resolve().parents[1]


class TestReleaseEvidence(unittest.TestCase):
    def test_committed_evidence_matches_calendar(self):
        evidence = json.loads((ROOT / "data/rpt_pj_2027/final_audit_evidence.json").read_text(encoding="utf-8"))
        records = read_calendar_csv(ROOT / "data/rpt_pj_2027/calendar_2027_16_negeri_sheet_snapshot.csv")
        result = calendar_release_status(records, evidence["audit_final_rows"], evidence["release_rows"])
        self.assertTrue(result["approved"])
        self.assertGreater(result["legacy_label_count"], 0)
        self.assertTrue(result["requires_disclosure"])


if __name__ == "__main__":
    unittest.main()
