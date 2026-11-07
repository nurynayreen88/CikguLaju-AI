"""Safety gate: no draft becomes READY by passing layout/editorial QA."""
import unittest
from pi_release_readiness import readiness


class PIReleaseReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = readiness()

    def test_complete_catalog_not_fake_ready(self):
        r = self.r
        self.assertEqual((r["catalog_total"], r["drafts"], r["held"]), (696,690,6))
        self.assertEqual(r["critical_source_review"], 3)
        self.assertEqual(r["editor_preview_eligible"], 687)
        self.assertEqual(r["prepared_closing_jawi_candidates"], 690)
        self.assertEqual(r["expert_approved_jawi_candidates"], 0)
        self.assertEqual(r["book_activity_exercises_verified"], 0)
        self.assertEqual(r["individual_expert_approvals"], 0)
        self.assertEqual(r["native_telegram_web_rph_pdf_verified"], 0)
        self.assertEqual(r["ready_count"], 0)
        self.assertIsNone(r["academic_quality_percent"])
        self.assertIs(r["academic_quality_80_certified"], False)
        self.assertIs(r["can_merge_or_publish"], False)
        self.assertEqual(r["decision"], "NO_GO")

    def test_references_are_not_approval(self):
        r = self.r
        self.assertEqual(r["reviewed_textbook_toc_ranges"], 77)
        self.assertEqual(r["toc_ranges_consistent_with_book"], 74)
        self.assertEqual(r["invalid_book_end_page_claims"], 3)
        self.assertEqual(r["book_activity_page_candidates"], 174)
        self.assertAlmostEqual(r["mechanical_three_step_coverage_percent"], 99.57)
        self.assertGreaterEqual(len(r["release_blockers"]), 9)
        self.assertTrue(all(x["action"] for x in r["release_blockers"]))

    def test_year_summary_is_coherent(self):
        r = self.r
        y = r["by_year"]
        self.assertEqual({int(k):v["total_lessons"] for k,v in y.items()},
                         {2:112,3:147,4:151,5:143,6:143})
        self.assertEqual(y["2"]["full_source_held"], 1)
        self.assertEqual(y["6"]["full_source_held"], 5)
        self.assertEqual(y["4"]["critical_source_hold"], 1)
        self.assertEqual(y["6"]["critical_source_hold"], 2)
        self.assertEqual(y["2"]["pbd_focused_rewrites_pending_expert"], 14)
        self.assertEqual(y["3"]["pbd_focused_rewrites_pending_expert"], 29)
        self.assertEqual(y["2"]["outdated_page_notes_pending_sp_match"], 77)
        self.assertEqual(y["2"]["page_claims_past_book_end"], 3)
        self.assertEqual(sum(x["eligible_only_for_editor_preview"] for x in y.values()),687)
        self.assertEqual(sum(x["ready_for_teacher"] for x in y.values()),0)


if __name__ == "__main__":
    unittest.main()
