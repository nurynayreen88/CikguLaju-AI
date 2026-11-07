"""QA for 20 remaining BM, Pendidikan Islam, Bahasa Arab and Music RPT 2027."""
from __future__ import annotations
import unittest
from pathlib import Path
import tempfile
from pypdf import PdfReader
from scripts.build_rpt_2027_remaining_four_subjects_staging import (
    bm_records,pi_records,arabic_records,music_records,build_all
)
from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks


class RemainingRPTFormatQA(unittest.TestCase):
    def test_5_years_of_bm_full_source_statements(self):
        expected=[164,165,165,166,165]
        cal=load_calendar_weeks()
        for year,count in zip(range(2,7),expected):
            with self.subTest(year=year):
                rows=bm_records(year)
                self.assertEqual(len(rows),count)
                self.assertEqual([r["id"] for r in rows],
                                 [f"{i:03d}" for i in range(1,count+1)])
                self.assertTrue(all(
                    (" — " in r["sp_display"] and len(r["sp_display"]) > len(r["sp"]) + 8)
                    or ("Penilaian Tema (tiada kod SP baharu)" in r["sp_display"])
                    for r in rows
                ))
                self.assertTrue(all("BT" in r["note"] for r in rows))
                for row in rows:
                    self.assertEqual((row["a_start"],row["a_end"]),
                                     cal["A"][row["week"]])
                    self.assertEqual((row["b_start"],row["b_end"]),
                                     cal["B"][row["week"]])

    def test_5_years_of_pi_source_is_unmodified(self):
        counts=[112,147,151,143,143]
        master=load_calendar_weeks()
        for year,n in zip(range(2,7),counts):
            with self.subTest(year=year):
                records=pi_records(year)
                self.assertEqual(len(records),n)
                self.assertEqual([r["id"] for r in records],
                                 [f"{i:03d}" for i in range(1,n+1)])
                self.assertEqual(sum(bool(r["source_held"]) for r in records),
                                 1 if year==2 else 5 if year==6 else 0)
                for row in records:
                    self.assertTrue(row["sk"])
                    self.assertTrue(row["sp"])
                    if row["source_held"]:
                        self.assertEqual(row["week"], "")
                        self.assertFalse(row.get("a_start"))
                        self.assertFalse(row.get("b_start"))
                    else:
                        self.assertIn(row["week"], master["A"])
                        self.assertIn(row["week"], master["B"])
                        self.assertEqual((row["a_start"],row["a_end"]),
                                         master["A"][row["week"]])
                        self.assertEqual((row["b_start"],row["b_end"]),
                                         master["B"][row["week"]])

    def test_arabic_298_rows_keep_unknown_standards_and_dates_explicit(self):
        counts={2:60,3:60,4:58,5:60,6:60}
        for y,n in counts.items():
            with self.subTest(year=y):
                rows=arabic_records(y)
                self.assertEqual(len(rows),n)
                self.assertEqual([r["id"] for r in rows],
                                 [f"{i:03d}" for i in range(1,n+1)])
                self.assertTrue(all("Pernyataan penuh SK belum dipadankan" in r["sk_display"] and
                                    "Pernyataan penuh SP belum dipadankan" in r["sp_display"]
                                    for r in rows))
                self.assertTrue(all(not r.get("week") and not r.get("a_start")
                                    for r in rows))

    def test_music_175_source_weeks_preserved(self):
        master=load_calendar_weeks()
        for year in range(2,7):
            with self.subTest(year=year):
                rows=music_records(year)
                self.assertEqual(len(rows),35)
                self.assertEqual([r["id"] for r in rows],
                                 [f"{i:03d}" for i in range(1,36)])
                self.assertTrue(all(r["sk"]=="Kod SK belum dibekalkan dalam CSV"
                                    for r in rows))
                self.assertTrue(all("Pernyataan penuh SP belum dipadankan" in r["sp_display"]
                                    for r in rows))
                for row in rows:
                    self.assertEqual((row["a_start"],row["a_end"]),master["A"][row["week"]])
                    self.assertEqual((row["b_start"],row["b_end"]),master["B"][row["week"]])

    def test_20_pdf_five_column_landscape_and_minimal_cover(self):
        with tempfile.TemporaryDirectory() as t:
            built=build_all(t)
            self.assertEqual(len(built),20)
            for sub,year,n,p in built:
                with self.subTest(sub=sub,year=year):
                    pdf=PdfReader(p)
                    self.assertGreaterEqual(len(pdf.pages),2)
                    for pg in pdf.pages:
                        self.assertGreater(float(pg.mediabox.width),
                                           float(pg.mediabox.height))
                    first=pdf.pages[0].extract_text()
                    for required in ("RANCANGAN PENGAJARAN TAHUNAN 2027",
                                     "NAMA SEKOLAH","NAMA GURU","LOGO SEKOLAH"):
                        self.assertIn(required,first)
                    for forbidden in ("ALAMAT SEKOLAH","KUMPULAN A","KUMPULAN B","Halaman 1"):
                        self.assertNotIn(forbidden,first)
                    # The same five columns as the already approved preview.
                    body="\n".join(pg.extract_text() for pg in pdf.pages[1:]).upper()
                    for head in ("MINGGU / TARIKH","UNIT / TAJUK / PDP","SK","SP","CATATAN / BAHAN"):
                        self.assertIn(head,body)
                    if sub=="bahasa_arab":
                        self.assertIn("BELUM DIPADANKAN",body)
                    if sub=="pendidikan_islam":
                        self.assertIn("REKOD DITAHAN",body) if year in (2,6) else None


if __name__=="__main__":
    unittest.main()
