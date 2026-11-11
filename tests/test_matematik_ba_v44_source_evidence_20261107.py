"""Staging-only mathematical audit v44: evidence-level gates.

No private BA/BT images and no proprietary 49MB ZIP are committed to GitHub.
"""
import csv
import json
from collections import Counter
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "audits"
def read(filename):
    with (ROOT / filename).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

class V44SourceEvidenceGate(unittest.TestCase):
    def test_351_textbook_sp_locations_are_not_exercise_approvals(self):
        rows = read("matematik_v44_351_lokasi_sp_buku_teks_20261107.csv")
        self.assertEqual(len(rows),351)
        self.assertEqual(Counter(x["year"] for x in rows),{"4":117,"5":117,"6":117})
        self.assertEqual(len({x["lesson_id"] for x in rows}),351)
        for x in rows:
            self.assertEqual(x["academic_approved"],"NO")
            self.assertEqual(x["evidence_level"],"SP_PDF_CODE_FOUND_ACTIVITY_NOT_CHECKED")
            self.assertGreater(int(x["audit_source_location_count"]),0)
            self.assertGreater(int(x["first_pdf_page_source_locator"]),0)

    def test_34_year4_splits_have_same_sp_but_distinct_steps(self):
        rows=read("matematik_v44_34_pasangan_tahun4_20261107.csv")
        self.assertEqual(len(rows),34)
        self.assertEqual(len({x["source_id"] for x in rows}),34)
        self.assertEqual(len({n for x in rows for n in (x["lesson_a"],x["lesson_b"])}),68)
        for x in rows:
            for k in ("same_sp","different_akt1","different_akt2","different_pbd"):
                self.assertEqual(x[k],"YES")
            self.assertEqual(x["academic_status"],"ACADEMIC_APPROVAL_PENDING")

    def test_360_equations_statuses_truthful_and_approved_zero(self):
        rows=read("matematik_v44_360_persamaan_audit_20261107.csv")
        self.assertEqual(len(rows),360)
        self.assertEqual(Counter(x["status"] for x in rows),{
            "ARITHMETIC_CONFIRMED":336,
            "CONTEXT_CONFIRMED_IN_ORIGINAL_MARKDOWN":24})
        proofs=read("matematik_v44_23_bukti_pengiraan_konteks_20261107.csv")
        self.assertEqual(len(proofs),23)
        for x in proofs:
            self.assertEqual(x["source_sentence_found"],"YES")
            self.assertEqual(x["math_exact"],"YES")

    def test_release_remains_staging_only_without_academic_signoff(self):
        p=ROOT/"matematik_v44_release_gate_20261107.json"
        gate=json.loads(p.read_text(encoding="utf8"))
        self.assertEqual(gate["rph_total"],585)
        self.assertEqual(gate["changed_lessons"],["T2-L087","T2-L088"])
        self.assertEqual(gate["year4_split_pairs_same_SP_distinct_steps"],34)
        self.assertEqual(gate["year4_to6_SP_found_in_textbook_pdf"],351)
        self.assertEqual(gate["arithmetic_assertions_screened"],360)
        self.assertEqual(gate["academic_exercise_level_approved"],0)
        self.assertFalse(gate["final_ready"])
        self.assertFalse(gate["production_modified"])
        self.assertFalse(gate["telegram_web_staging_live_tested"])

if __name__=="__main__":
    unittest.main()
