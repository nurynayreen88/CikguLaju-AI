"""Guard 64 RBT Y5–6 SP/page crosswalks and block accidental READY."""
from __future__ import annotations

import unittest

from scripts.audit_rbt_y5_y6_64_pdp_page_consistency_staging import run_audit
from rpt_2027.rbt.pdf_runtime import source_rows


class RBTYear5Year6BookMappingQA(unittest.TestCase):
    def test_64_pdp_rph_rpt_manifest_mapping(self):
        audit = run_audit()
        self.assertEqual(audit["pdps_verified_internal_only"], 64)
        self.assertEqual(audit["years"], {"5": 32, "6": 32})
        self.assertEqual(audit["unique_sp_by_year"], {"5": 34, "6": 23})
        self.assertEqual(audit["independent_book_page_checks_completed"], 0)
        self.assertEqual(audit["teacher_approvals"], 0)
        self.assertEqual(audit["release_ready_count"], 0)
        self.assertEqual(audit["status"], "STAGING_INTERNAL_CONSISTENCY_ONLY")
        self.assertEqual(len(audit["records"]), 64)
        for year in (5, 6):
            indexed = [r for r in audit["records"] if r["year"] == year]
            self.assertEqual([r["pdp"] for r in indexed], list(range(1, 33)))
            for r in indexed:
                self.assertFalse(r["teacher_approved"])
                self.assertFalse(r["activities_visual_verified"])
                self.assertEqual(r["source_book_page_verification"], "PENDING_INDEPENDENT")
                self.assertTrue(r["calon_halaman_bercetak_mengikut_sp"])
                self.assertTrue(all(x["muka_surat_bercetak_calon"] and len(x["muka_surat_bercetak_calon"]) == 2
                                    for x in r["calon_halaman_bercetak_mengikut_sp"]))

    def test_source_date_fields_remain_empty(self):
        for year in (5, 6):
            rows = source_rows(year)
            self.assertEqual(len(rows), 32)
            for r in rows:
                self.assertEqual(r["Kumpulan A tarikh"], "")
                self.assertEqual(r["Kumpulan B tarikh"], "")
                self.assertEqual(r["Status"], "DRAF")


if __name__ == "__main__":
    unittest.main()
