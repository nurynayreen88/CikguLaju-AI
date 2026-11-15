"""No silent Quran source gaps/overlaps across Y2-6 tasmi' lessons."""
import unittest
from pi_tasmi_continuity_quality_guard import audit


class PITasmiContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data=audit()

    def test_unresolved_source_holes_are_counted_and_held(self):
        r=self.data
        self.assertEqual(r["source_gaps_year2_l035_held_ayat225_to245"],21)
        self.assertEqual(r["source_juz25_original_year6_missing_ayah"],67)
        self.assertEqual({str(x["year"]):x["missing_ayat_within_referenced_bounds"]
                          for x in r["by_year"]},
                         {"2":21,"3":0,"4":0,"5":0,"6":184})
        self.assertEqual(r["proposed_verse_assignments"],0)
        self.assertEqual(r["expert_approved"],0)
        self.assertEqual(r["release"],"NO_GO")

    def test_no_nonheld_source_overlap_and_high_workload_flagged(self):
        r=self.data
        self.assertEqual(sum(y["nonheld_source_verse_duplicates"] for y in r["by_year"]),0)
        self.assertEqual(next(y for y in r["by_year"] if y["year"]==6)
                         ["unbounded_tasmi_lessons"],["T6-L137","T6-L141"])
        self.assertGreaterEqual(r["high_volume_60plus_ayah_source_lessons_for_teacher_review"],10)
        self.assertGreaterEqual(r["maximum_ayah_in_one_source_pdp"],106)
        self.assertTrue(all(not x["can_publish"] and not x["teacher_time_approved"]
                            for x in r["high_volume_review_queue"]))

if __name__=="__main__": unittest.main()
