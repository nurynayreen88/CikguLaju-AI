import unittest
from pathlib import Path

from pjpk_rpt_page_evidence_v2677 import lookup_page_evidence


ROOT = Path(__file__).resolve().parents[1]


class TestPjpkRptPageEvidenceV2677(unittest.TestCase):
    def test_year1_rpt_page_reference(self):
        result = lookup_page_evidence(
            "Tahun 1", "Pendidikan Jasmani", "Unit 1: Gerak Ceria", "Gerak Ruang", ROOT
        )
        self.assertIn(result["status"], {"RPT_PAGE_REFERENCE_ONLY", "RPT_MULTIPLE_PAGE_REFERENCES_REVIEW"})
        self.assertIn("3", result["pages"])
        self.assertIn("1.1.2", result["rpt_sp_codes"])

    def test_year5_rpt_page_reference(self):
        result = lookup_page_evidence(
            "Tahun 5", "Pendidikan Jasmani", "Unit 1: Jadi Yang Terbaik", "Mengimbang", ROOT
        )
        self.assertIn(result["status"], {"RPT_PAGE_REFERENCE_ONLY", "RPT_MULTIPLE_PAGE_REFERENCES_REVIEW"})
        self.assertIn("2", result["pages"])

    def test_subject_and_year_are_never_crossed(self):
        result = lookup_page_evidence(
            "Tahun 1", "Pendidikan Kesihatan", "Unit 1: Gerak Ceria", "Gerak Ruang", ROOT
        )
        self.assertEqual(result["status"], "SOURCE_TEXT_NOT_AVAILABLE")
        result = lookup_page_evidence(
            "Tingkatan 1", "Pendidikan Jasmani", "Unit 1", "Gerak Ruang", ROOT
        )
        self.assertEqual(result["status"], "SOURCE_SCOPE_INVALID")

    def test_all_six_pj_rpt_sources_exist(self):
        for year in range(1, 7):
            path = ROOT / "curriculum_sources" / "pjpk" / f"rpt_pj_tahun_{year}_2026_extracted.txt"
            self.assertTrue(path.is_file(), str(path))
            self.assertGreater(path.stat().st_size, 10000)


if __name__ == "__main__":
    unittest.main()
