"""Matematik v57 — academic HOLD and 34 Year4 split pairs, RPH ONLY.

This GitHub test validates the small audit manifest. The separate 15-test
offline script uses the real ZIP (not committed to public repository).
"""
import csv
import json
import unittest
from pathlib import Path
from rph_standalone.matematik import staging_preview_v57 as preview
AUD=Path(__file__).resolve().parents[1]/"audits"

class V57Year4PairStaging(unittest.TestCase):
    def test_release_gate_exact_hash_and_counts(self):
        gate=json.loads((AUD/"matematik_v57_release_gate_RPH_only_20261107.json").read_text(encoding="utf8"))
        self.assertEqual(gate["archive_sha256"],"07bada94723bde54d958c11fcdfc3e46b06e59aefbcf63e26926144365331332")
        self.assertEqual(preview.EXPECTED_SHA256,gate["archive_sha256"])
        self.assertEqual(gate["archive_bytes"],48927660)
        self.assertEqual(gate["rph_total"],585)
        self.assertEqual(gate["year4_34_pairs_total"],34)
        self.assertEqual(gate["pairs_with_duplicate_intro_before"],32)
        self.assertEqual(gate["pairs_with_duplicate_intro_after"],0)
        self.assertEqual(gate["changed_second_session_intros"],32)
        self.assertEqual(gate["changed_first_session_intros"],1)
        self.assertEqual(gate["changed_rph"],33)
        self.assertEqual(gate["changed_sections"],33)
        self.assertEqual(gate["unchanged_rph"],552)
        self.assertEqual(gate["individual_pdf_A4_one_page_count"],585)
        self.assertEqual(gate["word_docx_count"],585)
        self.assertEqual(gate["markdown_count"],585)
        self.assertEqual(gate["merged_pdf_count"],5)
        self.assertEqual(gate["year4_merged_pages"],117)
    def test_source_34_original_pair_locator_entries(self):
        with (AUD/"matematik_v48_34_pasangan_T4_DSKP_20261107.csv").open(encoding="utf8",newline="") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),34)
        self.assertEqual(len({r["source_id"] for r in rows}),34)
        self.assertTrue(all(r["dskp_SP_found"]=="YES" for r in rows))
        self.assertTrue(all(r["item_level_book_verified"]=="NO" for r in rows))
        self.assertTrue(all(r["academic_signoff"]=="PENDING" for r in rows))
    def test_never_final_ready_or_modify_rpt(self):
        gate=json.loads((AUD/"matematik_v57_release_gate_RPH_only_20261107.json").read_text(encoding="utf8"))
        self.assertEqual(gate["item_level_book_exercises_verified"],0)
        self.assertEqual(gate["teacher_academic_formal_signoffs"],0)
        for field in ("final_ready","full_academic_ready","telegram_web_real_staging_e2e",
                      "rpt_changed","production_modified"):
            self.assertIs(gate[field],False)
        self.assertIn("RPH",gate["scope"])
        self.assertIn("out of scope",gate["scope"])
if __name__=="__main__":
    unittest.main()
