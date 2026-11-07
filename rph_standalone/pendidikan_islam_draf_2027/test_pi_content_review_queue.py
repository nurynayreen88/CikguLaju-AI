"""Safety and completeness regressions for the risk-prioritized PI review queue."""
import unittest
from pi_content_review_queue import build_queue, PRIORITIES
from pi_quality_audit import COUNT


class PIContentReviewQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queue = build_queue()

    def test_no_record_loss_and_no_false_release(self):
        q = self.queue
        self.assertEqual(q["total"], sum(COUNT.values()))
        self.assertEqual(len(set(r["id"] for r in q["rows"])), 696)
        self.assertIsNone(q["quality_score_percent"])
        self.assertIs(q["quality_80_certified"], False)
        self.assertIs(q["can_publish"], False)
        self.assertEqual(q["release"], "NO_GO")
        self.assertEqual(sum(q["by_priority"].values()), 696)
        self.assertEqual(set(q["by_priority"]), set(PRIORITIES))
        for row in q["rows"]:
            self.assertIs(row["can_publish"], False)
            self.assertIs(row["content_expert_approved"], False)
            self.assertIs(row["book_page_verified_in_this_audit"], False)
            self.assertIs(row["book_activity_verified_in_this_audit"], False)
            self.assertEqual(row["release"], "NO_GO")
            self.assertTrue(row["editor_next_step"])

    def test_all_six_holds_have_no_teaching_content(self):
        held = [r for r in self.queue["rows"] if r["priority"] == "P0_HELD"]
        self.assertEqual(len(held), 6)
        self.assertTrue(all(r["sp_as_source"] is None for r in held))

    def test_critical_source_cases_are_not_auto_completed(self):
        critical = [r["id"] for r in self.queue["rows"]
                    if r["priority"] == "P1_CRITICAL_SOURCE"]
        self.assertEqual(critical, ["T4-L083", "T6-L137", "T6-L141"])

    def test_measured_pbd_and_page_review_not_misnamed_quality_score(self):
        q = self.queue
        self.assertEqual(q["generic_pbd_records"], 43)
        self.assertEqual(q["unverified_old_page_note_records"], 77)
        self.assertEqual(q["by_priority"]["P2_PBD_OR_PAGE"], 108)
        pbd = [r for r in q["rows"]
               if "PBD_TIDAK_KHUSUS_KEPADA_SP" in r["reason_codes"]]
        self.assertEqual(len(pbd), 43)
        self.assertTrue(all(r["year"] in (2, 3) for r in pbd))
        self.assertEqual(len([r for r in pbd if r["year"] == 2]), 14)
        self.assertEqual(len([r for r in pbd if r["year"] == 3]), 29)


if __name__ == "__main__":
    unittest.main()
