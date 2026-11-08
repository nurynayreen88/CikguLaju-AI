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

    def test_year2_19_visual_candidates_are_source_locked_and_academically_held(self):
        path=ROOT/"audits/bahasa_arab_rpt2027_t2_19_sp_visual_statement_candidates_20261108.json"
        candidate=json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(candidate["status"],
                         "VISUAL_TRANSCRIPTION_CANDIDATE_ONLY_NOT_ACADEMIC_FINAL")
        self.assertEqual(candidate["source_pdf_sha256"],self.data["year2"]["pdf_sha256"])
        self.assertEqual(candidate["source_url"],self.data["year2"]["source_url"])
        self.assertEqual(candidate["source_pages_inspected"],list(range(31,39)))
        evidence={e["sp_code"]:e["pdf_page"] for e in self.data["year2"]["entries"]}
        parts={e["sp_code"]:e for e in candidate["entries"]}
        self.assertEqual(set(parts),set(evidence))
        self.assertEqual(len(parts),19)
        self.assertEqual(sum(bool(x["candidate_for_staging_display"])
                             for x in parts.values()),18)
        self.assertTrue(all(x["pdf_page"]==evidence[code]
                            and x["inspected_rendered_page"]
                            and not x["academic_panel_signed_off"]
                            for code,x in parts.items()))
        self.assertFalse(parts["3.4.1"]["candidate_for_staging_display"])
        self.assertEqual(parts["3.4.1"]["visual_transcription_candidate"],
                         parts["3.3.1"]["visual_transcription_candidate"])
        self.assertIn("identical",parts["3.4.1"]["hold_reason"])
        self.assertEqual(candidate["summary"]["academic_panel_signoffs"],0)
        rows=arabic_records(2)
        self.assertEqual(len(rows),60)
        self.assertEqual(sum(row["source_sp_visual_candidate_staging"]
                             for row in rows),58)
        self.assertEqual(sum(row["sp"]=="3.4.1" for row in rows),2)
        self.assertTrue(all(row["source_sp_dskp_text_signoff"] is False
                            and row["source_sp_academic_panel_signed_off"] is False
                            for row in rows))
        self.assertIs(candidate["summary"]["rpt_release_ready"],False)

    def test_year3_23_visual_candidates_hold_three_duplicate_syllable_sp(self):
        path=ROOT/"audits/bahasa_arab_rpt2027_t3_23_sp_visual_statement_candidates_20261108.json"
        candidate=json.loads(path.read_text(encoding="utf-8"))
        original=next(x for x in self.data["years"] if x["year"]==3)
        self.assertEqual(candidate["status"],
                         "VISUAL_TRANSCRIPTION_CANDIDATE_ONLY_NOT_ACADEMIC_FINAL")
        self.assertEqual(candidate["source_pdf_sha256"],original["pdf_sha256"])
        self.assertEqual(candidate["source_url"],original["source_url"])
        self.assertEqual(candidate["source_pdf_pages"],48)
        self.assertEqual(candidate["source_pages_inspected"],[29,30,31,34,35,36,39])
        code_to_page={e["sp_code"]:e["pdf_page"] for e in original["entries"]}
        entries={e["sp_code"]:e for e in candidate["entries"]}
        self.assertEqual(len(entries),23)
        self.assertEqual(set(entries),set(code_to_page))
        self.assertEqual(sum(e["candidate_for_staging_display"]
                             for e in entries.values()),20)
        self.assertTrue(all(e["pdf_page"]==code_to_page[code]
                            and e["inspected_rendered_page"]
                            and e["academic_panel_signed_off"] is False
                            for code,e in entries.items()))
        holds={"2.3.1":"2.2.1","2.3.2":"2.2.2","2.3.3":"2.2.3"}
        self.assertEqual({code for code,e in entries.items()
                          if not e["candidate_for_staging_display"]},set(holds))
        for conflict,source in holds.items():
            self.assertEqual(entries[conflict]["pdf_page"],35)
            self.assertFalse(entries[conflict]["candidate_for_staging_display"])
            self.assertEqual(entries[conflict]["visual_transcription_candidate"],
                             entries[source]["visual_transcription_candidate"])
            self.assertIn("syllable",entries[conflict]["hold_reason"])
        self.assertEqual(candidate["summary"]["academic_panel_signoffs"],0)
        self.assertIs(candidate["summary"]["rpt_release_ready"],False)
        rows=arabic_records(3)
        self.assertEqual(len(rows),60)
        self.assertEqual(sum(row["sp"] in holds for row in rows),6)
        self.assertEqual(sum(row["source_sp_visual_candidate_staging"]
                             for row in rows),54)
        self.assertTrue(all(row["source_sp_dskp_text_signoff"] is False
                            and row["source_sp_academic_panel_signed_off"] is False
                            for row in rows))

    def test_year4_25_visual_candidates_source_locked_and_58_pdp(self):
        path=ROOT/"audits/bahasa_arab_rpt2027_t4_25_sp_visual_statement_candidates_20261108.json"
        draft=json.loads(path.read_text(encoding="utf-8"))
        source=next(x for x in self.data["years"] if x["year"]==4)
        self.assertEqual(draft["status"],
                         "VISUAL_TRANSCRIPTION_CANDIDATE_ONLY_NOT_ACADEMIC_FINAL")
        self.assertEqual(draft["source_pdf_sha256"],source["pdf_sha256"])
        self.assertEqual(draft["source_url"],source["source_url"])
        self.assertEqual(draft["source_pdf_pages"],54)
        self.assertEqual(draft["source_pages_inspected"],
                         [31,32,33,34,36,37,38,39,41,42,43,44])
        matches={e["sp_code"]:e["pdf_page"] for e in source["entries"]}
        evidence={e["sp_code"]:e for e in draft["entries"]}
        self.assertEqual(len(evidence),25)
        self.assertEqual(set(evidence),set(matches))
        self.assertTrue(all(e["pdf_page"]==matches[code]
                            and e["inspected_rendered_page"] is True
                            and e["candidate_for_staging_display"] is True
                            and e["academic_panel_signed_off"] is False
                            and e["visual_transcription_candidate"].startswith("القدرة على ")
                            for code,e in evidence.items()))
        self.assertEqual(draft["summary"]["candidate_for_staging_display"],25)
        self.assertEqual(draft["summary"]["held_source_conflict"],0)
        self.assertEqual(draft["summary"]["academic_panel_signoffs"],0)
        self.assertEqual(draft["summary"]["sk_full_statement_signoffs"],0)
        self.assertIs(draft["summary"]["rpt_release_ready"],False)
        rows=arabic_records(4)
        self.assertEqual(len(rows),58)
        self.assertEqual(sum(r["source_sp_visual_candidate_staging"] for r in rows),58)
        self.assertTrue(all(not r["source_sp_dskp_text_signoff"]
                            and not r["source_sp_academic_panel_signed_off"]
                            and not r.get("week")
                            for r in rows))

    def test_year5_25_visual_candidates_are_year_specific_and_unapproved(self):
        path=ROOT/"audits/bahasa_arab_rpt2027_t5_25_sp_visual_statement_candidates_20261108.json"
        draft=json.loads(path.read_text(encoding="utf-8"))
        source=next(x for x in self.data["years"] if x["year"]==5)
        self.assertEqual(draft["status"],
                         "VISUAL_TRANSCRIPTION_CANDIDATE_ONLY_NOT_ACADEMIC_FINAL")
        self.assertEqual(draft["source_pdf_sha256"],source["pdf_sha256"])
        self.assertEqual(draft["source_url"],source["source_url"])
        self.assertEqual(draft["source_pdf_pages"],54)
        self.assertEqual(draft["source_pages_inspected"],
                         [31,32,33,34,36,37,38,41,42,43,44])
        pages={e["sp_code"]:e["pdf_page"] for e in source["entries"]}
        mapped={e["sp_code"]:e for e in draft["entries"]}
        self.assertEqual(len(mapped),25)
        self.assertEqual(set(mapped),set(pages))
        self.assertTrue(all(e["pdf_page"]==pages[code]
                            and e["inspected_rendered_page"] is True
                            and e["candidate_for_staging_display"] is True
                            and e["academic_panel_signed_off"] is False
                            and e["visual_transcription_candidate"].startswith("القدرة على ")
                            for code,e in mapped.items()))
        self.assertEqual(draft["summary"]["candidate_for_staging_display"],25)
        self.assertEqual(draft["summary"]["held_source_conflict"],0)
        self.assertEqual(draft["summary"]["academic_panel_signoffs"],0)
        self.assertEqual(draft["summary"]["sk_full_statement_signoffs"],0)
        self.assertIs(draft["summary"]["rpt_release_ready"],False)
        self.assertIn("من الكلمات المدروسة",
                      mapped["1.2.5"]["visual_transcription_candidate"])
        rows=arabic_records(5)
        self.assertEqual(len(rows),60)
        self.assertEqual(sum(r["source_sp_visual_candidate_staging"] for r in rows),60)
        self.assertTrue(all(not r["source_sp_dskp_text_signoff"]
                            and not r["source_sp_academic_panel_signed_off"]
                            and not r.get("week") for r in rows))

    def test_year6_25_source_candidates_not_borrowed_from_year5(self):
        year=6
        path=ROOT/"audits/bahasa_arab_rpt2027_t6_25_sp_visual_statement_candidates_20261108.json"
        ledger=json.loads(path.read_text(encoding="utf-8"))
        y6=next(x for x in self.data["years"] if x["year"]==year)
        y5=json.loads((ROOT/"audits/bahasa_arab_rpt2027_t5_25_sp_visual_statement_candidates_20261108.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["status"],
                         "VISUAL_TRANSCRIPTION_CANDIDATE_ONLY_NOT_ACADEMIC_FINAL")
        self.assertEqual(ledger["source_pdf_sha256"],y6["pdf_sha256"])
        self.assertEqual(ledger["source_url"],y6["source_url"])
        self.assertEqual(ledger["source_pdf_pages"],52)
        self.assertEqual(ledger["source_pages_inspected"],
                         [31,32,33,34,36,37,38,41,42,43])
        pages={e["sp_code"]:e["pdf_page"] for e in y6["entries"]}
        mapped={e["sp_code"]:e for e in ledger["entries"]}
        five={e["sp_code"]:e for e in y5["entries"]}
        self.assertEqual(len(mapped),25)
        self.assertEqual(set(mapped),set(pages))
        self.assertTrue(all(e["pdf_page"]==pages[code]
                            and e["inspected_rendered_page"] is True
                            and e["candidate_for_staging_display"] is True
                            and e["academic_panel_signed_off"] is False
                            and e["visual_transcription_candidate"].startswith("القدرة على ")
                            for code,e in mapped.items()))
        self.assertEqual(ledger["summary"]["candidate_for_staging_display"],25)
        self.assertEqual(ledger["summary"]["held_source_conflict"],0)
        self.assertEqual(ledger["summary"]["academic_panel_signoffs"],0)
        self.assertEqual(ledger["summary"]["sk_full_statement_signoffs"],0)
        self.assertIs(ledger["summary"]["rpt_release_ready"],False)
        self.assertIn("من الكلمات المسموعة",
                      mapped["1.2.5"]["visual_transcription_candidate"])
        self.assertIn("من الكلمات المدروسة",
                      five["1.2.5"]["visual_transcription_candidate"])
        self.assertNotEqual(mapped["1.2.5"]["visual_transcription_candidate"],
                            five["1.2.5"]["visual_transcription_candidate"])
        self.assertNotEqual(mapped["3.1.1"]["visual_transcription_candidate"],
                            five["3.1.1"]["visual_transcription_candidate"])
        rows=arabic_records(6)
        self.assertEqual(len(rows),60)
        self.assertEqual(sum(r["source_sp_visual_candidate_staging"] for r in rows),60)
        self.assertTrue(all(not r["source_sp_dskp_text_signoff"]
                            and not r["source_sp_academic_panel_signed_off"]
                            and not r.get("week") for r in rows))

    def test_pdf_location_evidence_cannot_automatically_unlock_rpt(self):
        for year in range(2, 7):
            records = arabic_records(year)
            expected = {2: 60, 3: 60, 4: 58, 5: 60, 6: 60}[year]
            self.assertEqual(len(records), expected)
            for row in records:
                self.assertIn("Pernyataan penuh SK belum dipadankan",
                              row["sk_display"])
                if ((year==2 and row["sp"]!="3.4.1")
                    or (year==3 and row["sp"] not in
                        {"2.3.1","2.3.2","2.3.3"})
                    or year in (4,5,6)):
                    self.assertTrue(row["source_sp_visual_candidate_staging"])
                    self.assertIn(" — القدرة على ",row["sp_display"])
                else:
                    self.assertFalse(row["source_sp_visual_candidate_staging"])
                    self.assertIn("Pernyataan penuh SP belum dipadankan",
                                  row["sp_display"])
                self.assertIs(row["source_sp_academic_panel_signed_off"],False)
                self.assertIs(row["source_sp_dskp_text_signoff"],False)
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
