"""Source-locked Year2 SP-specific PBD evidence for 2 BA mismatch cases.

Original task sheets; NOT rebranded KPM activity book, not production-ready.
"""
import unittest
from pathlib import Path
from tools.sains_buku_aktiviti_mapping_20261107 import activity_for,is_direct_sp_match
from tools.render_sains_y2_2_sp_alternative_pbd_20261107 import (
    TASKS, DSKP_URL,doc_file
)
from tools.render_sains_y2_51_rph_draf_20261107 import get_y2_records,markdown

class TestTwoYear2PBDAlternatives(unittest.TestCase):
    def test_only_two_mismatched_sps_have_original_pbd_sheet(self):
        self.assertEqual(set(TASKS),{"4.1.7","6.1.6"})
        for sp,item in TASKS.items():
            ref=activity_for(2,item["pdp"],sp)
            self.assertFalse(is_direct_sp_match(ref))
            self.assertEqual(item["related_page"],ref["workbook_printed_page"])
            self.assertEqual(item["related_sp"],ref["workbook_printed_sp_codes"][0])
            self.assertIn("drive.google.com",DSKP_URL)
            self.assertIn("lakaran",item["sp_text"])
            self.assertEqual(len(item["criteria"]),3)
            self.assertTrue(item["question1"] and item["question2"] and item["question3"])
            self.assertIn("PBD_ALTERNATIF_DRAF",doc_file(sp).name)

    def test_rph_never_calls_wrong_workbook_page_a_direct_sp_pbd(self):
        rows=get_y2_records()
        self.assertEqual(len(rows),51)
        alternative=[r for r in rows if r["pbd_alternative"]]
        self.assertEqual({r["sp"] for r in alternative},set(TASKS))
        for row in alternative:
            text=markdown(row)
            self.assertIn("bukan SP PdP",text)
            self.assertIn("PBD alternatif bukan BA rasmi",text)
            self.assertIn(row["pbd_alternative"],text)
            self.assertIn("JANGAN",text)

    def test_no_49_direct_sp_rph_has_dummy_worksheet_link(self):
        for row in get_y2_records():
            if row["sp"] not in TASKS:
                self.assertFalse(row["pbd_alternative"])
                self.assertTrue(is_direct_sp_match(row["activity_book"]))

    def test_content_specific_to_official_dskp(self):
        life=TASKS["4.1.7"]
        self.assertIn("pembiakan dan tumbesaran",life["sp_text"])
        self.assertIn("lisan",life["question3"])
        self.assertIn("rama-rama",life["question1"])
        dark=TASKS["6.1.6"]
        self.assertIn("terang dan gelap",dark["sp_text"])
        self.assertIn("menyala",dark["question1"])
        self.assertIn("padam",dark["question2"])
        self.assertIn("mata",dark["safe"])

if __name__=="__main__":
    unittest.main()
