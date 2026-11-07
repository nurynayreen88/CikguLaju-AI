"""Ensure the Sains release gate never confuses structural QA with teacher READY."""
import csv
import json
import unittest
from collections import Counter
from tools.audit_sains_342_pdp_release_gate_20261106 import (
    analyze, AUDIT_DIR, EXPECTED
)

class Science342ReleaseGateTests(unittest.TestCase):
    def test_every_pdp_has_an_explicit_hold_reason(self):
        rows,summary=analyze()
        self.assertEqual(len(rows),342)
        self.assertEqual(summary["decision"],"HOLD")
        self.assertEqual(summary["academically_approved"],0)
        self.assertEqual(summary["standalone_rph_year3_draft"],45)
        self.assertEqual(summary["standalone_rph_remaining_unverified"],297)
        self.assertTrue(summary["non_destructive"])
        ids=[row["pdp_code"] for row in rows]
        self.assertEqual(len(set(ids)),342)
        groups=Counter(row["tahun"] for row in rows)
        self.assertEqual(groups,Counter(EXPECTED))
        for row in rows:
            self.assertEqual(row["keputusan"],"HOLD")
            self.assertEqual(row["uji_telegram_web"],"NOT_TESTED")
            self.assertEqual(row["status_tarikh_rpt"],"BELUM_DIJADUAL")
            self.assertEqual(row["kelulusan_akademik"],"PENDING")
            self.assertIn("TEACHER_ACADEMIC_APPROVAL_MISSING",row["isu"])
            if row["tahun"]==3:
                self.assertEqual(row["rph_word_pdf"],"DRAF_YEAR3_ONLY")
            else:
                self.assertEqual(row["rph_word_pdf"],"NOT_VERIFIED")
                self.assertIn("RPH_STANDALONE_UNVERIFIED",row["isu"])
            if row["tahun"]==6:
                self.assertIn("DSKP_YEAR6_PUBLIC_MIRROR_NOT_OWNER_ORIGINAL",row["isu"])
    def test_export_complete_and_preserves_holds(self):
        with (AUDIT_DIR/"SAINS_342_PDP_RELEASE_GATE_DRAF.csv").open(
                encoding="utf-8-sig",newline="") as f:
            rows=list(csv.DictReader(f))
        summary=json.loads((AUDIT_DIR/"SUMMARY_HOLD.json").read_text(encoding="utf-8"))
        self.assertEqual(len(rows),342)
        self.assertEqual({row["keputusan"] for row in rows},{"HOLD"})
        self.assertEqual(summary["checked_pdp"],342)
        self.assertEqual(set(summary["years"]),{str(n) for n in EXPECTED})
if __name__=="__main__":unittest.main()
