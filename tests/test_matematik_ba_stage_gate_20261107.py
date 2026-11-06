"""Standalone tests. No runtime, DB, or external services touched."""
import unittest
from tools.matematik_ba_stage_gate_20261107 import verified_ba_reference


class BookActivityGateTests(unittest.TestCase):
    def row(self):
        return dict(year="2", v41_lesson_id="T2-L001", ba_exact_page="1-2",
                    ba_activity_ref="Aktiviti 1", ba_source_key="T2_SCAN_REVIEWED",
                    bt_sp_semantic_check="YES", visual_page_check="YES",
                    source_edition_check="YES", reviewer="sample-reviewer",
                    evidence_note="verified page and exercise",
                    approval="APPROVED")

    def test_complete_manual_approval(self):
        self.assertEqual(
            verified_ba_reference(self.row()),
            "Buku Aktiviti Matematik Tahun 2, hlm. 1-2, Aktiviti 1.")

    def test_unapproved_is_never_rendered(self):
        row = self.row()
        row["approval"] = "NOT_APPROVED"
        self.assertIsNone(verified_ba_reference(row))

    def test_every_gate_is_required(self):
        for key in ("bt_sp_semantic_check", "visual_page_check",
                    "source_edition_check", "reviewer", "evidence_note",
                    "ba_source_key", "ba_exact_page", "ba_activity_ref"):
            with self.subTest(key=key):
                row = self.row()
                row[key] = ""
                self.assertIsNone(verified_ba_reference(row))

    def test_wrong_year_or_lesson_is_blocked(self):
        row = self.row()
        row["v41_lesson_id"] = "T3-L001"
        self.assertIsNone(verified_ba_reference(row))
        row = self.row()
        row["year"] = "1"
        self.assertIsNone(verified_ba_reference(row))

    def test_invalid_page_ranges_are_blocked(self):
        for page in ("0", "20-10", "1-9999", "hlm 10", "2,3"):
            with self.subTest(page=page):
                row = self.row()
                row["ba_exact_page"] = page
                self.assertIsNone(verified_ba_reference(row))


if __name__ == "__main__":
    unittest.main()
