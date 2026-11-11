"""Matematik v56: RPH Years 5+6 scope, archive hash and release hold.

Offline ZIP tests run separately against actual archive and are NOT counted as
GitHub runner E2E, because the large ZIP is not committed to the repository.
"""
import json
import unittest
from pathlib import Path
from rph_standalone.matematik import staging_preview_v56 as preview

ROOT=Path(__file__).resolve().parents[1]/"audits"
SHA="f6c50114698826060bac92355ca1e476e9bf6ca921785cd0b2138e935b773695"

class V56IntroAndHold(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate=json.loads((ROOT/"matematik_v56_release_gate_RPH_only_20261107.json").read_text(encoding="utf-8"))

    def test_counts_explicit_and_585_stable(self):
        a=self.gate
        self.assertEqual(a["rph_total"],585)
        self.assertEqual(a["changed_year5_rph"],70)
        self.assertEqual(a["changed_year6_rph"],106)
        self.assertEqual(a["changed_rph"],176)
        self.assertEqual(a["unchanged_rph"],409)
        self.assertEqual(a["changed_rph"]+a["unchanged_rph"],585)
        self.assertEqual(a["year5_generic_after"],0)
        self.assertEqual(a["year6_generic_after"],0)
        self.assertEqual(a["PDF_one_page_A4_count"],585)
        self.assertEqual(a["DOCX_count"],585)
        self.assertEqual(a["Markdown_count"],585)
        self.assertEqual(a["merged_PDF_count"],5)
        self.assertEqual(a["merged_each_page_count"],117)

    def test_expected_hash_pinned_and_preview_isolated(self):
        a=self.gate
        self.assertEqual(a["archive_sha256"],SHA)
        self.assertEqual(preview.EXPECTED_SHA256,SHA)
        self.assertEqual(a["archive_bytes"],48930951)
        self.assertEqual(a["source_sha256"],"3913f179aa5690b8c2b550c5cb65c87aac16157f38db9f1001cb9c2fa9784d7e")
        self.assertEqual(a["actual_zip_offline_tests_passed"],12)
        self.assertTrue(a["complete_change_ledger_embedded"].startswith("AUDIT/V56_"))
        self.assertEqual(a["archive_crc"],"PASS")

    def test_rpt_unmodified_production_unmodified_and_academic_hold(self):
        a=self.gate
        self.assertEqual(a["BA_year2_3_ref_count"],234)
        self.assertEqual(a["teacher_formal_signoffs"],0)
        self.assertFalse(a["complete_exercise_level_validation"])
        self.assertFalse(a["year4_34_book_pairs_validated"])
        self.assertFalse(a["real_telegram_web_staging_e2e"])
        self.assertFalse(a["rpt_changed"])
        self.assertFalse(a["production_modified"])
        self.assertFalse(a["final_ready"])
        self.assertIn("RPH",a["scope"])
        self.assertIn("out of scope",a["scope"])

if __name__=="__main__":
    unittest.main()
