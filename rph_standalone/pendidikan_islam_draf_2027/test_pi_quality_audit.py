"""Regression checks for isolated Pendidikan Islam staging QA."""
import unittest
from pi_quality_audit import audit, HELD, COUNT


class PIQualityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit()

    def test_no_loss_no_release_no_fake_score(self):
        r = self.result
        self.assertEqual(r["total"], sum(COUNT.values()))
        self.assertEqual(r["drafts"], 690)
        self.assertEqual(r["held"], 6)
        self.assertEqual(r["release"], "NO_GO")
        self.assertIsNone(r["quality_score_percent"])
        self.assertIs(r["quality_80_certified"], False)

    def test_numbering_fixed_without_unlocking_holds(self):
        flags = self.result["flags"]
        self.assertNotIn("NOMBOR_AKTIVITI_TIDAK_BERMULA_1", flags)
        for year, lesson in HELD:
            row = next(x for x in self.result["records"] if x["id"] == f"T{year}-L{lesson:03}")
            self.assertEqual(row["flags"], ["TAHAN_KANDUNGAN"])
        self.assertEqual(flags["TAHAN_KANDUNGAN"], 6)

    def test_remaining_short_content_is_not_masked(self):
        r = self.result
        self.assertEqual(r["short_activity_count"], 0)
        self.assertEqual(r["expanded_activity_draft_count"], 560)
        self.assertEqual(r["critical_source_review_count"], 3)
        self.assertEqual(r["t6_tasmi_rpt_editorial_range_review_count"],2)
        self.assertEqual(r["t6_sp42_edited_kbat_review_count"],1)
        self.assertEqual(r["textbook_page_range_overrun_count"], 3)
        bad_page = sorted(x["id"] for x in r["records"]
                          if "HALAMAN_BUKU_T2_MELEBIHI_MUKA_TERAKHIR" in x["flags"])
        self.assertEqual(bad_page, ["T2-L102", "T2-L105", "T2-L108"])
        self.assertAlmostEqual(r["mechanical_three_step_coverage_percent"], 100.0, places=2)
        self.assertEqual(sum(r["domain_counts"].values()), 696)
        self.assertGreater(r["flags"].get("RUJUKAN_HALAMAN_BELUM_DISAHKAN", 0), 0)

    def test_specific_pbd_is_not_confused_with_expert_approval(self):
        r = self.result
        self.assertEqual(r["generic_pbd_count"], 0)
        self.assertEqual(r["generic_pbd_by_year"],
                         {"2": 0, "3": 0, "4": 0, "5": 0, "6": 0})
        self.assertEqual(r["refined_pbd_review_count"], 43)
        self.assertEqual(r["refined_pbd_review_by_year"],
                         {"2": 14, "3": 29, "4": 0, "5": 0, "6": 0})
        self.assertEqual(r["flags"]["PBD_SP_SASARAN_BELUM_DISAH_PAKAR"], 43)
        self.assertNotIn("PBD_TIDAK_KHUSUS_KEPADA_SP", r["flags"])
        self.assertIsNone(r["quality_score_percent"])

    def test_unverified_activity_book_mentions_get_flags_without_approval(self):
        r = self.result
        self.assertEqual(r["unverified_year4_to6_activity_book_wording_count"], 13)
        ids = [x["id"] for x in r["records"] if
               "BUKU_AKTIVITI_T4_T6_KESAHIHAN_SUMBER_BELUM_DISAHKAN" in x["flags"]]
        self.assertEqual(ids, [f"T5-L{n:03}" for n in
                              (92,96,100,104,111,115,119,123,127,131,135,139,143)])
        self.assertIsNone(r["quality_score_percent"])

    def test_script_consistency_requires_review_not_transliteration(self):
        r = self.result
        self.assertEqual(r["closing_rumi_consistency_review_count"], 690)
        self.assertEqual(r["flags"]["PENUTUP_RUMI_SEMAK_PENYERAGAMAN_JAWI"], 690)
        self.assertIsNone(r["quality_score_percent"])

    def test_source_blockers_are_explicit_not_silently_approved(self):
        blocked = sorted(row["id"] for row in self.result["records"]
                         if "SUMBER_KRITIKAL_BELUM_LENGKAP" in row["flags"])
        self.assertEqual(blocked, ["T4-L083", "T6-L137", "T6-L141"])
        self.assertEqual(self.result["release"], "NO_GO")
        self.assertIsNone(self.result["quality_score_percent"])

    def test_document_content_still_unapproved(self):
        self.assertEqual(self.result["flags"]["PENAMBAHAN_PDP_BELUM_SAH_PAKAR"], 560)
        self.assertIs(self.result["quality_80_certified"], False)


if __name__ == "__main__":
    unittest.main()
