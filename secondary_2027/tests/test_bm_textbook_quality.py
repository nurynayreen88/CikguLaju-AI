"""Secondary BM textbook crosswalk QA: no network, no runtime changes."""
import json
import unittest
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
INDEX = DATA / "bm_t4_t5_textbook_sp_102_anchor_index.json"
PACKS = {
    4: ("bm_t4_dskp_54sp_108rph_draft.json", 54, 108, 22),
    5: ("bm_t5_dskp_48sp_96rph_draft.json", 48, 96, 24),
}

class TestBookAnchorIntegrity(unittest.TestCase):
    def test_book_index_codes(self):
        index=json.loads(INDEX.read_text(encoding="utf-8"))
        self.assertEqual(index["source"]["4"]["page_offset"],22)
        self.assertEqual(index["source"]["5"]["page_offset"],24)
        self.assertEqual(index["source"]["5"]["codes"]["1.1.1"],[3,"Cergaskan Dirimu"])
        for form,(_,num_sp,_,offset) in PACKS.items():
            src=index["source"][str(form)]
            self.assertEqual(src["page_offset"],offset)
            self.assertEqual(len(src["codes"]),num_sp)
            for sp,(page,title) in src["codes"].items():
                self.assertTrue(sp.count(".")==2)
                self.assertGreater(page,0)
                self.assertTrue(title.strip())

    def test_all_204_drafts_match_book_source(self):
        index=json.loads(INDEX.read_text(encoding="utf-8"))
        for form,(filename,num_sp,num_rph,offset) in PACKS.items():
            source=index["source"][str(form)]
            pack=json.loads((DATA/filename).read_text(encoding="utf-8"))
            self.assertEqual(pack["rph_count"],num_rph)
            self.assertFalse(pack["usable_in_runtime"])
            self.assertNotEqual(pack["release_status"],"READY")
            self.assertEqual({x["sp"] for x in pack["lessons"]},set(source["codes"]))
            for i,r in enumerate(pack["lessons"],1):
                with self.subTest(form=form,pdp=i):
                    self.assertEqual(r["pdp"],i)
                    self.assertEqual(r["status"],pack["release_status"])
                    page,title=source["codes"][r["sp"]]
                    self.assertEqual(r["source_book"]["title"],title)
                    self.assertEqual(r["source_book"]["printed_page"],page)
                    self.assertEqual(r["source_book"]["pdf_page"],page+offset)
                    self.assertEqual(r["source_book"]["file_id"],source["drive_file_id"])
                    self.assertEqual(r["tajuk"],title)
                    self.assertIn(f"m/s {page}",r["bahan"])
                    self.assertIn(title,r["aktiviti_1"])
                    self.assertIn(title,r["aktiviti_2"])
                    self.assertIn("RPT_SEQUENCE_UNVERIFIED",r["review_flags"])
                    self.assertIn("ACTIVITIES_REQUIRE_MANUAL_BOOK_QA",r["review_flags"])
                    self.assertGreater(len(r["aktiviti_1"]),110)
                    self.assertGreater(len(r["aktiviti_2"]),110)

if __name__=="__main__":
    unittest.main()
