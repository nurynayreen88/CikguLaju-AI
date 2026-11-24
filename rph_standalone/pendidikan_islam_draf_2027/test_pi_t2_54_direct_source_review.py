"""Two scoped source-supported Jawi/SP corrections, no automatic teacher READY."""
import unittest
from pi_t2_54_direct_source_review import (
    audit, SP_BOOK_FOOTER_PAGES, LESSON_CODES,
    TEXTBOOK_SHA256, DSKP_SHA256
)


class PIYear2DSKP54DirectEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit()

    def test_exact_page_correlation_to_dskp_and_original_textbook(self):
        v = self.result
        self.assertEqual(v["directly_cross_checked_lesson_count"], 3)
        self.assertEqual(v["sp_543_jawi_wording_corrections"], 2)
        self.assertEqual(v["staging_rph_material_book_page_references_added"],3)
        self.assertEqual(v["book_sp_footer_page_evidence_count"], 5)
        self.assertEqual(v["dskp_sp_codes_observed"], ["5.4.1","5.4.2","5.4.3","5.4.4"])
        self.assertEqual(v["book_page_to_pdf_offset"],10)
        self.assertEqual(SP_BOOK_FOOTER_PAGES["5.4.1"],[134,137,138])
        self.assertEqual(SP_BOOK_FOOTER_PAGES["5.4.2"],[134,138])
        self.assertEqual(SP_BOOK_FOOTER_PAGES["5.4.3"],[135,137])
        self.assertEqual(SP_BOOK_FOOTER_PAGES["5.4.4"],[136,138])
        self.assertEqual(set(x["id"] for x in v["rows"]),set(LESSON_CODES))
        self.assertEqual(v["dskp_sha256"],DSKP_SHA256)
        self.assertEqual(v["textbook_sha256"],TEXTBOOK_SHA256)

    def test_staging_sp_fix_does_not_approve_lesson(self):
        v=self.result
        self.assertEqual(v["lesson_specific_activity_approvals"],0)
        self.assertEqual(v["jawi_expert_approvals"],0)
        self.assertIsNone(v["academic_quality_score"])
        self.assertIs(v["can_publish"],False)
        self.assertEqual(v["release"],"NO_GO")
        affected={x["id"] for x in v["rows"] if x["dskp_543_adab_adab_wording_corrected"]}
        self.assertEqual(affected,{"T2-L105","T2-L108"})
        for r in v["rows"]:
            self.assertEqual(len(r["source_supported_material_reference_pages"].split("|")),
                             1 if r["id"]=="T2-L102" else 2)
            self.assertIs(r["source_original_material_line_preserved"],True)
            self.assertIs(r["verified_book_sp_footer_correspondence"],True)
            self.assertIs(r["original_sk_sp_preserved"],True)
            self.assertIs(r["original_objective_preserved"],True)
            for key in ("activity_exact_page_verified","jawi_editor_approved",
                        "content_expert_approved","rights_to_redistribute_book",
                        "can_publish"):
                self.assertIs(r[key],False)
            self.assertEqual(r["release"],"NO_GO")


if __name__=="__main__":
    unittest.main()
