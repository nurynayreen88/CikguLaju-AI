"""Year-6 Juz25 reconciliation cues cannot silently add Quran sessions."""
import unittest
from pi_t6_juz25_gap_resolution_editor_plan import build, EXPECTED


class PIY6Juz25GapResolutionDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = build()

    def test_four_unmapped_spans_have_explicit_order_hints(self):
        r = self.result
        self.assertEqual(r["source_rpt_verses_already_referenced"], 179)
        self.assertEqual(r["verified_juz25_verse_total"], 246)
        self.assertEqual(r["remaining_unassigned_verses"], 67)
        self.assertEqual(r["editor_decision_rows"], 4)
        self.assertEqual(sum(row["ayah_count"] for row in r["rows"]), 67)
        for row, exp in zip(r["rows"], EXPECTED):
            self.assertEqual((row["surah"], row["ayah_first"], row["ayah_last"],
                              row["ayah_count"], row["editor_location_hint"]), exp[:5])
            self.assertTrue(row["editor_action"])
        self.assertEqual(r["rows"][-1]["editor_location_hint"], "INSIDE_T6_L026_BOUNDARY")

    def test_no_auto_approval_or_rpt_rph_mutation(self):
        r = self.result
        self.assertEqual(r["teacher_exact_allocations_approved"], 0)
        self.assertEqual(r["new_official_dskp_codes_claimed"], 0)
        self.assertFalse(r["source_rpt_modified"])
        self.assertFalse(r["held_source_rph_modified"])
        self.assertEqual(r["publication"], "HOLD")
        self.assertEqual(r["release"], "NO_GO")
        self.assertIsNone(r["academic_quality_percent"])
        for row in r["rows"]:
            self.assertIsNone(row["teacher_allocated_lesson"])
            self.assertIsNone(row["exact_student_ayah_assignment"])
            self.assertFalse(row["teacher_quran_sequence_approved"])
            self.assertFalse(row["content_expert_approved"])
            self.assertFalse(row["rpt_changed"])
            self.assertFalse(row["rph_changed"])
            self.assertEqual(row["release"], "NO_GO")


if __name__ == "__main__":
    unittest.main()
