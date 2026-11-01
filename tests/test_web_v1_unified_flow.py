import unittest
from web_v1_unified_flow import normalize_flow, reset_after_change
from web_v1_dropdown_catalog import component_options, verified_component_records


class UnifiedFlowTests(unittest.TestCase):
    def test_bm_and_english_have_identical_selection_structure(self):
        for subject in ("Bahasa Melayu", "Bahasa Inggeris", "Matematik", "Sains", "Pendidikan Islam", "PJPK"):
            with self.subTest(subject=subject):
                flow = normalize_flow(year=3, subject=subject, unit="Unit 1", lesson="Lesson 1")
                self.assertEqual((flow.year, flow.subject, flow.unit, flow.lesson), (3, subject, "Unit 1", "Lesson 1"))
                self.assertEqual(reset_after_change(flow, "subject").unit, "")
                self.assertEqual(reset_after_change(flow, "unit").lesson, "")

    def test_pjpk_has_explicit_optional_component(self):
        self.assertEqual([x["value"] for x in component_options("PJPK")], ["PJ", "PK"])
        self.assertEqual(component_options("BM"), [])
        records = [
            {"component": "PJ", "component_verified": True},
            {"component": "PK", "component_verified": True},
            {"component": "PJ", "component_verified": False},
            {"topic": "Unknown"},
        ]
        self.assertEqual(verified_component_records(records, "PJPK", "PJ"), [records[0]])
        self.assertEqual(verified_component_records(records, "PJPK", "PK"), [records[1]])
        with self.assertRaises(ValueError):
            verified_component_records(records, "PJPK", None)

    def test_out_of_order_selection_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_flow(year=3, lesson="1")
        with self.assertRaises(ValueError):
            normalize_flow(year=3, unit="Unit 1")


if __name__ == "__main__":
    unittest.main()
