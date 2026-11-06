"""Source-only QA of official KPM group break dates and 10 draft Sains RPT pairs.

Uses existing project calendar ledger, never assigns PdP dates or writes DB.
Runs after the draft renderer in CI (requires python-docx and pypdf).
"""
import json
import re
import unittest
from datetime import date
from pathlib import Path
from docx import Document
from pypdf import PdfReader
from tools.render_sains_rpt_2027_ab_review_20261106 import (
    ROOT, OUT, calendar_for, calendar_cover_lines, EXPECTED,
)
class SainsRPTCalendarWindowsTests(unittest.TestCase):
    def test_official_group_windows_are_distinct_and_unscheduled(self):
        a,b=calendar_for("A"),calendar_for("B")
        self.assertEqual(a["starts"],"2027-01-04")
        self.assertEqual(b["starts"],"2027-01-04")
        self.assertEqual(a["last_school_day"],"2027-12-02")
        self.assertEqual(b["last_school_day"],"2027-12-03")
        self.assertEqual([x["start"] for x in a["holiday_windows"]],
                         ["2027-03-05","2027-05-21","2027-08-27","2027-12-03"])
        self.assertEqual([x["start"] for x in b["holiday_windows"]],
                         ["2027-03-06","2027-05-22","2027-08-28","2027-12-04"])
        self.assertIn("05/03/2027", " ".join(calendar_cover_lines("A")))
        self.assertNotIn("05/03/2027", " ".join(calendar_cover_lines("B")))
        self.assertEqual(sum(EXPECTED.values()),342)
        data=json.loads((ROOT/"audits/sains_rpt_2027_calendar_windows_20261106.json")
                        .read_text(encoding="utf-8"))
        self.assertIn("PENDING",data["status"])
        self.assertIn("must not", " ".join(data["release_constraints"]).lower())
        with self.assertRaises(ValueError):calendar_for("X")

    def test_ten_word_pdf_drafts_keep_group_specific_breaks_and_342_source_pdp(self):
        count=0
        for year,expected in EXPECTED.items():
            csv=OUT/f"SAINS_TAHUN_{year}_SOURCE_DRAF.csv"
            self.assertTrue(csv.is_file())
            for group in "AB":
                stem=f"RPT_SAINS_TAHUN_{year}_2027_KUMPULAN_{group}_DRAF"
                docx=OUT/(stem+".docx")
                pdf=OUT/(stem+".pdf")
                self.assertTrue(docx.is_file())
                self.assertTrue(pdf.is_file())
                d=Document(docx)
                self.assertEqual(len(d.tables),1)
                self.assertEqual(len(d.tables[0].rows),expected+1)
                cover=" ".join(p.text for p in d.paragraphs)
                words=" ".join(p.extract_text() for p in PdfReader(str(pdf)).pages)
                self.assertIn("DRAF",cover)
                self.assertIn("DRAF",words)
                self.assertIn("BELUM DISAHKAN",cover)
                for line in calendar_cover_lines(group):
                    self.assertIn(line,cover)
                    # PDF text extraction can break line spacing; test dates and names.
                    for v in re.findall(r"\\d{2}/\\d{2}/2027",line):
                        self.assertIn(v,words)
                self.assertIn("Belum dijadual",d.tables[0].cell(1,6).text)
                count+=1
        self.assertEqual(count,10)
if __name__=="__main__":unittest.main()
