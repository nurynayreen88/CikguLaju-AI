"""Regression checks for KP2027 Year 1 Alam's 29 QA-only RPH archive.

Does not access teacher accounts, the paid catalog or any runtime download endpoint.
Source ZIP bytes remain only in private owner Drive.
"""
import datetime as dt
import json
import re
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"audits/kp2027_alam_t1_29_rph_native_qa_format_20261123.json"
MAPPING=ROOT/"audits/kp2027_alam_t1_rpt93_source64_83sp_qa29_20261122.json"
CALENDAR=ROOT/"audits/kp2027_bm_sjk_rpt_2027_ab_calendar_unallocated_20261123.json"

class TestKP2027Alam29QAOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger=json.loads(LEDGER.read_text("utf-8"))
        cls.mapping=json.loads(MAPPING.read_text("utf-8"))
        cls.calendar=json.loads(CALENDAR.read_text("utf-8"))

    def test_archive_is_qa_only_and_source_original_is_immutable(self):
        item=self.ledger
        self.assertEqual(item["status"],"QA_ONLY_NOT_PUBLISHED")
        self.assertFalse(item["academic_approved"])
        self.assertFalse(item["web_publish"])
        self.assertEqual(item["ready_count"],0)
        self.assertFalse(item["source_educational_content_changed"])
        self.assertFalse(item["source_sk_sp_descriptions_changed"])
        self.assertFalse(item["source_activity_instructions_changed"])
        self.assertTrue(item["source"]["preserved"])
        self.assertEqual(item["qa_artifact"]["docx"],29)
        self.assertEqual(item["qa_artifact"]["pdf"],29)
        self.assertEqual(item["qa_artifact"]["pdf_pages"],29)
        self.assertEqual(item["qa_artifact"]["zip_entries"],61)
        self.assertEqual(item["qa_artifact"]["bytes"],1988026)
        self.assertEqual(item["qa_artifact"]["format"],"A4-portrait")
        self.assertEqual(len(item["qa_pdp_numbers"]),29)
        self.assertEqual(len(set(item["qa_pdp_numbers"])),29)
        for name in ("source","qa_artifact"):
            self.assertRegex(item[name]["sha256"],r"^[0-9a-f]{64}$")
            self.assertTrue(item[name]["drive_file_id"])
        self.assertNotEqual(item["source"]["sha256"],item["qa_artifact"]["sha256"])
        self.assertTrue(any("Refleksi" in s for s in item["format_changes"]))
        self.assertTrue(any("native DOCX-to-PDF" in s for s in item["format_changes"]))

    def test_93_rpt_rows_64_original_29_qa_and_83_unique_sp(self):
        rows=self.mapping["mappings"]
        self.assertEqual(len(rows),93)
        self.assertEqual([x["rpt_pdp"] for x in rows],list(range(1,94)))
        self.assertEqual(len({x["sp"] for x in rows}),83)
        c=Counter(x["output_status"] for x in rows)
        self.assertEqual(c,{"APPROVED_SOURCE":64,"QA_ONLY_NOT_PUBLISHED":29})
        reasons=Counter(x["mapping_reason"] for x in rows)
        self.assertEqual(reasons,{"existing_source":64,"qa_split":20,"qa_reinforcement":9})
        qa=[x for x in rows if x["output_status"]=="QA_ONLY_NOT_PUBLISHED"]
        self.assertEqual([x["rpt_pdp"] for x in qa],self.ledger["qa_pdp_numbers"])
        self.assertEqual([x["draft_qa_rph"] for x in qa],self.ledger["qa_pdp_numbers"])
        self.assertTrue(all(x["sp"] in x["source_codes"] for x in rows))
        self.assertTrue(all(x["source_rph"]>=1 and x["source_rph"]<=64 for x in rows))
        self.assertTrue(all(x["draft_qa_rph"] is None for x in rows if x["output_status"]=="APPROVED_SOURCE"))

    def test_both_weekday_windows_fit_all_2027_kpm_term_segments(self):
        rows=self.mapping["mappings"]
        for group,start_field,end_field,start_dow,end_dow in (
            ("A","start_a","end_a",6,3),("B","start_b","end_b",0,4)
        ):
            cal=self.calendar["groups"][group]
            terms=cal["segmen"]
            for row in rows:
                start=row[start_field];end=row[end_field]
                self.assertTrue(any(a<=start and end<=b for a,b in terms),
                                (group,row["rpt_pdp"],start,end))
                self.assertEqual(dt.date.fromisoformat(start).weekday(),start_dow)
                self.assertEqual(dt.date.fromisoformat(end).weekday(),end_dow)
                self.assertLessEqual(start,"2027-11-05")
                self.assertTrue(re.fullmatch(r"M\d{2}",row["week_"+group.lower()]))
        self.assertEqual(self.ledger["rpt_alignment_audit"]["issues"],0)
        self.assertEqual(self.calendar["owner_target"]["last_curricular_pdp_on_or_before"],"2027-11-05")
        self.assertTrue(self.calendar["owner_target"]["not_official_kpm"])

if __name__=="__main__":
    unittest.main()
