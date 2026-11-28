import unittest
from unittest.mock import patch
from tools.export_science_native_5p_mapping_input import collect

class ScienceNativeMappingTests(unittest.TestCase):
    @patch("tools.export_science_native_5p_mapping_input.native.list_native_lessons")
    @patch("tools.export_science_native_5p_mapping_input.native.list_native_units")
    def test_preserve_native_tokens_and_leave_unmapped(self, units, lessons):
        units.return_value=[{"value":"u"+"a"*24,"label":"3.1 • Manusia"},
                            {"value":"u"+"b"*24,"label":"3.2 • Manusia"}]
        lessons.side_effect=[[{"value":"S3-PDP-019","label":"PdP 19 • Gigi","textbook_ref":"BT 12"}],
                             [{"value":"S3-PDP-020","label":"PdP 20 • Makanan"}]]
        report=collect(3)
        self.assertEqual(report["native_selection_count"],2)
        self.assertEqual(report["unique_lesson_ids"],2)
        self.assertFalse(report["academic_approval"])
        self.assertEqual([x["unit"] for x in report["records"]],[u["value"] for u in units.return_value])
        self.assertEqual([x["lesson_id"] for x in report["records"]],["S3-PDP-019","S3-PDP-020"])
        self.assertEqual(report["records"][0]["textbook_ref"],"BT 12")
        self.assertTrue(all(x["candidate_id"] is None and x["ready"] is False for x in report["records"]))
        lessons.assert_any_call(3,"SCIENCE",units.return_value[1]["value"])

    @patch("tools.export_science_native_5p_mapping_input.native.list_native_lessons")
    @patch("tools.export_science_native_5p_mapping_input.native.list_native_units")
    def test_duplicate_selection_and_empty_unit_rejected(self, units, lessons):
        units.return_value=[{"value":"u"+"a"*24,"label":"Unit 1"}]
        row={"value":"PDP-1","label":"PdP 1"}
        for items in ([row,row],[]):
            lessons.return_value=items
            with self.assertRaises(ValueError):
                collect(2)

    def test_invalid_year(self):
        with self.assertRaises(ValueError):
            collect(1)
