"""Safe, source-locked Year5 Science three-part book reference staging QA."""
import unittest

from tools.render_sains_y5_83_rph_draf_20261107 import get_y5_records
from web.sains_y5_83_textbook_resources_20261107 import proposed_textbook_material


class TestSainsY5BookReferences(unittest.TestCase):
    def test_every_one_of_83_pdp_maps_to_correct_sp_and_source(self):
        records=get_y5_records()
        self.assertEqual(len(records),83)
        for row in records:
            card=proposed_textbook_material(
                "Sains",5,row["pdp_code"],row["sp"])
            self.assertEqual(card["pdp_code"],row["pdp_code"])
            self.assertEqual(card["sp"],row["sp"])
            self.assertEqual(card["primary_printed_page"],
                             row["textbook_page_primary"])
            self.assertTrue(card["source_url"].startswith(
                "https://drive.google.com/file/d/"))
            self.assertEqual(len(card["source_parts"]),3)
            self.assertFalse(card["teacher_academic_approved"])
            self.assertFalse(card["ready_for_runtime"])
            self.assertIsNone(card["direct_download_url"])
            self.assertEqual(card["download_method"],
                             "OPEN_EXTERNAL_DRIVE_SOURCE__NO_APP_COPY")
            self.assertTrue(all(p["source_url"].startswith("https://drive.google.com/file/d/")
                                for p in card["source_pages"]))

    def test_accurate_pdf_local_pages_and_three_part_boundary(self):
        first=proposed_textbook_material(
            "Science","5","SCI-Y5-PDP-001","2.1.1")
        self.assertEqual(first["source_part"],1)
        self.assertEqual(first["primary_printed_page"],20)
        self.assertEqual(first["primary_pdf_page_1_based"],28)
        across=next(r for r in get_y5_records() if r["sp"]=="5.2.6")
        item=proposed_textbook_material(
            "Sains",5,across["pdp_code"],across["sp"])
        self.assertEqual([p["printed_page"] for p in item["source_pages"]],
                         [129,131])
        self.assertEqual([p["source_part"] for p in item["source_pages"]],
                         [2,3])
        self.assertEqual([p["pdf_page_1_based"] for p in item["source_pages"]],
                         [94,1])
        self.assertEqual(
            [(p["printed_from"],p["printed_to"]) for p in item["source_parts"]],
            [(1,35),(36,130),(131,234)])
        self.assertEqual(len({p["sha256"] for p in item["source_parts"]}),3)

    def test_fail_closed_on_wrong_year_subject_sp_or_pdp(self):
        self.assertIsNone(proposed_textbook_material(
            "Matematik",5,"SCI-Y5-PDP-001","2.1.1"))
        self.assertIsNone(proposed_textbook_material(
            "Sains",4,"SCI-Y5-PDP-001","2.1.1"))
        with self.assertRaises(ValueError):
            proposed_textbook_material("Sains",5,"SCI-Y5-PDP-001","2.1.2")
        with self.assertRaises(ValueError):
            proposed_textbook_material("Sains",5,"SCI-Y5-PDP-999","2.1.1")


if __name__=="__main__":
    unittest.main()
