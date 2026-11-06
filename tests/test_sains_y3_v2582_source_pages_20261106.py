"""Sains Y3 latest source quality holds: source page evidence ≠ ready RPH."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TITLE=ROOT/"audits/sains_y3_v2582_12_dskp_title_corrections_20261106.json"
PAGES=ROOT/"audits/sains_y3_v2582_45_textbook_page_candidates_20261106.json"
class SainsLatestSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t=json.loads(TITLE.read_text("utf-8"))
        cls.p=json.loads(PAGES.read_text("utf-8"))
    def test_exact_source_identifiers_not_older_2568(self):
        changes=self.t["changes"]
        self.assertEqual(len(changes),12)
        self.assertEqual({r["sp_code"] for r in changes},{
            "3.1.1","3.2.2","3.3.1","3.3.2",
            "5.1.2","5.1.3","6.1.3","6.1.4",
            "7.1.2","8.1.2","9.1.2","9.1.3"})
        self.assertEqual({r["pdp_code"] for r in changes},{f"SCI-Y3-PDP-{x:03}"
            for x in (1,7,10,11,18,19,23,24,29,33,37,38)})
        self.assertEqual(self.t["release_decision"],"HOLD")
    def test_45_page_refs_are_review_only(self):
        p=self.p
        items=p["items"]
        self.assertEqual(len(items),45)
        self.assertEqual([r["pdp_code"] for r in items],
                         [f"SCI-Y3-PDP-{i:03d}" for i in range(1,46)])
        self.assertEqual(len({r["sp_code"] for r in items}),45)
        self.assertEqual(p["counts"],{"tagged_sp_evidence":44,
                                      "toc_heading_only":1,"unresolved":0})
        self.assertFalse(p["db_write_allowed"])
        self.assertEqual(p["release_decision"],"HOLD")
        for r in items:
            self.assertTrue(r["printed_book_page_candidates"])
            self.assertTrue(all(1<=n<=138 for n in r["printed_book_page_candidates"]))
            self.assertEqual(r["teacher_approval"],"PENDING")
            self.assertEqual(r["visual_layout_check"],"PENDING")
            self.assertFalse(r["final_textbook_ref_in_database"])
    def test_3_missing_sp_are_not_invented_new_pdp(self):
        self.assertEqual({x["sp"] for x in self.p["missing_source_sp_pages"]},
                         {"3.2.5","3.3.3","3.3.4"})
        self.assertEqual(self.p["items"][43]["source_evidence"],
                         "BT_CONTENTS_HEADING_NOT_SP_TAG")
if __name__=="__main__":unittest.main()
