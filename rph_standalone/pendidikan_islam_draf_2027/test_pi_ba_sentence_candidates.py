"""Candidate workbook sentences exist for editing but NEVER enter live RPH."""
import unittest
from pi_ba_sentence_candidates import sentence_candidates, TOPIC
from pi_ba_match_queue import match_queue, NEEDS_PAGE


class TestBookSentenceCandidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=sentence_candidates()
        cls.rows={r["lesson_id"]:r for r in cls.report["rows"]}

    def test_all_174_cue_proposals_and_jawi_first(self):
        self.assertEqual(self.report["proposal_count"],174)
        self.assertEqual(self.report["jawi_priority_count"],73)
        self.assertEqual(self.report["status"],"STAGING_EDITOR_ONLY")
        self.assertEqual(self.report["verified_page_count"],0)
        self.assertEqual(self.report["ready_rph_count"],0)
        self.assertEqual(len(self.rows),174)

    def test_zero_injection_zero_fake_page_numbers(self):
        for r in self.rows.values():
            self.assertIn("SP",r["candidate_jawi_one_sentence"])
            self.assertIn("بوکو اکتيۏيتي",r["candidate_jawi_one_sentence"])
            self.assertNotIn("[",r["candidate_jawi_one_sentence"])
            self.assertIs(r["not_teacher_facing"],True)
            self.assertIs(r["injected_into_rph"],False)
            self.assertIs(r["book_exercise_verified"],False)
            self.assertIs(r["sp_and_exercise_alignment_verified"],False)
            self.assertIs(r["jawi_checked_by_expert"],False)
            self.assertIs(r["a4_render_checked"],False)
            self.assertIsNone(r["book_printed_page"])
            self.assertIsNone(r["book_exercise_id"])
            self.assertEqual(r["release"],"HOLD")

    def test_coverage_exactly_matches_page_queue(self):
        expected={x["id"] for x in match_queue()["rows"]
                  if x["disposition"]==NEEDS_PAGE}
        self.assertEqual(set(self.rows),expected)
        self.assertEqual(len(TOPIC),10)
        self.assertTrue(all(r["candidate_jawi_one_sentence"].startswith("جك") for r in self.rows.values()))


if __name__=="__main__":
    unittest.main()
