"""QA-only readback: official BM SJK 26-SP source crosscheck must not release drafts."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=ROOT/"audits/kp2027_bm_sjk_year1_26sp_52pdp_20261122.json"
DRAFT=ROOT/"audits/kp2027_bm_sjk_tahun1_52_rph_editorial_qa_20261123.json"
CHECK=ROOT/"audits/kp2027_bm_sjk_official_sp_crosscheck_20261123.json"

class OfficialDKSourceCrosscheck(unittest.TestCase):
    def test_source_codes_draft_pairing_and_hold_are_consistent(self):
        ref=json.loads(REFERENCE.read_text(encoding="utf-8"))
        draft=json.loads(DRAFT.read_text(encoding="utf-8"))
        check=json.loads(CHECK.read_text(encoding="utf-8"))
        self.assertEqual(check["source"]["file_id"],ref["source"]["drive_file_id"])
        self.assertEqual(check["source"]["isbn"],ref["source"]["isbn"])
        self.assertEqual(check["outcome"]["verified_unique_sp_codes"],26)
        self.assertEqual(check["outcome"]["verified_code_focus_alignment"],26)
        self.assertEqual(len(check["checks"]),26)
        self.assertEqual({r["sp"] for r in check["checks"]},{r["sp"] for r in ref["records"]})
        by_sp={r["sp"]:r for r in ref["records"]}
        for record in check["checks"]:
            original=by_sp[record["sp"]]
            self.assertEqual(record["sk"],original["sk"])
            self.assertEqual(record["editorial_focus"],original["focus"])
            self.assertEqual(record["source_pdf_page_draft"],original["page_ref_pdf_draft"])
            self.assertIs(record["official_code_found"],True)
            self.assertGreaterEqual(record["official_text_extracted_matches"],1)
            actual=[r["id"] for r in draft["records"] if r["sp_code"]==record["sp"]]
            self.assertEqual(record["linked_drafts"],actual)
            self.assertEqual(len(actual),2)
            self.assertEqual(record["pedagogical_approval"],"pending")
        self.assertEqual(check["outcome"]["draft_rph_count"],len(draft["records"]))
        self.assertEqual(check["outcome"]["ready_rph_count"],0)
        self.assertEqual(draft["status"],"QA_HOLD_NOT_READY")
        self.assertEqual(check["release_gate"],"QA_HOLD_NOT_READY")
        for key in ("rpt_ab_final_approved","official_sk_sp_descriptions_in_drafts",
                    "user_word_pdf_approved","web_download_verified"):
            self.assertIs(check["outcome"][key],False)

if __name__=="__main__":
    unittest.main()
