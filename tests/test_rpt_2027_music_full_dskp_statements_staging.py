"""Regression guard for 175 Music RPT PdP's original SP and DSKP clauses.

This verifies exact code catalog coverage and display text provenance. The
original DSKP diagram/score graphics are NOT represented by plain text.
"""
from __future__ import annotations
import json
import re
import unittest
from pathlib import Path
from rpt_2027.common.music_dskp_full_statement_staging import _catalog, music_full_standard_display
from scripts.build_rpt_2027_remaining_four_subjects_staging import music_records, csv_rows

ROOT=Path(__file__).resolve().parents[1]
CATALOG_SIZES={2:20,3:22,4:19,5:20,6:18}

class MusicOriginalDSKPTextQA(unittest.TestCase):
    def test_source_code_sets_exact_99_unique_and_175_pdp(self):
        self.assertEqual(sum(CATALOG_SIZES.values()),99)
        for year,expect in CATALOG_SIZES.items():
            with self.subTest(year=year):
                catalog=_catalog(year)
                self.assertEqual(len(catalog),expect)
                records=music_records(year)
                raw=csv_rows(ROOT/"staging/pendidikan_muzik/rpt_rph_2027"/
                            f"year{year}"/f"RPT_MUZIK_TAHUN_{year}_2027_DRAF.csv")
                self.assertEqual(len(records),len(raw))
                self.assertEqual(len(records),35)
                all_codes=set()
                for row,orig in zip(records,raw):
                    codes=re.split(r"\s*[;/]\s*",row["sp"])
                    self.assertEqual(codes,
                                     re.split(r"\s*[;/]\s*",
                                              orig.get("SP DSKP",orig.get("SP",orig.get("Kod SP")))))
                    all_codes.update(codes)
                    self.assertTrue(all(code in catalog for code in codes))
                    self.assertEqual([x.split(" — ",1)[0] for x in row["sp_display"].splitlines()],
                                     codes)
                    self.assertEqual(row["sk_display"].split(" — ",1)[0], row["sk"].split(" / ")[0])
                    self.assertNotIn("Pernyataan penuh SP belum dipadankan", row["sp_display"])
                    self.assertFalse("READY" in str(row.get("source_status","")).upper() and
                                     "DRAF" not in str(row.get("source_status","")).upper())
                self.assertTrue(all_codes)
                # DSKP also includes two valid SP unused by this 35-PdP
                # RPT source; do not invent PdP just to consume them.
                unused = {2:{"2.3.1"},3:{"2.4.3"},4:set(),5:set(),6:set()}[year]
                self.assertEqual(set(catalog)-all_codes,unused)

    def test_year4_official_printed_numbering_discrepancy_is_visible(self):
        catalog=_catalog(4)
        for code in ("3.2.1","3.2.2","3.2.3"):
            self.assertEqual(catalog[code]["sk"],"3.1")
        self.assertEqual(catalog["4.2.1"]["sk"],"4.1")
        for code in ("3.2.2","4.2.1"):
            d=music_full_standard_display(4,code)
            self.assertIn("kekalkan konflik sumber",d["source_note"])
            self.assertTrue(d["sk"].startswith("3.1" if code.startswith("3.") else "4.1"))

    def test_figures_explicitly_require_original_musical_notation(self):
        for year in range(2,7):
            catalog=_catalog(year)
            diagrams=[x for x in catalog.values() if x["figure_or_score_required"]]
            self.assertTrue(diagrams)
            for d in diagrams:
                rendered=music_full_standard_display(year,d["code"])
                self.assertIn("rujuk rajah DSKP PDF hlm",rendered["source_note"])
                self.assertFalse(d.get("teacher_approval", False))

if __name__=="__main__":
    unittest.main()
