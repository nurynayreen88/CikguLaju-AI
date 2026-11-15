"""Exact 13 source-linked editor fixes; no official BA invented."""
import hashlib
import unittest
from pi_y5_khat_nasakh_editor_overlay import generate, LETTER, WORD, UPDATED, SHEET

class PIY5KhatOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=generate()

    def test_13_activities_and_pbd_pedagogically_matched(self):
        r=self.data
        self.assertEqual(r["source_rph_count"],143)
        self.assertEqual(r["editor_proposed_improvements"],13)
        self.assertEqual(r["sp_source_corrected_prior_to_overlay"],4)
        self.assertEqual(r["editor_changed_field_count"],30)
        self.assertEqual(r["original_activity_book_mentions_retained_in_provenance"],13)
        self.assertEqual(r["preview_unsupported_official_activity_book_mentions"],0)
        self.assertEqual(r["new_source_verified_workbook_pages"],0)
        self.assertEqual(r["release"],"NO_GO")
        self.assertEqual({x["id"] for x in r["rows"]},LETTER|WORD|UPDATED)
        self.assertEqual(sum(x["type"]=="AYAT_DAN_TEKAL" for x in r["rows"]),4)

    def test_source_unchanged_and_no_fake_book_claim(self):
        for row in self.data["rows"]:
            self.assertFalse(row["can_publish"])
            self.assertFalse(row["jawi_spelling_approved"])
            self.assertFalse(row["academic_content_approved"])
            self.assertFalse(row["source_catalog_overwritten"])
            self.assertTrue(row["teacher_prepared_worksheet_only"])
            self.assertFalse(row["official_buku_aktiviti_edition_or_page_confirmed"])
            self.assertEqual(row["source_sp_unchanged"],row["revised_fields"]["sp"])
            self.assertEqual(row["source_objective_unchanged"],row["revised_fields"]["objektif"])
            self.assertIn(SHEET,row["revised_fields"]["pentaksiran"])
            self.assertNotIn("بوكو اكتيۏيتي",row["revised_fields"]["pentaksiran"])
            self.assertNotIn("بوكو اكتيۏيتي",row["revised_fields"]["aktiviti_utama"])
            self.assertIn("Pen khat",row["revised_fields"]["bahan"])
            for field,item in row["changes"].items():
                self.assertEqual(row["original_fields"][field],item["before"])
                self.assertEqual(row["revised_fields"][field],item["after"])
                self.assertEqual(hashlib.sha256(item["before"].encode("utf-8")).hexdigest(),
                                 item["before_sha256"])
            if row["id"] in LETTER:
                self.assertEqual(row["type"],"HURUF")
                self.assertIn("حروف",row["revised_fields"]["pentaksiran"])
                self.assertIn(row["source_examples_from_sp"],row["revised_fields"]["pentaksiran"])
            elif row["id"] in WORD:
                self.assertEqual(row["type"],"PERKATAAN")
                self.assertIn("ڤركاتاءن",row["revised_fields"]["pentaksiran"])
                self.assertIn(row["source_examples_from_sp"],row["revised_fields"]["pentaksiran"])
            else:
                self.assertEqual(row["type"],"AYAT_DAN_TEKAL")
                self.assertIn("7.2.5",row["source_sp_unchanged"])
                self.assertIn("7.2.6",row["source_sp_unchanged"])
                self.assertIn("7.2.6",row["revised_fields"]["pentaksiran"])
                self.assertEqual(len(row["revised_fields"]["aktiviti_utama"].splitlines()),3)

if __name__=="__main__":unittest.main()
