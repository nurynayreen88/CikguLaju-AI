"""Human approval gates for the first two restored Year 1 worksheet examples."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "audits/worksheet_y1_repair_review_queue_20261112.json"


class WorksheetYear1ReviewQueueTests(unittest.TestCase):
    def test_queue_agrees_with_actual_sources_and_does_not_publish(self):
        queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        self.assertEqual(queue["scope"], "INTERNAL_STAGING_ONLY")
        self.assertEqual(queue["live_feature_gate"], "OFF")
        self.assertFalse(queue["auto_publish"])
        self.assertEqual(len(queue["candidates"]), 2)
        self.assertEqual({x["subject"] for x in queue["candidates"]},
                         {"Matematik", "Sains"})
        for item in queue["candidates"]:
            with self.subTest(item=item["id"]):
                self.assertFalse(item["public"])
                self.assertFalse(item["teacher_approved"])
                self.assertIsNone(item["lesson_token"])
                self.assertEqual(item["content_status"], "REVIEW_REQUIRED")
                self.assertEqual(item["question_count"], 6)
                self.assertFalse(Path(item["source"]).is_absolute())
                self.assertNotIn("..", Path(item["source"]).parts)
                record = json.loads((ROOT / item["source"]).read_text(encoding="utf-8"))
                self.assertEqual(record["curriculum"]["year"], item["year"])
                self.assertEqual(record["curriculum"]["subject"], item["subject"])
                self.assertEqual(record["curriculum"]["sk"], item["sk"])
                self.assertEqual(record["curriculum"]["sp"], item["sp"])
                self.assertEqual(len(record["student_copy"]["questions"]), item["question_count"])
                self.assertEqual(record["approval"], "NOT_APPROVED_FOR_PRODUCTION")
                self.assertEqual(record["visibility"], "STAGING_INTERNAL")
                self.assertFalse(record["publish"])
                self.assertFalse(record["qa"]["teacher_approved"])
                self.assertFalse(record["qa"]["lesson_mapping_approved"])
                self.assertTrue(record["qa"]["no_public_routes"])
                self.assertIsNone(record["curriculum"]["lesson_token"])


if __name__ == "__main__":
    unittest.main()
