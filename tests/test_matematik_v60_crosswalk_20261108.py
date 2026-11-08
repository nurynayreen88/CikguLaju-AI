"""A code/SP match is only a candidate, never an approved lesson."""
import unittest

from web.matematik_v60_crosswalk_candidates import make_candidates


def row(code, lesson, sk, sp):
    return {"pdp_sequence_code": code, "source_sequence_no": lesson,
            "sk_code": sk, "sp_code": sp,
            "unit_title": "Nombor", "pdp_title": "Latihan guru"}


class CrosswalkCandidateGateTests(unittest.TestCase):
    def test_same_number_is_still_only_a_candidate(self):
        a = make_candidates(2, [row("N1", 1, "1.1", "1.1.1")])
        self.assertEqual(a["native_pdp_count"], 1)
        self.assertEqual(a["candidates"][0]["status"], "EXACT_NUMBER_AND_SKSP_CANDIDATE")
        self.assertFalse(a["candidates"][0]["approved"])
        self.assertEqual(a["approved_count"], 0)

    def test_different_sequence_can_be_reviewed_not_published(self):
        a = make_candidates(2, [row("N5", 99, "1.1", "1.1.1")])
        self.assertEqual(a["candidates"][0]["status"],
                         "UNIQUE_SKSP_DIFFERENT_NUMBER_CANDIDATE")
        self.assertEqual(a["candidates"][0]["candidate_v60_lessons"][0]["lesson"], 1)
        self.assertFalse(a["candidates"][0]["approved"])

    def test_duplicate_SP_and_multi_SP_block_autoselection(self):
        same_sp = make_candidates(2, [row("R", 10, "1.7", "1.7.1")])
        self.assertEqual(same_sp["candidates"][0]["status"], "AMBIGUOUS_DUPLICATE_SKSP")
        composite = make_candidates(2, [row("R", 10, "1.7", "1.7.1"),
                                       row("R", 10, "1.7", "1.7.2")])
        self.assertEqual(composite["candidates"][0]["status"], "BLOCKED_MULTI_SP")

    def test_duplicate_number_across_pdp_keys_blocks_both(self):
        r = make_candidates(2, [row("A", 1, "1.1", "1.1.1"),
                                row("B", "1", "1.1", "1.1.1")])
        self.assertEqual(r["status_counts"], {"BLOCKED_DUPLICATE_NATIVE_NUMBER": 2})
        self.assertEqual(r["approved_count"], 0)

    def test_never_mutates_input(self):
        original = row("R", 1, "1.1", "1.1.1")
        old = dict(original)
        make_candidates(2, [original])
        self.assertEqual(old, original)


if __name__ == "__main__":
    unittest.main()
