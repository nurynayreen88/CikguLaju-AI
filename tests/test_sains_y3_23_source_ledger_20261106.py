"""Static review gate for 23 historical Sains Y3 candidate corrections.

Deliberately no database writes, RPH runtime imports, network or PDF generation.
This validates source review evidence, not final readiness of a PdP or release.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "audits" / "sains_y3_23_source_candidate_ledger_20261106.json"
CORRECTIONS = {
    "SCI-Y3-PDP-002": ("8.1.2", "Mengitlak"),
    "SCI-Y3-PDP-005": ("3.1.1", "Memerihalkan"),
    "SCI-Y3-PDP-011": ("3.2.2", "Mengitlak"),
    "SCI-Y3-PDP-020": ("9.1.2", "Mengitlak suhu planet"),
    "SCI-Y3-PDP-021": ("9.1.3", "Memerihalkan planet beredar"),
}


class SainsYear3SourceLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(LEDGER.read_text("utf-8"))
        cls.rows = cls.data["records"]

    def test_covers_exact_23_unique_pending_records(self):
        self.assertEqual(len(self.rows), 23)
        self.assertEqual(len({r["pdp_code"] for r in self.rows}), 23)
        self.assertEqual([r["source_sequence_no"] for r in self.rows],
                         list(range(1, 24)))
        self.assertEqual([r["historical_row_id"] for r in self.rows],
                         list(range(282, 305)))
        self.assertEqual(self.data["status"],
                         "DRAF_SOURCE_CROSSCHECK_ONLY_NOT_DB_EDIT")
        self.assertEqual(self.data["summary"]["pending"], 23)

    def test_exact_five_dskp_wording_differences_are_not_silently_approved(self):
        mismatch = {r["pdp_code"]: r for r in self.rows
                    if not r["original_title_matches_dskp"]}
        self.assertEqual(set(mismatch), set(CORRECTIONS))
        self.assertEqual(self.data["summary"]["candidate_title_fixes"], 5)
        for code, (expected_sp, prefix) in CORRECTIONS.items():
            row = mismatch[code]
            self.assertEqual(row["sp_code"], expected_sp)
            self.assertTrue(row["candidate_pdp_title"].startswith(prefix))
            self.assertNotEqual(row["original_pdp_title"],
                                row["candidate_pdp_title"])
            self.assertEqual(row["release_decision"], "HOLD")

    def test_solar_system_codes_respect_official_3_distinct_objectives(self):
        by_code = {r["pdp_code"]: r for r in self.rows}
        temp = by_code["SCI-Y3-PDP-020"]
        orbit = by_code["SCI-Y3-PDP-021"]
        period = by_code["SCI-Y3-PDP-022"]
        self.assertEqual([temp["sp_code"], orbit["sp_code"], period["sp_code"]],
                         ["9.1.2", "9.1.3", "9.1.4"])
        self.assertIn("suhu planet", temp["candidate_pdp_title"].lower())
        self.assertIn("orbit", orbit["candidate_pdp_title"].lower())
        self.assertIn("masa planet", period["candidate_pdp_title"].lower())
        self.assertNotEqual(orbit["candidate_pdp_title"],
                            period["candidate_pdp_title"])

    def test_page_cues_are_evidence_not_release(self):
        for row in self.rows:
            self.assertEqual(row["manual_visual_page_and_activities_check"],
                             "PENDING")
            self.assertEqual(row["release_decision"], "HOLD")
            self.assertTrue(row["textbook_sp_code_observed"])
            self.assertTrue(all(1 <= p <= 200 for p in row[
                "textbook_printed_pages_evidence"]))
            self.assertTrue(row["dskp_sp_text"])
            self.assertTrue(row["candidate_pdp_title"])
        self.assertIn("17QNqKZjSF7V9GzzkXkz46bDJGnyKYq-F",
                      self.data["textbook_url"])
        self.assertIn("1n4OM7x2e1_LIaBQDIxyeHmXglImtu5Yb",
                      self.data["dskp_url"])


if __name__ == "__main__":
    unittest.main()
