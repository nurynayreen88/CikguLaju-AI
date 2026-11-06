"""Source-only QA of official KPM group break dates and 10 draft Sains RPT pairs.

Uses existing project calendar ledger, never assigns PdP dates or writes DB.
Runs after the draft renderer in CI (requires python-docx and pypdf).
"""
import csv
import json
import re
import unittest
from datetime import date
from pathlib import Path
from docx import Document
from pypdf import PdfReader
from tools.render_sains_rpt_2027_ab_review_20261106 import (
    ROOT, OUT, calendar_for, calendar_cover_lines, EXPECTED,
    year3_overlay_sources, YEAR3_INTEGRATED_SP_CANDIDATE,
)
from web.sains_y3_rph_activity_preview_20261106 import adapt_rows, source_ledgers
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

    def test_all_year3_titles_and_supplemental_sp_align_to_source_ledger(self):
        # The RPT draft must never repeat the 12 stale DSKP titles
        # or omit the 3 SP integrated in the RPH draft (#419).
        fixes,evidence=year3_overlay_sources()
        self.assertEqual(len(fixes),12)
        self.assertEqual(set(YEAR3_INTEGRATED_SP_CANDIDATE.values()),set(evidence))
        with (OUT/"SAINS_TAHUN_3_SOURCE_DRAF.csv").open(encoding="utf-8-sig",newline="") as fh:
            rows=list(csv.DictReader(fh))
        self.assertEqual(len(rows),45)
        by_code={row["Kod sumber"]:row for row in rows}
        self.assertEqual(len(by_code),45)
        count_fixed=count_extra=0
        for code,row in by_code.items():
            original=row["Fokus asal (v25.82)"]
            original_sp=row["SP asal"]
            expected_title=original
            if code in fixes:
                f=fixes[code]
                self.assertEqual(f["original_title"],original)
                self.assertEqual(f["sp_code"],original_sp)
                expected_title=f["ds_kpm_official_sp_text"]
                self.assertIn("DSKP_TITLE_CANDIDATE",row["Catatan QA"])
                count_fixed+=1
            self.assertEqual(row["Fokus PdP (draf QA)"],expected_title)
            extra=YEAR3_INTEGRATED_SP_CANDIDATE.get(original_sp)
            if extra:
                self.assertEqual(row["SP"],original_sp+", "+extra)
                self.assertIn("DSKP_EXTRA_SP_CANDIDATE",row["Catatan QA"])
                count_extra+=1
            else:
                self.assertEqual(row["SP"],original_sp)
            self.assertEqual(row["Minggu/tarikh"],"BELUM DIJADUAL")
            self.assertEqual(row["Status"],"DRAF_SEMAK")
        self.assertEqual((count_fixed,count_extra),(12,3))
        # Both groups have identical corrected academic source but
        # distinct KPM covers; do not create additional lesson identities.
        for group in "AB":
            path=OUT/f"RPT_SAINS_TAHUN_3_2027_KUMPULAN_{group}_DRAF.docx"
            doc=Document(path)
            self.assertEqual(len(doc.tables[0].rows),46)
            for row in doc.tables[0].rows[1:]:
                index=int(row.cells[0].text)
                code=f"SCI-Y3-PDP-{index:03d}"
                source=by_code[code]
                self.assertEqual(row.cells[3].text,source["SP"])
                self.assertEqual(row.cells[4].text,source["Fokus PdP (draf QA)"])

    def test_all_45_year3_rpt_and_rph_word_pdf_share_one_sp_title_source(self):
        # Integration guard between two draft PR streams, no production edits.
        src,fixes=source_ledgers()
        with (OUT/"SAINS_TAHUN_3_SOURCE_DRAF.csv").open(encoding="utf-8-sig",newline="") as f:
            rpt={row["Kod sumber"]:row for row in csv.DictReader(f)}
        rphroot=ROOT/"build/sains_y3_45_rph_REVIEW_ONLY_20261106"
        with (rphroot/"MANIFEST_DRAF.csv").open(encoding="utf-8-sig",newline="") as f:
            manifest={row["pdp"]:row for row in csv.DictReader(f)}
        self.assertEqual(set(rpt),set(src))
        self.assertEqual(set(manifest),set(src))
        self.assertEqual(len(src),45)
        for n in range(1,46):
            code=f"SCI-Y3-PDP-{n:03d}"
            primary=src[code]["sp_code"]
            state={"subject":"Sains","year":"Tahun 3","year_label":"Tahun 3",
                   "pdp_sequence_code":code,
                   "sk_code":primary.rsplit(".",1)[0],"sp_code":primary}
            rendered=adapt_rows(state,{})
            row=rpt[code]
            with self.subTest(pdp=code):
                self.assertEqual(row["SP"],rendered["STANDARD PEMBELAJARAN"])
                self.assertEqual(row["Fokus PdP (draf QA)"],rendered["TAJUK"])
                self.assertEqual(manifest[code]["title"],rendered["TAJUK"])
                word=Document(rphroot/f"SAINS_T3_PDP_{n:03d}_DRAF.docx")
                self.assertEqual(word.tables[1].cell(1,1).text,rendered["TAJUK"])
                self.assertIn(rendered["STANDARD PEMBELAJARAN"],word.tables[1].cell(2,1).text)
                self.assertIn("Guru",word.tables[2].cell(1,1).text)
                self.assertIn("Murid",word.tables[2].cell(1,1).text)
                pdf=PdfReader(str(rphroot/f"SAINS_T3_PDP_{n:03d}_DRAF.pdf"))
                self.assertEqual(len(pdf.pages),1)
                txt=re.sub(r"\\s+"," ",pdf.pages[0].extract_text())
                for codepart in rendered["STANDARD PEMBELAJARAN"].split(", "):
                    self.assertIn(codepart,txt)
                if primary in YEAR3_INTEGRATED_SP_CANDIDATE:
                    self.assertIn("3. Guru",word.tables[2].cell(1,1).text)
                    self.assertIn("4. Murid",word.tables[2].cell(1,1).text)
                    self.assertIn(YEAR3_INTEGRATED_SP_CANDIDATE[primary],txt)
                else:
                    self.assertNotIn("3. Guru",word.tables[2].cell(1,1).text)
        self.assertEqual(len(fixes),12)

    def test_years_two_four_five_six_are_not_silently_rewritten(self):
        for year in [2,4,5,6]:
            with (OUT/f"SAINS_TAHUN_{year}_SOURCE_DRAF.csv").open(
                    encoding="utf-8-sig",newline="") as fh:
                rows=list(csv.DictReader(fh))
            self.assertEqual(len(rows),EXPECTED[year])
            for row in rows:
                self.assertEqual(row["SP"],row["SP asal"])
                self.assertEqual(row["Fokus PdP (draf QA)"],row["Fokus asal (v25.82)"])
                self.assertEqual(row["Minggu/tarikh"],"BELUM DIJADUAL")

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
