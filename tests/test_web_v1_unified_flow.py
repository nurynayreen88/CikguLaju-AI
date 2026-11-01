import unittest
from web_v1_unified_flow import normalize_flow, reset_after_change


class UnifiedFlowTests(unittest.TestCase):
    def test_bm_and_english_have_identical_selection_structure(self):
        for subject in ("Bahasa Melayu", "Bahasa Inggeris", "Matematik", "Sains", "Pendidikan Islam", "PJPK"):
            with self.subTest(subject=subject):
                flow = normalize_flow(year=3, subject=subject, unit="Unit 1", lesson="Lesson 1")
                self.assertEqual((flow.year, flow.subject, flow.unit, flow.lesson), (3, subject, "Unit 1", "Lesson 1"))
                self.assertEqual(reset_after_change(flow, "subject").unit, "")
                self.assertEqual(reset_after_change(flow, "unit").lesson, "")

    def test_out_of_order_selection_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_flow(year=3, lesson="1")
        with self.assertRaises(ValueError):
            normalize_flow(year=3, unit="Unit 1")


if __name__ == "__main__":
    unittest.main()
