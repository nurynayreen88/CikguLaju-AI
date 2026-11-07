"""QA source-linked Sains 2027 342 PdP five-column PARTIAL RPT drafts."""
from __future__ import annotations
from collections import Counter
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest
import fitz

from scripts.build_rpt_2027_sains_342_actual_source_staging import (
    EXPECTED,source_records,build_all
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
                self.assertTrue(all("DRAF, bukan RPT lengkap" in r["note"] for r in rows))

    def test_week_ranges_match_snapshot_exactly_and_do_not_use_breaks(self):
        weeks=load_calendar_weeks()
        for year,rows in self.yearly.items():
            actual=[int(r["week"][1:]) for r in rows]
            self.assertEqual(sorted(actual),actual)
            self.assertTrue(all(2<=x<=43 and x!=6 for x in actual))
            for r in rows:
                w=r["week"]
                self.assertEqual((r["a_start"],r["a_end"]),weeks["A"][w])
                self.assertEqual((r["b_start"],r["b_end"]),weeks["B"][w])

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
                if not row["curriculum_text_matched"]:
                    self.assertIn("Kod sumber tanpa pernyataan penuh DSKP",
                                  row["sp_display"])
                    self.assertNotIn("textbook verified",row["note"].lower())

    def test_five_landscape_pdf_with_cover_five_columns(self):
        with TemporaryDirectory() as tmp:
            files=build_all(tmp)
            self.assertEqual(len(files),5)
            for year,count,matched,path in files:
                self.assertEqual(count,EXPECTED[year])
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
                    self.assertIn("DRAF",body)
                    self.assertIn("001",body)
                    self.assertIn(f"{count:03d}",body)

if __name__=="__main__":
    unittest.main()
