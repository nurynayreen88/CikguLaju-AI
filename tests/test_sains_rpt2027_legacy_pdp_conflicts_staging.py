"""Fail-closed KSSR2017 Sains per-PdP historical-code conflicts."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from scripts.audit_sains_rpt2027_legacy_pdp_conflicts_staging import audit,write_report
from scripts.build_rpt_2027_sains_342_actual_source_staging import EXPECTED

class HistoricSainsPdPWorkQueueQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=audit()

    def test_all_342_historical_pdp_remain_unapproved_and_flagged(self):
        a=self.audit
        self.assertFalse(a["ready_for_web_telegram"])
        self.assertEqual(a["production_db_writes"],0)
        self.assertEqual(a["all_legacy_sains_pdp_academic_signoffs"],0)
        self.assertEqual({int(y):d["historical_pdp_count"] for y,d in a["years"].items()},EXPECTED)
        for key,section in a["years"].items():
            year=int(key)
            self.assertEqual(section["unresolved_pdp"],section["historical_pdp_count"])
            self.assertFalse(section["release_ready"])
            if year in (4,5):
                self.assertTrue(section["official_code_membership_checked"])
                self.assertIsInstance(section["pdp_with_officially_absent_code"],int)
                self.assertEqual(section["pdp_with_officially_absent_code"],
                                 len(section["requires_reconciliation"]))
                self.assertEqual(section["pdp_with_code_present_but_full_pdp_signoff_missing"]
                                 + section["pdp_with_officially_absent_code"],
                                 section["historical_pdp_count"])
                self.assertEqual(section["pdp_with_official_sp_text_match"]
                                 + len(section["pdp_with_official_sp_text_mismatch"])
                                 + section["pdp_with_officially_absent_code"],
                                 section["historical_pdp_count"])
                self.assertEqual(section["pdp_with_official_sk_title_match"]
                                 + len(section["pdp_with_official_sk_title_mismatch"])
                                 + section["pdp_with_officially_absent_code"],
                                 section["historical_pdp_count"])
                self.assertEqual(section["source_text_visual_signoff_count"],0)
                self.assertEqual(len({r["source_pdp_code"] for r in section["requires_reconciliation"]}),
                                 len(section["requires_reconciliation"]))
                for r in section["requires_reconciliation"]:
                    self.assertFalse(r["academic_release_approved"])
                    self.assertEqual(r["year"],year)
            else:
                self.assertFalse(section["official_code_membership_checked"])
                self.assertIsNone(section["pdp_with_officially_absent_code"])
                self.assertEqual(section["requires_reconciliation"],[])

    def test_report_saved_separately_without_writing_db(self):
        with TemporaryDirectory() as d:
            report=write_report(Path(d)/"sains_conflicts_DRAF.json")
            data=json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data,self.audit)
            self.assertFalse(data["ready_for_web_telegram"])
            with self.assertRaises(ValueError):
                write_report(Path(d)/"FINAL.json")

if __name__=="__main__":
    unittest.main()
