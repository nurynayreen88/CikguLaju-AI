"""Non-release verification of official KP2027 BM SJK SK/SP passages in 52 drafts."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
CANON=ROOT/"audits/kp2027_bm_sjk_sksp_verified_20261123.json"
DRAFT=ROOT/"audits/kp2027_bm_sjk_tahun1_52_rph_editorial_qa_20261123.json"
BASE=ROOT/"audits/kp2027_bm_sjk_year1_26sp_52pdp_20261122.json"

class BM_SJK_OfficialDescriptionsQA(unittest.TestCase):
    def test_every_draft_has_verified_sk_sp_text_but_stays_hold(self):
        official=json.loads(CANON.read_text(encoding="utf-8"))
        draft=json.loads(DRAFT.read_text(encoding="utf-8"))
        base=json.loads(BASE.read_text(encoding="utf-8"))
        self.assertEqual(official["source"]["file_id"],base["source"]["drive_file_id"])
        self.assertEqual(official["source"]["isbn"],base["source"]["isbn"])
        self.assertEqual(official["counts"],{"sk":9,"sp":26})
        self.assertEqual(len(official["sk"]),9)
        self.assertEqual(len(official["sp"]),26)
        self.assertEqual({r["sp"] for r in base["records"]},set(official["sp"]))
        self.assertEqual({r["sk"] for r in base["records"]},set(official["sk"]))
        self.assertEqual(len(draft["records"]),52)
        self.assertEqual(draft["counts"]["ready"],0)
        self.assertEqual(draft["status"],"QA_HOLD_NOT_READY")
        self.assertEqual(draft["source_validation"]["applied_draft_rph"],52)
        self.assertEqual(draft["source_validation"]["verified_sk_descriptions"],9)
        self.assertEqual(draft["source_validation"]["verified_sp_descriptions"],26)
        for record in draft["records"]:
            with self.subTest(id=record["id"]):
                self.assertEqual(record["status"],"QA_HOLD_NOT_READY")
                self.assertEqual(record["sk_description"],official["sk"][record["sk_code"]])
                self.assertEqual(record["sp_description"],official["sp"][record["sp_code"]])
                self.assertGreater(len(record["sk_description"]),20)
                self.assertGreater(len(record["sp_description"]),20)
                self.assertEqual(record["refleksi_label"],"Refleksi")
                self.assertEqual(len(record["aktiviti_utama"]),3)
                self.assertNotIn("Penerangan penuh SK dan SP daripada DK muktamad",
                                 record["verification_required"])
                if record["sp_code"]=="1.2.2":
                    self.assertEqual(record["sp_components"],
                                     official["special_sp_components"]["1.2.2"])
        self.assertEqual(len({r["id"] for r in draft["records"]}),52)

if __name__=="__main__":
    unittest.main()
