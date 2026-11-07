"""Staged Web/Telegram book download metadata test, never live-enabled."""
import unittest
from web.sains_buku_aktiviti_resources_20261107 import proposed_material

class TestSainsBAResources(unittest.TestCase):
    def test_same_original_year_file_for_all_pdp_and_distinct_exercise_pages(self):
        a=proposed_material("Sains",2,"SCI-Y2-PDP-001","3.1.1")
        b=proposed_material("Sains",2,"SCI-Y2-PDP-002","3.1.2")
        self.assertEqual(a["source_url"],b["source_url"])
        self.assertNotEqual(a["book_printed_page"],b["book_printed_page"])
        self.assertEqual(a["book_printed_page"],13)
        self.assertEqual(b["pdf_page_1_based"],18)
        self.assertFalse(a["ready_for_runtime"])
        self.assertEqual(a["material_type"],"BUKU_AKTIVITI")
    def test_science_year3_different_file_and_precise_exercise(self):
        y3=proposed_material("Sains",3,"SCI-Y3-PDP-044","10.1.4")
        y2=proposed_material("Sains",2,"SCI-Y2-PDP-044","9.2.5")
        self.assertNotEqual(y3["source_url"],y2["source_url"])
        self.assertEqual(y3["book_printed_page"],90)
        self.assertEqual(y3["exercise"],"Model Takal Saya")
    def test_related_only_exercise_not_assigned_as_curriculum_pbd(self):
        butterfly=proposed_material("Sains",2,"SCI-Y2-PDP-010","4.1.7")
        shadow=proposed_material("Sains",2,"SCI-Y2-PDP-022","6.1.6")
        for item in (butterfly,shadow):
            self.assertFalse(item["printed_sp_matches_pdp"])
            self.assertEqual(item["assignment_status"],"RELATED_ONLY__DO_NOT_ASSIGN_AS_SP_PBD")
            self.assertFalse(item["ready_for_runtime"])
        growth=proposed_material("Sains",2,"SCI-Y2-PDP-003","3.1.3")
        self.assertEqual(growth["book_printed_page"],16)
        self.assertTrue(growth["printed_sp_matches_pdp"])

    def test_full_content_review_visible_in_staging_resource_but_never_ready(self):
        examples=[
            (2,"SCI-Y2-PDP-036","9.1.2","pisau"),
            (3,"SCI-Y3-PDP-033","8.1.2","jangan rasa"),
            (3,"SCI-Y3-PDP-019","5.1.3","guru"),
        ]
        for year,pdp,sp,expected in examples:
            item=proposed_material("Sains",year,pdp,sp)
            self.assertEqual(item["content_review_status"],"DIRECT_EXERCISE_CONTENT_REVIEW")
            self.assertIn(expected,item["teacher_usage_guidance"].lower())
            self.assertFalse(item["teacher_academic_approved"])
            self.assertFalse(item["ready_for_runtime"])
        unmatched=proposed_material("Sains",2,"SCI-Y2-PDP-010","4.1.7")
        self.assertEqual(unmatched["assignment_status"],"RELATED_ONLY__DO_NOT_ASSIGN_AS_SP_PBD")
        self.assertIn("pbd",unmatched["teacher_usage_guidance"].lower())

    def test_not_other_year_or_subject(self):
        self.assertIsNone(proposed_material("Matematik",2,"SCI-Y2-PDP-001","3.1.1"))
        self.assertIsNone(proposed_material("Sains",4,"SCI-Y4-PDP-001","2.1.1"))
        with self.assertRaises(ValueError):
            proposed_material("Sains",3,"SCI-Y3-PDP-001","3.1.2")

if __name__=="__main__":
    unittest.main()
