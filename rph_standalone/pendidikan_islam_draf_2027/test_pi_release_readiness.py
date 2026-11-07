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
        self.assertEqual(r["direct_dskp_textbook_sp_footer_lesson_crosschecks"], 3)
        self.assertEqual(r["source_supported_sp543_jawi_wording_fixes"], 2)
        self.assertEqual(r["year2_dskp_codes_indexed"], 83)
        self.assertEqual(r["year2_lessons_with_existing_dskp_sp_codes"], 81)
        self.assertEqual(r["year2_tasmi_lessons_without_invented_sp"], 30)
        self.assertEqual(r["year2_full_sp_text_accuracy_verified"], 0)
        self.assertEqual(r["year3_awalan_direct_book_unit_references"], 12)
        self.assertEqual(r["year3_legacy_pdf34_hints_next_unit"], 6)
        self.assertEqual(r["year3_awalan_prefix_examples_expert_approved"], 0)
        self.assertEqual(r["year3_book_footer_code_present_lesson_count"], 109)
        self.assertEqual(r["year3_book_footer_exception_dskp_confirmed"], 1)
        self.assertEqual(r["year3_l146_dskp_643_645_objective_activity_pbd_revised_draft"],1)
        self.assertEqual(r["year3_l146_expert_approved"],0)
        self.assertEqual(r["year4_l083_original_hadith_excerpt_cited_in_draft"],1)
        self.assertEqual(r["year4_l083_hadith_expert_approved"],0)
        self.assertEqual(r["year6_tasmi_four_step_rph_drafts"],2)
        self.assertEqual(r["year6_tasmi_rpt_ayah_ranges_teacher_verified"],0)
        self.assertEqual(r["year6_tasmi_official_dskp_codes_invented"],0)
        self.assertEqual(r["year3_tasmi_verse_lessons_not_given_fake_sp"], 37)
        self.assertEqual(r["teacher_approved_page_specific_exercises"], 0)
        self.assertEqual(r["book_activity_page_candidates"], 174)
        self.assertAlmostEqual(r["mechanical_three_step_coverage_percent"], 100.0)
        self.assertGreaterEqual(len(r["release_blockers"]), 9)
        issue = [x for x in r["release_blockers"] if x["code"] ==
                 "YEAR3_6433_DSKP_BOOK_FOOTER_AND_L146_OBJECTIVE_REVIEW"]
        self.assertEqual(len(issue), 1)
        self.assertEqual(issue[0]["affected_lessons"], 1)
        self.assertIn("objective 2", issue[0]["action"])
        self.assertIn("merumus", issue[0]["action"])
        self.assertIn("DRAFT", issue[0]["action"])
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
        self.assertEqual(y["2"]["direct_dskp_textbook_sp_footer_crosschecked"], 3)
        self.assertEqual(y["2"]["source_dskp_code_presence_verified_only"], 81)
        self.assertEqual(y["2"]["tasmi_lessons_not_assigned_official_3_level_sp"], 30)
        self.assertEqual(y["3"]["source_textbook_awalan_unit_refs"], 12)
        self.assertEqual(y["3"]["old_pdf34_cross_topic_page_hints"], 6)
        self.assertEqual(y["3"]["book_footer_sp_code_present_only"], 109)
        self.assertEqual(y["3"]["book_footer_missing_but_dskp_manually_seen"], 1)
        self.assertEqual(y["3"]["l146_objective_activity_pbd_revised_pending_expert"],1)
        self.assertEqual(y["4"]["hadith_excerpt_from_original_source_pending_expert"],1)
        self.assertEqual(y["6"]["year6_tasmi_rpt_ayah_ranges_teacher_pending"],2)
        self.assertEqual(y["3"]["tasmi_verse_descriptions_without_3_level_sp"], 37)
        self.assertEqual(y["3"]["direct_dskp_textbook_sp_footer_crosschecked"], 0)
        self.assertEqual(sum(x["exact_lesson_activity_approvals"] for x in y.values()), 0)
        self.assertEqual(sum(x["eligible_only_for_editor_preview"] for x in y.values()),687)
        self.assertEqual(sum(x["ready_for_teacher"] for x in y.values()),0)


if __name__ == "__main__":
    unittest.main()
