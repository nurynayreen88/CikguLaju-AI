"""A Year3 RPT unit index is evidence only, not a calendar or a release."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANDIDATE=ROOT/"rpt_2027/sains/tahun3_unit_order_source_candidate_20261106.json"
TITLES=("Kemahiran Saintifik","Peraturan Bilik Sains","Manusia",
        "Haiwan","Tumbuh-tumbuhan","Pengukuran","Ketumpatan",
        "Asid dan Alkali","Sistem Suria","Mesin")


class SainsYear3RPTIndexTests(unittest.TestCase):
    def test_source_units_are_numbered_and_not_scheduled(self):
        data=json.loads(CANDIDATE.read_text("utf-8"))
        units=data["source_book_unit_order"]
        self.assertEqual([u["unit_no"] for u in units],list(range(1,11)))
        self.assertEqual(tuple(u["unit_title"] for u in units),TITLES)
        self.assertEqual([u["book_printed_start_page"] for u in units],
                         [1,23,29,59,71,79,95,105,115,127])
        self.assertTrue(all(u["unit_label"].startswith(f"Unit {i}: ")
                            for i,u in enumerate(units,1)))
        self.assertEqual(data["status"],"NOT_AN_RPT_SCHEDULE_NOT_FINAL")
        self.assertEqual(data["release_status"],"HOLD")
        self.assertFalse(data["rpt_2027_calendar_allocated"])
        self.assertFalse(data["teacher_approval"])

    def test_2024_alignment_is_optional_and_no_fake_pdp_identity(self):
        data=json.loads(CANDIDATE.read_text("utf-8"))
        self.assertIn("optional",data["policy"])
        self.assertIn("2024",data["kpm_2024_alignment_letter"])
        self.assertTrue(all("week_no" not in u and "pdp_sequence_code" not in u
                            for u in data["source_book_unit_order"]))


if __name__=="__main__":
    unittest.main()
