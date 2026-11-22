"""Non-destructive release guard for 52 editorial KP2027 BM SJK Year-1 RPH.

These QA drafts never authorize a live route, curriculum release, charging,
RPT allocation or a downloadable Word/PDF. Official SP descriptions must
still be independently checked against the original DK.
"""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "audits/kp2027_bm_sjk_year1_26sp_52pdp_20261122.json"
DRAFT = ROOT / "audits/kp2027_bm_sjk_tahun1_52_rph_editorial_qa_20261123.json"

class BM_SJK_52_RPH_EditorialQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(BASE.read_text(encoding="utf-8"))
        cls.edition = json.loads(DRAFT.read_text(encoding="utf-8"))

    def test_provenance_and_gate(self):
        e=self.edition
        self.assertEqual(e["version"],"2026-11-23")
        self.assertEqual(e["status"],"QA_HOLD_NOT_READY")
        self.assertEqual(e["counts"],{"sp":26,"draft_rph":52,"ready":0})
        self.assertEqual(e["source"]["drive_file_id"],self.reference["source"]["drive_file_id"])
        self.assertEqual(e["source"]["isbn"],self.reference["source"]["isbn"])
        self.assertNotIn("READY", e["status"].replace("NOT_READY",""))

    def test_all_26_dk_sp_and_52_distinct_pdp(self):
        records=self.edition["records"]
        self.assertEqual(len(records),52)
        self.assertEqual([r["proposed_pdp"] for r in records],list(range(1,53)))
        self.assertEqual(len({r["id"] for r in records}),52)
        for item in self.reference["records"]:
            pair=[r for r in records if r["sp_code"]==item["sp"]]
            self.assertEqual([r["proposed_pdp"] for r in pair],item["rpt_pdp_proposals"])
            self.assertEqual([r["phase"] for r in pair],item["phases"])
            self.assertEqual([r["sk_code"] for r in pair],[item["sk"],item["sk"]])
            self.assertEqual([r["source_pdf_page_draft"] for r in pair],[item["page_ref_pdf_draft"]]*2)
            self.assertEqual([r["focus_editorial"] for r in pair],[item["focus"]]*2)

    def test_real_pedagogical_phases_without_fabricated_approval(self):
        for r in self.edition["records"]:
            self.assertEqual(r["status"],"QA_HOLD_NOT_READY")
            self.assertEqual((r["curriculum"],r["school_stream"],r["year"]),("KP2027","SJK",1))
            self.assertTrue(re.fullmatch(r"[1-4]\\.\\d\\.\\d",r["sp_code"]))
            self.assertEqual(r["refleksi_label"],"Refleksi")
            self.assertEqual(r["teacher_fields"],["Kelas","Tarikh","Masa","Bil. Murid"])
            self.assertEqual(len(r["objectives"]),2)
            self.assertEqual(len(r["aktiviti_utama"]),3)
            self.assertTrue(all("Guru " in a["guru"] and "Murid " in a["murid"]
                                for a in r["aktiviti_utama"]))
            for idx,a in enumerate(r["aktiviti_utama"],1):
                self.assertTrue(a["title"].startswith(f"Aktiviti {idx}: "))
                self.assertGreater(len(a["guru"]),80)
                self.assertGreater(len(a["murid"]),70)
            self.assertGreater(len(r["set_induksi"]["guru"]),60)
            self.assertGreater(len(r["penutup"]["murid"]),40)
            self.assertTrue(r["pemulihan"] and r["pengayaan"] and r["penilaian"])
            self.assertEqual(len(r["verification_required"]),5)
            self.assertNotIn("KSSR",json.dumps(r,ensure_ascii=False))
            self.assertTrue(r["formatting_contract"].startswith("jadual besar tunggal"))

if __name__ == "__main__":
    unittest.main()
