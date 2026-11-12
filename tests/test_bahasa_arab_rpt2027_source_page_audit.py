"""Strict, source-faithful Arabic RPT2027 DSKP SP page evidence QA.

This validates verified PDF *locations*, not the accuracy of rendered Arabic
sentence text. Do not infer final academic approval or publish source OCR.
"""
import csv
import json
import re
import unittest
from collections import defaultdict
from pathlib import Path

from scripts.build_rpt_2027_remaining_four_subjects_staging import arabic_records

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "audits/bahasa_arab_rpt2027_y2_y6_117_sp_pdf_page_evidence_20261107.json"
INDEX = ROOT / "rpt_2027/bahasa_arab/rpt_2027_KUMPULAN_A_INDEKS_PDP_DRAF.csv"
EXPECTED_COUNTS = {2: 19, 3: 23, 4: 25, 5: 25, 6: 25}


class ArabicSPPageEvidenceQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(LEDGER.read_text(encoding="utf-8"))
        with INDEX.open(encoding="utf-8-sig", newline="") as f:
            cls.rpt = list(csv.DictReader(f))

    def test_pdf_pages_cover_all_98_year3to6_unique_sp_codes(self):
        actual = defaultdict(set)
        for row in self.rpt:
            actual[int(row["tahun"])].add(row["sp"].strip())
        self.assertEqual({y: len(v) for y, v in actual.items()}, EXPECTED_COUNTS)
        self.assertEqual(self.data["status"], "STAGING_117_CODE_AND_PDF_PAGE_VERIFIED_ONLY")
        self.assertEqual(self.data["summary"]["year3to6_unique_codes"], 98)
        self.assertEqual(self.data["summary"]["full_arabic_statement_signoffs"], 0)
        indexed_years = {x["year"]: x for x in self.data["years"]}
        self.assertEqual(set(indexed_years), {3, 4, 5, 6})
        for year in range(3, 7):
            with self.subTest(year=year):
                indexed = indexed_years[year]
                entries = indexed["entries"]
                codes = [x["sp_code"] for x in entries]
                self.assertEqual(len(codes), EXPECTED_COUNTS[year])
                self.assertEqual(set(codes), actual[year])
                self.assertEqual(len(set(codes)), len(codes))
                self.assertRegex(indexed["pdf_sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(indexed["pdf_page_count"], 40)
                for entry in entries:
                    self.assertRegex(entry["sp_code"], r"^\d+\.\d+\.\d+$")
                    self.assertGreaterEqual(entry["pdf_page"], 1)
                    self.assertLessEqual(entry["pdf_page"], indexed["pdf_page_count"])
                    self.assertIs(entry["statement_verified"], False)
                    self.assertEqual(entry["review_status"],
                                     "PDF_CODE_PAGE_LOCATED_NOT_TEXT_SIGNOFF")

    def test_year2_pdf_text_glyph_defect_not_treated_as_missing_standard(self):
        year2 = self.data["year2"]
        self.assertEqual(year2["unique_rpt_sp_codes"], len({
            row["sp"] for row in self.rpt if int(row["tahun"]) == 2}))
        self.assertIn("VISUALLY_LOCATED", year2["status"])
        self.assertRegex(year2["pdf_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(self.data["summary"]["year2_page_located"], 19)
        self.assertEqual(self.data["summary"]["all_year2to6_pdf_page_located"], 117)
        self.assertIs(self.data["summary"]["year2_visual_page_review"], True)
        page_map = {e["sp_code"]: e for e in year2["entries"]}
        year2_rpt_codes = {row["sp"] for row in self.rpt if int(row["tahun"]) == 2}
        self.assertEqual(set(page_map), year2_rpt_codes)
        self.assertEqual(len(page_map), 19)
        for code, entry in page_map.items():
            self.assertGreaterEqual(entry["pdf_page"], 31)
            self.assertLessEqual(entry["pdf_page"], 38)
            self.assertIs(entry["statement_verified"], False)
            self.assertEqual(entry["review_status"],
                             "PDF_CODE_PAGE_LOCATED_BY_VISUAL_NOT_TEXT_SIGNOFF")

    def test_pdf_location_evidence_cannot_automatically_unlock_rpt(self):
        for year in range(2, 7):
            records = arabic_records(year)
            expected = {2: 60, 3: 60, 4: 58, 5: 60, 6: 60}[year]
            self.assertEqual(len(records), expected)
            for row in records:
                if year == 2:
                    self.assertIn("Pernyataan penuh SK belum dipadankan",row["sk_display"])
                    self.assertNotIn("Pernyataan penuh SP belum dipadankan",row["sp_display"])
                    self.assertIn("القدرة",row["sp_display"])
                    self.assertTrue(row["source_pdf_extraction_code_repeated_unreliable"])
                    self.assertFalse(row["source_sp_dskp_text_signoff"])
                elif year in (3,4,5):
                    self.assertIn("Pernyataan penuh SK belum dipadankan",row["sk_display"])
                    self.assertNotIn("Pernyataan penuh SP belum dipadankan",row["sp_display"])
                    self.assertIn("القدرة",row["sp_display"])
                    self.assertTrue(row["source_arabic_orthography_normalized_not_visual_signoff"])
                    self.assertFalse(row["source_sp_dskp_text_signoff"])
                else:
                    self.assertNotIn("Pernyataan penuh",row["sk_display"])
                    self.assertNotIn("Pernyataan penuh",row["sp_display"])
                    self.assertIn("القدرة",row["sp_display"])
                    self.assertTrue(row["source_sk_opening_not_full_thematic_examples"])
                    self.assertTrue(row["source_arabic_orthography_normalized_not_visual_signoff"])
                    self.assertFalse(row["source_sp_dskp_text_signoff"])
                self.assertFalse(row.get("week"))
                self.assertFalse(row.get("a_start"))
                self.assertIn("DSKP SP PDF hlm ", row["note"])
                self.assertIn("teks belum disahkan", row["note"])
                self.assertIsInstance(row["source_sp_dskp_pdf_page"], int)
                page_source = self.data["year2"] if year == 2 else next(
                    x for x in self.data["years"] if x["year"] == year)
                matches = [e["pdf_page"] for e in page_source["entries"]
                           if e["sp_code"] == row["sp"]]
                self.assertEqual(matches, [row["source_sp_dskp_pdf_page"]])


if __name__ == "__main__":
    unittest.main()
