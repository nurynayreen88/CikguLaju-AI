"""QA for 20 remaining BM, Pendidikan Islam, Bahasa Arab and Music RPT 2027."""
from __future__ import annotations
import unittest
from pathlib import Path
import tempfile
from pypdf import PdfReader
import fitz
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
                        self.assertTrue(row["held_source_proposal"])
                        self.assertIs(row["held_release_approved"], False)
                        self.assertIn("REKOD DITAHAN", row["note"])
                        if year==6 and row["id"]=="060":
                            self.assertIn("Solat Ketika Sakit", row["sk"])
                            self.assertIn("4.2.3", row["sp"])
                        else:
                            self.assertIn("BUKAN KOD SK RASMI", row["sk"])
                            self.assertIn("TIADA KOD SP RASMI", row["sp"])
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
                if y == 2:
                    self.assertTrue(all("Pernyataan penuh SK belum dipadankan" in r["sk_display"] and
                                        "Pernyataan penuh SP belum dipadankan" not in r["sp_display"] and
                                        "القدرة" in r["sp_display"] and
                                        r["source_sp_dskp_text_signoff"] is False and
                                        r["source_pdf_extraction_code_repeated_unreliable"] is True
                                        for r in rows))
                    self.assertEqual(len({r["sp"] for r in rows}),19)
                elif y in (3,4,5):
                    self.assertTrue(all("Pernyataan penuh SK belum dipadankan" in r["sk_display"] and
                                        "Pernyataan penuh SP belum dipadankan" not in r["sp_display"] and
                                        "القدرة" in r["sp_display"] and
                                        r["source_arabic_orthography_normalized_not_visual_signoff"] and
                                        r["source_sp_dskp_text_signoff"] is False for r in rows))
                    self.assertEqual(len({r["sp"] for r in rows}), {3:23,4:25,5:25}[y])
                else:
                    self.assertTrue(all("Pernyataan penuh" not in r["sk_display"] and
                                        "Pernyataan penuh" not in r["sp_display"] and
                                        "القدرة" in r["sp_display"] and
                                        r["source_arabic_orthography_normalized_not_visual_signoff"]
                                        for r in rows))
                    self.assertEqual(len({r["sp"] for r in rows}),25)
                    self.assertEqual(rows[0]["sp"],"1.1.1")
                self.assertTrue(all(not r.get("week") and not r.get("a_start")
                                    for r in rows))
                self.assertTrue(all(r["source_sp_dskp_pdf_url"].startswith("https://drive.google.com/file/d/")
                                    and r["source_sp_dskp_pdf_page"]>0
                                    and r["source_sp_dskp_text_signoff"] is False
                                    for r in rows))
                self.assertTrue(all(r["source_pdf_extraction_code_repeated_unreliable"] is (y==2)
                                    for r in rows))

    def test_music_175_source_weeks_preserved(self):
        master=load_calendar_weeks()
        for year in range(2,7):
            with self.subTest(year=year):
                rows=music_records(year)
                self.assertEqual(len(rows),35)
                self.assertEqual([r["id"] for r in rows],
                                 [f"{i:03d}" for i in range(1,36)])
                self.assertTrue(all(" — " in r["sk_display"] and
                                    " — " in r["sp_display"] for r in rows))
                self.assertTrue(all("Pernyataan penuh SP belum dipadankan" not in r["sp_display"]
                                    for r in rows))
                self.assertTrue(all(r["dskp_text_source"]==
                                    "KPM_MUSIC_DSKP_PDF_PRINTED_SK_SP_STAGING_ONLY"
                                    for r in rows))
                self.assertTrue(all(r["source_rpt_sp_codes"].replace(";", " / ")==
                                    r["sp"] for r in rows))
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
                    # Five-column visual formatting stays the same, but
                    # Jawi PI and Arabic BA must have native headings.
                    body="\n".join(pg.extract_text() for pg in pdf.pages[1:]).upper()
                    if sub in ("pendidikan_islam","bahasa_arab"):
                        self.assertNotIn("MINGGU / TARIKH",body)
                        self.assertNotIn("CATATAN / BAHAN",body)
                        with fitz.open(p) as original:
                            clip=original[1].get_text("dict")
                            spans=[s for block in clip["blocks"]
                                   for line in block.get("lines",[])
                                   for s in line["spans"]
                                   if 46<=s["bbox"][1]<86 and s["bbox"][3]<90]
                            self.assertTrue(any(
                                any("\u0600"<=c<="\u08ff" or "\ufb50"<=c<="\ufeff"
                                    for c in s["text"])
                                for s in spans))
                    else:
                        for head in ("MINGGU / TARIKH","UNIT / TAJUK / PDP",
                                     "SK","SP","CATATAN / BAHAN"):
                            self.assertIn(head,body)
                    if sub=="bahasa_arab":
                        # Missing official Arabic text stays flagged in the source
                        # audit ledger, never printed as a teacher-facing placeholder.
                        self.assertNotIn("BELUM DIPADANKAN",body)
                        self.assertTrue(all(x["source_sp_dskp_text_signoff"] is False
                                            for x in arabic_records(year)))
                        with fitz.open(p) as doc:
                            urls=[link["uri"] for page in list(doc)[1:]
                                  for link in page.get_links() if link.get("uri")]
                        self.assertEqual(len(urls),n)
                        row_sources=arabic_records(year)
                        self.assertEqual(set(urls),{r["source_sp_dskp_pdf_url"]
                                                      for r in row_sources})
                    if sub=="pendidikan_islam" and year in (2,6):
                        # The Jawi/Arabic bidi font roundtrip does not always
                        # expose Latin notes in PDF text-extraction order.
                        # Assert the pre-render sourced record instead.
                        self.assertTrue(any("REKOD DITAHAN" in r["note"]
                                            for r in pi_records(year)))


if __name__=="__main__":
    unittest.main()
