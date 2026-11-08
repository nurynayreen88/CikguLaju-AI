"""All 696 proposed Pendidikan Islam RPH must have reviewable export fields."""
import unittest

from pi_696_rph_editor_export import gather, CRITICAL, HELD, academic_warning_codes
from pi_quality_audit import COUNT, REQUIRED


class PIFullRPHReviewerExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=gather()

    def test_all_696_without_duplicate_or_loss(self):
        rows=self.rows
        self.assertEqual(len(rows),696)
        self.assertEqual(len({x["record"]["id"] for x in rows}),696)
        self.assertEqual({year:sum(x["record"]["tahun"]==year for x in rows)
                          for year in COUNT},COUNT)
        for row in rows:
            ident=row["record"]["id"]
            fields=row["record"]["fields"]
            self.assertTrue(all(isinstance(fields.get(k),str) and fields[k].strip()
                                for k in REQUIRED),ident)
            self.assertIn("1.",fields["aktiviti_utama"])
            self.assertIn("2.",fields["aktiviti_utama"])
            self.assertTrue(fields["penutup"])
            self.assertTrue(fields["bahan"])

    def test_export_risks_do_not_disappear_when_a4_passes(self):
        from collections import Counter
        rows = self.rows
        codes_by_id = {item["record"]["id"]:
                       academic_warning_codes(item, 1) for item in rows}
        counts = Counter(code for codes in codes_by_id.values() for code in codes)
        self.assertEqual(counts["ACADEMIC_AND_JAWI_APPROVAL_PENDING"], 696)
        self.assertEqual(counts["SOURCE_RECORD_WITHHELD_EDITOR_CANDIDATE_ONLY"], 6)
        self.assertEqual(counts["CRITICAL_HADITH_OR_TASMI_SOURCE_HOLD"], 3)
        self.assertEqual(counts["ORIGINAL_RPT_SURAH_LABEL_ERROR_PENDING"], 7)
        self.assertEqual(counts["ORIGINAL_RPT_YEAR4_PUASA_SIX_RUKUN_ERROR_PENDING"], 1)
        self.assertEqual(counts["ORIGINAL_RPT_YEAR3_SOLAT_OBJECTIVE_SEQUENCE_ERROR_PENDING"], 1)
        self.assertEqual(counts["YEAR5_BUKU_AKTIVITI_EDITION_AND_EXERCISE_UNVERIFIED"], 13)
        self.assertEqual(counts["ORIGINAL_RPT_YEAR6_JUZ25_67_AYAT_UNMAPPED"], 7)
        self.assertEqual(counts["ORIGINAL_RPT_YEAR2_AYAH224_OVERLAP_UNRESOLVED"], 1)
        self.assertIn("ORIGINAL_RPT_YEAR4_PUASA_SIX_RUKUN_ERROR_PENDING",
                      codes_by_id["T4-L107"])
        self.assertIn("CRITICAL_HADITH_OR_TASMI_SOURCE_HOLD",
                      codes_by_id["T4-L083"])
        self.assertIn("SOURCE_RECORD_WITHHELD_EDITOR_CANDIDATE_ONLY",
                      codes_by_id["T2-L035"])
        self.assertNotIn("PDF_LAYOUT_NOT_ONE_PAGE", codes_by_id["T4-L107"])
        two_page = next(x for x in rows if x["record"]["id"] == "T4-L107")
        self.assertIn("PDF_LAYOUT_NOT_ONE_PAGE", academic_warning_codes(two_page, 2))

    def test_held_and_critical_never_claim_to_be_ready(self):
        rows=self.rows
        held={x["record"]["id"] for x in rows
              if x["review_status"]=="ORIGINAL_HELD_EDITOR_CANDIDATE"}
        critical={x["record"]["id"] for x in rows
                  if x["review_status"]=="CRITICAL_SOURCE_HOLD"}
        self.assertEqual(held,HELD)
        self.assertEqual(critical,CRITICAL)
        self.assertEqual(sum(x["review_status"]=="UNVERIFIED_RPH_DRAFT"
                             for x in rows),687)
        self.assertEqual(sum(x["original_rumi_penutup"] is not None for x in rows),690)
        self.assertFalse(any("FINAL READY" in str(x["record"]) for x in rows))

if __name__=="__main__":
    unittest.main()
