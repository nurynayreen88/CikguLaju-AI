"""Crosscheck every Jawi penutup candidate against its exact unchanged Rumi source."""
import unittest
from pi_editor_jawi_closing_projection import preview


class PIJawiClosingProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=preview()

    def test_each_nonheld_lesson_has_preview_closing_in_jawi_and_original(self):
        r=self.data
        self.assertEqual(r["jawi_closing_candidates_injected_in_reversible_preview"],690)
        self.assertEqual(r["unique_reviewable_jawi_closing_groups"],78)
        self.assertEqual(len(r["rows"]),690)
        self.assertTrue(r["all_original_rumi_closings_preserved"])
        self.assertEqual(r["original_rph_fields_modified"],0)
        for row in r["rows"]:
            self.assertNotEqual(row["original_penutup_rumi"],row["display_fields"]["penutup"])
            self.assertEqual(len(row["penutup_original_sha256"]),64)
            self.assertTrue(row["jawi_candidate_group_id"].startswith("PI-CLOSING-"))
            self.assertFalse(row["jawi_spelling_approved"])
            self.assertFalse(row["sp_content_expert_approved"])
            self.assertFalse(row["can_publish"])

    def test_still_not_academically_approved_or_live(self):
        self.assertEqual(self.data["academic_and_jawi_approved"],0)
        self.assertEqual(self.data["ready_for_teacher"],0)
        self.assertIs(self.data["source_year1_included"],False)
        self.assertEqual(self.data["release"],"NO_GO")
        self.assertIsNone(self.data["academic_quality_percent"])


if __name__=="__main__":
    unittest.main()
