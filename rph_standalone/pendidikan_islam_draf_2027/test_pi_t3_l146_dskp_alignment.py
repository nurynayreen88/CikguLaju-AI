"""Verify cautious Year3 L146 curriculum alignment without expert approval."""
import json
from pathlib import Path
import unittest

from pi_quality_audit import audit, ROOT
from pi_content_review_queue import build_queue


class PIT3L146DSKPAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cat=json.loads((Path(ROOT)/"year3.json").read_text(encoding="utf-8"))
        cls.row=cat["records"][145]

    def test_exact_sp_codes_and_three_objectives(self):
        row=self.row
        self.assertEqual(row["id"],"T3-L146")
        fields=row["fields"];meta=row["staging_dskp_l146_alignment"]
        self.assertTrue(all(code in fields["sp"] for code in ("6.4.3","6.4.4","6.4.5")))
        self.assertIn("6.4.4 مروموس كڤنتيڠن",fields["sp"])
        self.assertIn("6.4.5 مڠعملكن سنة رسول الله",fields["sp"])
        self.assertIn("2. مثنارايكن كڤنتيڠن",meta["original_objektif"])
        self.assertIn("2. مروموس كڤنتيڠن",fields["objektif"])
        self.assertIn("3. مڠعملكن ساتو سنة رسول الله",fields["objektif"])
        self.assertNotIn("2. مثنارايكن كڤنتيڠن",fields["objektif"])
        self.assertEqual(len([x for x in fields["aktiviti_utama"].splitlines()
                              if x[:1].isdigit()]),4)
        self.assertIn("4. موريد ممڤراݢاكن",fields["aktiviti_utama"])
        self.assertEqual((meta["dskp_pdf_page"],meta["dskp_printed_page"]),(51,39))
        self.assertEqual(meta["source_sp_codes"],["6.4.3","6.4.4","6.4.5"])

    def test_offtopic_old_pbd_preserved_in_audit_not_current(self):
        row=self.row;fields=row["fields"]
        meta=row["staging_dskp_l146_alignment"]
        self.assertIn("بخيل",meta["original_pentaksiran"])
        self.assertIn("برشكور",meta["original_pentaksiran"])
        self.assertNotIn("بخيل",fields["pentaksiran"])
        self.assertNotIn("برشكور",fields["pentaksiran"])
        for item in ("منرڠكن","مروموس","ممڤراݢاكن","سناراي سمق"):
            self.assertIn(item,fields["pentaksiran"])
        self.assertTrue(meta["original_aktiviti_utama"])
        self.assertIs(meta["source_sk_sp_unchanged"],True)
        for status in ("content_expert_approved","jawi_orthography_approved",
                       "native_word_pdf_visual_approved"):
            self.assertIs(meta[status],False)
        self.assertEqual(meta["publication"],"HOLD")
        self.assertIs(row["verified_ready"],False)

    def test_explicit_quality_flag_and_review_queue(self):
        q=audit()
        self.assertEqual(q["dskp_l146_alignment_editorial_review_count"],1)
        quality=next(r for r in q["records"] if r["id"]=="T3-L146")
        self.assertIn("DSKP_T3_L146_OBJECTIVE_PBD_REVISED_EXPERT_PENDING",
                      quality["flags"])
        queue=build_queue()
        r=next(x for x in queue["rows"] if x["id"]=="T3-L146")
        self.assertEqual(r["priority"],"P2_PBD_OR_PAGE")
        self.assertIn("6.4.3",r["editor_next_step"])
        self.assertIn("Jawi belum diluluskan",r["editor_next_step"])
        self.assertIs(r["can_publish"],False)
        self.assertEqual(r["release"],"NO_GO")


if __name__=="__main__":
    unittest.main()
