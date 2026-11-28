"""QA source-linked Sains 2027 342 PdP five-column PARTIAL RPT drafts."""
from __future__ import annotations
from collections import Counter
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest
import fitz

from scripts.build_rpt_2027_sains_342_actual_source_staging import (
    EXPECTED,source_records,build_all,_kssr2017_official_code_sets_y4_y5
)
from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks

class Science2027PartialRPTQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.yearly=source_records()

    def test_numbered_source_is_exactly_342_real_historical_pdp(self):
        self.assertEqual({y:len(records) for y,records in self.yearly.items()},EXPECTED)
        self.assertEqual(sum(map(len,self.yearly.values())),342)
        for year,rows in self.yearly.items():
            with self.subTest(year=year):
                self.assertEqual([r["id"] for r in rows],
                                 [f"{i:03d}" for i in range(1,len(rows)+1)])
                self.assertEqual(len({r["display_id"] for r in rows}),len(rows))
                self.assertTrue(all(r["source_status"] and
                                    r["week_allocation"]=="PROPOSED_2027_WEEK_NOT_TIMETABLE"
                                    for r in rows))
                self.assertTrue(all(r["raw_pdp_title"] and r["topic"] and
                                    r["sp_display"] and r["sk_display"] for r in rows))
                self.assertTrue(all("DRAF LEGACY:" in r["note"] and "BUKAN untuk digunakan guru" in r["note"] for r in rows))

    def test_342_legacy_source_statements_never_claim_academic_signoff(self):
        all_records=[row for rows in self.yearly.values() for row in rows]
        self.assertEqual(sum(r["curriculum_text_matched"] for r in all_records),0)
        self.assertEqual(sum(r["source_statement_available"] for r in all_records),342)
        self.assertTrue(all(r["academic_release_approved"] is False
                            and r["live_download_verified"] is False
                            for r in all_records))
        source_counts=Counter(r["curriculum_provenance"] for r in all_records)
        self.assertEqual(source_counts["KPM_DSKP_ORIGINAL_PDF_TEXT_SP_COLUMN"],35)
        self.assertEqual(source_counts["V26_DB_VERIFIED_FLAG_NOT_EXTERNAL_DSKP_SIGNOFF"],291)
        self.assertEqual(source_counts["KPM2021_PUBLISHED_DSKP_EXACT_SP_DISPLAY_ONLY_NOT_ACADEMIC_SIGNOFF"],16)
        for year,rows in self.yearly.items():
            self.assertTrue(all(" — " in r["sk_display"] and " — " in r["sp_display"]
                                for r in rows))
            self.assertFalse(any("Pernyataan DSKP belum" in r["sk_display"] or
                                 "Kod sumber tanpa" in r["sp_display"] for r in rows))
        for row in all_records:
            if row["curriculum_provenance"]=="KPM_DSKP_ORIGINAL_PDF_TEXT_SP_COLUMN":
                self.assertIn("SP KPM DSKP asli PDF hlm",row["note"])

    def test_week_ranges_match_snapshot_exactly_and_do_not_use_breaks(self):
        weeks=load_calendar_weeks()
        for year,rows in self.yearly.items():
            actual=[int(r["week"][1:]) for r in rows]
            self.assertEqual(sorted(actual),actual)
            self.assertTrue(all(1<=x<=43 and x!=6 for x in actual))
            self.assertEqual(rows[0]["week"], "M01")
            self.assertEqual(set(actual), set(range(1,44)) - {6})
            self.assertEqual((rows[0]["a_start"],rows[0]["a_end"]),
                             weeks["A"]["M01"])
            self.assertEqual((rows[0]["b_start"],rows[0]["b_end"]),
                             weeks["B"]["M01"])
            for r in rows:
                w=r["week"]
                self.assertEqual((r["a_start"],r["a_end"]),weeks["A"][w])
                self.assertEqual((r["b_start"],r["b_end"]),weeks["B"][w])

    def test_legacy_sains_year4_year5_2017_membership_exposed_per_pdp(self):
        original_codes=_kssr2017_official_code_sets_y4_y5()
        self.assertEqual({y:len(c) for y,c in original_codes.items()},{4:91,5:95})
        for year,rows in self.yearly.items():
            for row in rows:
                actual=row["official_kssr2017_code_membership"]
                if year in (4,5):
                    self.assertEqual(actual,row["sp"] in original_codes[year])
                    if actual is False:
                        self.assertIn("TIADA dalam DSKP KSSR2017",row["note"])
                        self.assertFalse(row["academic_release_approved"])
                else:
                    self.assertIsNone(actual)

    def test_sixteen_year6_official_statement_conflicts_do_not_corrupt_database(self):
        rows=self.yearly[6]
        changed=[r for r in rows if r["year6_official_2021_sp_display_reconciled"]]
        self.assertEqual(len(changed),16)
        self.assertEqual({r["sp"] for r in changed},
                         {"2.2.2","2.2.3","3.1.2","3.1.3","3.1.4","3.1.5",
                          "5.1.5","5.1.6","6.2.2","6.2.3","6.3.2","6.3.3",
                          "7.1.1","7.1.2","7.1.3","7.1.4"})
        by_sp={r["sp"]:r for r in changed}
        self.assertEqual(by_sp["2.2.2"]["sp_display"],
                         "2.2.2 — Memerihalkan sistem saraf pusat dan fungsinya.")
        self.assertEqual(by_sp["2.2.3"]["sp_display"],
                         "2.2.3 — Menyatakan fungsi sistem saraf periferi.")
        self.assertIn("fungsi sistem saraf pusat dan sistem saraf periferi",
                      by_sp["2.2.2"]["year6_legacy_original_sp_text"])
        self.assertIn("fungsi bahagian utama sistem saraf pusat",
                      by_sp["2.2.3"]["year6_legacy_original_sp_text"])
        self.assertEqual(by_sp["3.1.3"]["sp_display"],
                         "3.1.3 — Memerihalkan proses hidup mikroorganisma dengan menjalankan penyiasatan.")
        self.assertEqual(by_sp["6.2.2"]["sp_display"],
                         "6.2.2 — Memerihalkan kesan daya geseran.")
        self.assertEqual(by_sp["7.1.2"]["sp_display"],
                         "7.1.2 — Mengeksperimen untuk menentukan hubungan antara kelajuan, jarak dan masa.")
        self.assertEqual(by_sp["7.1.4"]["sp_display"],
                         "7.1.4 — Mendefinisi secara operasi kelajuan dengan menjalankan aktiviti.")
        self.assertTrue(all("AMARAN: Teks SP v26 berbeza" in r["note"] and
                            r["raw_pdp_title"] and
                            r["curriculum_text_matched"] is False and
                            r["academic_release_approved"] is False and
                            r["year6_official_2021_original_pdf_sha_verified"] is False
                            for r in changed))
        guide_shifts=[r for r in rows if r["panduan_y6_2020_to_2021_sp_focus_changed"]]
        self.assertEqual({r["sp"] for r in guide_shifts},{"7.1.1","7.1.2","7.1.3"})
        self.assertTrue(all("AWAS: Panduan PdP 2020" in r["note"] for r in guide_shifts))

    def test_year3_12_display_corrections_preserve_original_title(self):
        rows=self.yearly[3]
        revised=[r for r in rows if "Tajuk paparan ikut calon" in r["note"]]
        self.assertEqual(len(revised),12)
        self.assertEqual(len({r["display_id"] for r in revised}),12)
        self.assertTrue(all("BT m/s cadangan:" in r["note"] for r in rows))
        self.assertTrue(all("belum sah visual" in r["note"] for r in rows))
        self.assertTrue(all(r["raw_pdp_title"] for r in revised))

    def test_missing_sk_sp_does_not_autofill_from_wrong_subject_or_year(self):
        for year,rows in self.yearly.items():
            for row in rows:
                self.assertFalse(row["curriculum_text_matched"])
                self.assertTrue(row["source_statement_available"])
                self.assertFalse(row["academic_release_approved"])
                self.assertIn("DRAF LEGACY:",row["note"])
                self.assertNotIn("textbook verified",row["note"].lower())

    def test_five_landscape_pdf_with_cover_five_columns(self):
        with TemporaryDirectory() as tmp:
            files=build_all(tmp)
            self.assertEqual(len(files),5)
            for year,count,matched,path in files:
                self.assertEqual(count,EXPECTED[year])
                self.assertEqual(matched,0, "Legacy text must not count as academic signoff")
                with fitz.open(path) as doc:
                    self.assertGreater(doc.page_count,2)
                    self.assertTrue(all(p.rect.width>p.rect.height for p in doc))
                    cover=doc[0].get_text()
                    self.assertIn("LOGO SEKOLAH",cover)
                    self.assertIn("NAMA SEKOLAH",cover)
                    self.assertIn("NAMA GURU",cover)
                    body="\n".join(p.get_text() for p in list(doc)[1:])
                    self.assertIn("MINGGU / TARIKH",body)
                    self.assertIn("UNIT / TAJUK / PDP",body)
                    self.assertIn("CATATAN / BAHAN",body)
                    # Legacy release holds stay in source metadata, not in
                    # the teacher-facing body as a developer checkpoint.
                    self.assertNotIn("DRAF",body)
                    self.assertIn("001",body)
                    self.assertIn(f"{count:03d}",body)

if __name__=="__main__":
    unittest.main()
