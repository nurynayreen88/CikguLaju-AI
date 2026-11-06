"""All external page hints must remain second-hand and unreachable by runtime."""
import unittest

from pi_ba_secondary_evidence import evidence_queue


class SecondaryEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = evidence_queue()

    def test_30_topic_matched_secondary_page_hints(self):
        d = self.data
        self.assertEqual(d["year2_year3_candidate_lessons"], 174)
        self.assertEqual(d["secondary_page_hints"], 30)
        self.assertEqual(d["hints_by_year"], {2:1, 3:29})
        self.assertEqual(d["page_mappings_verified_from_original"], 0)
        self.assertEqual(d["rph_activity_book_injections"], 0)
        self.assertEqual(d["status"], "NO_GO_SECONDARY_EVIDENCE_ONLY")
        self.assertEqual(len({x["lesson_id"] for x in d["rows"]}), 30)

    def test_no_publication_or_fake_verification(self):
        for x in self.data["rows"]:
            self.assertTrue(x["page_numbers_reported_by_secondary_source"])
            self.assertTrue(x["secondary_source_url"].startswith("https://"))
            self.assertIn("SP", x["review_next"])
            self.assertEqual(x["source_credibility"], "SECONDARY_TEACHER_RESOURCE_ONLY")
            self.assertIs(x["page_number_is_verified_in_original_book"], False)
            self.assertIs(x["actual_printed_book_seen_at_page"], False)
            self.assertIs(x["exercise_instruction_verified"], False)
            self.assertIs(x["edition_and_print_page_verified"], False)
            self.assertIs(x["book_page_to_lesson_match_approved"], False)
            self.assertIs(x["copyright_permission_to_distribute"], False)
            self.assertIs(x["allow_auto_inject_to_rph"], False)
            self.assertIsNone(x["teacher_sentence"])

    def test_conflicted_jawi_source_is_flagged_for_human_review(self):
        idx = {x["lesson_id"]:x for x in self.data["rows"]}
        conflicted = [r for r in self.data["rows"] if r["cross_source_conflict_detected"]]
        self.assertEqual([r["lesson_id"] for r in conflicted], ["T3-L004"])
        self.assertIn("p65-66", conflicted[0]["conflict_note"])
        self.assertIs(conflicted[0]["allow_auto_inject_to_rph"], False)
        self.assertIsNone(conflicted[0]["teacher_sentence"])

    def test_critical_source_matched_topics(self):
        idx = {x["lesson_id"]:x for x in self.data["rows"]}
        self.assertEqual(idx["T3-L097"]["page_numbers_reported_by_secondary_source"], [35])
        self.assertIn("إخفاء حقيقي", idx["T3-L097"]["sp_original"])
        self.assertEqual(idx["T3-L087"]["page_numbers_reported_by_secondary_source"], [124,125])
        self.assertIn("علمو", idx["T3-L087"]["sp_original"])
        self.assertEqual(idx["T3-L068"]["page_numbers_reported_by_secondary_source"], [52])
        self.assertIn("اخيرن", idx["T3-L068"]["sp_original"])
        self.assertEqual(idx["T2-L108"]["page_numbers_reported_by_secondary_source"], [134,135,136])
        self.assertEqual(idx["T3-L111"]["page_numbers_reported_by_secondary_source"], [90,91,92,93,94,95,96])
        self.assertEqual(idx["T3-L123"]["page_numbers_reported_by_secondary_source"], [59])


if __name__ == "__main__":
    unittest.main()
