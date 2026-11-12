"""Check 29 content Sains SP form exactly 12 SK topics, not fake lessons."""
import unittest
from scripts.audit_sains_2027_29_sp_12_topic_clusters_staging import group_29_content_sp

class Sains29ContentSPClusterQA(unittest.TestCase):
    def test_clusters_have_all_source_sp_with_safe_placement(self):
        info=group_29_content_sp()
        self.assertEqual(info["topic_clusters"],12)
        self.assertEqual(info["unrepresented_content_sp"],29)
        self.assertEqual(info["year_counts"],{"4":6,"5":2,"6":4})
        self.assertTrue(info["counts_are_not_new_lessons"])
        self.assertEqual(info["production_changes"],0)
        codes=set()
        for cluster in info["clusters"]:
            self.assertFalse(cluster["approved_for_release"])
            self.assertIsNone(cluster["proposed_lesson_week"])
            self.assertEqual(len(cluster["missing_sp"]),cluster["missing_content_sp_count"])
            self.assertIn(cluster["candidate_action"],(
                "ATTACH_WITH_EXPLICIT_ACTIVITY_RPH_REVIEW",
                "NEW_TOPIC_UNIT_NEEDS_TEXTBOOK_SOURCE_AND_LESSON_PLAN",
            ))
            for entry in cluster["existing_historical_pdp_same_sk"]:
                self.assertRegex(entry["pdp_id"],r"^\d{3}$")
            for item in cluster["missing_sp"]:
                self.assertGreater(len(item["sp_statement"]),10)
                key=(cluster["year"],item["sp_code"])
                self.assertNotIn(key,codes)
                codes.add(key)
        self.assertEqual(len(codes),29)

if __name__=="__main__":
    unittest.main()
