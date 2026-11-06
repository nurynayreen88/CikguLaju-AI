"""QA 45 fully distinct Sains Y3 draft RPH activities, no app import."""
import unittest
import json
from pathlib import Path
from web.sains_y3_rph_activity_preview_20261106 import (
    BANK,INTEGRATED_SP_DRAFT,KPS_LABELS,KPS_BY_SP,adapt_rows,source_ledgers,
)

class SainsY3ActivityCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger,cls.fixes=source_ledgers()

    def test_exact_45_sp_specific_activity_coverage(self):
        self.assertEqual(len(self.ledger),45)
        self.assertEqual(len(BANK),45)
        self.assertEqual(len(self.fixes),12)
        seen=set()
        for code,record in self.ledger.items():
            sp=record["sp_code"]
            original={"REFLEKSI":"Asal","TARIKH":"06/11/2026","STATUS":"DRAF"}
            state={"subject":"Sains","year":"Tahun 3","year_label":"Tahun 3",
                   "pdp_sequence_code":code,
                   "sk_code":sp.rsplit(".",1)[0],"sp_code":sp}
            revised=adapt_rows(state,original)
            with self.subTest(code=code):
                self.assertIsNot(revised,original)
                self.assertEqual(revised["REFLEKSI"],"Asal")
                self.assertEqual(revised["TARIKH"],"06/11/2026")
                self.assertEqual(revised["STATUS"],"DRAF")
                self.assertEqual(original,{"REFLEKSI":"Asal","TARIKH":"06/11/2026","STATUS":"DRAF"})
                self.assertTrue(revised["TAJUK"])
                expected_sp=sp+((", "+INTEGRATED_SP_DRAFT[sp]["sp"]) if sp in INTEGRATED_SP_DRAFT else "")
                self.assertEqual(revised["STANDARD PEMBELAJARAN"],expected_sp)
                self.assertIn("Guru",revised["AKTIVITI UTAMA"])
                self.assertIn("Murid",revised["AKTIVITI UTAMA"])
                self.assertIn("\n1. Guru",revised["AKTIVITI UTAMA"])
                self.assertIn("\n2. Murid",revised["AKTIVITI UTAMA"])
                self.assertEqual(revised["AKTIVITI UTAMA"].count("Aktiviti "),2)
                self.assertTrue(len(revised["AKTIVITI UTAMA"])>200)
                self.assertIn("Buku Teks Sains Tahun 3",revised["BAHAN BANTU MENGAJAR"])
                self.assertIn("semak sebelum cetak",revised["BAHAN BANTU MENGAJAR"])
                self.assertTrue(revised["PENTAKSIRAN"])
                self.assertTrue(revised["PENUTUP"])
                self.assertTrue(revised["KRITERIA KEJAYAAN"])
                self.assertNotIn("penerokaan konsep",revised["AKTIVITI UTAMA"].lower())
                seen.add(revised["AKTIVITI UTAMA"])
        self.assertEqual(len(seen),45)

    def test_exact_45_dskp_year3_kps_activities_integrated(self):
        self.assertEqual(set(KPS_BY_SP),set(BANK))
        self.assertEqual(KPS_LABELS,{
            "1.1.1":"Memerhati","1.1.2":"Mengelas",
            "1.1.3":"Mengukur dan menggunakan nombor",
            "1.1.4":"Membuat inferens","1.1.5":"Meramal",
            "1.1.6":"Berkomunikasi",
        })
        all_skills=set()
        for rec in self.ledger.values():
            sp=rec["sp_code"]
            state={"subject":"Sains","year":"Tahun 3",
                   "pdp_sequence_code":rec["pdp_code"],"sp_code":sp,
                   "sk_code":sp.rsplit(".",1)[0]}
            out=adapt_rows(state,{})
            codes=KPS_BY_SP[sp]
            self.assertGreaterEqual(len(codes),2)
            self.assertEqual(len(codes),len(set(codes)))
            expected="; ".join(f"{code} {KPS_LABELS[code]}" for code in codes)
            with self.subTest(sp=sp):
                self.assertEqual(out["KEMAHIRAN PROSES SAINS"],expected)
            all_skills.update(codes)
        self.assertEqual(all_skills,set(KPS_LABELS))

    def test_twelve_dskp_corrections_win_over_outdated_titles(self):
        for code,f in self.fixes.items():
            p=self.ledger[code]
            s={"subject":"Sains","year":"Tahun 3","sp_code":p["sp_code"],
               "sk_code":p["sp_code"].rsplit(".",1)[0],
               "pdp_sequence_code":code}
            revised=adapt_rows(s,{"TAJUK":"OLD"})
            with self.subTest(code=code):
                self.assertEqual(revised["TAJUK"],f["ds_kpm_official_sp_text"])

    def test_wrong_subject_year_code_or_sp_fails_closed_without_side_effects(self):
        code="SCI-Y3-PDP-037"
        original={"AKTIVITI UTAMA":"original","REFLEKSI":"orig"}
        valid={"subject":"Sains","year":"Tahun 3","sp_code":"9.1.2",
               "sk_code":"9.1","pdp_sequence_code":code}
        for bad in [
            {**valid,"subject":"Matematik"},{**valid,"year":"Tahun 1"},
            {**valid,"pdp_sequence_code":"SCI-Y3-PDP-002"},
            {**valid,"sp_code":"9.1.3"},{**valid,"sk_code":"8.1"},
            {**valid,"pdp_sequence_code":"SCI-Y3-PDP-999"},
            {**valid,"year_label":"Tahun 4"},
        ]:
            with self.subTest(bad=bad):
                self.assertIs(adapt_rows(bad,original),original)
        self.assertEqual(original,{"AKTIVITI UTAMA":"original","REFLEKSI":"orig"})

    def test_three_missing_content_sp_have_explicit_activity_and_pbd_evidence(self):
        # DSKP crosswalk candidates; remain DRAF pending textbook review.
        self.assertEqual(
            {k:v["sp"] for k,v in INTEGRATED_SP_DRAFT.items()},
            {"3.2.1":"3.2.5","3.3.1":"3.3.3","3.3.2":"3.3.4"}
        )
        self.assertEqual(len(self.ledger),45)
        for row in self.ledger.values():
            sp=row["sp_code"]
            state={"subject":"Sains","year":"Tahun 3","sp_code":sp,
                   "sk_code":sp.rsplit(".",1)[0],
                   "pdp_sequence_code":row["pdp_code"]}
            revised=adapt_rows(state,{})
            with self.subTest(sp=sp):
                if sp in INTEGRATED_SP_DRAFT:
                    extra=INTEGRATED_SP_DRAFT[sp]
                    self.assertEqual(revised["STANDARD PEMBELAJARAN"],sp+", "+extra["sp"])
                    self.assertIn(extra["pbd"],revised["KRITERIA KEJAYAAN"])
                    self.assertIn(extra["pbd"],revised["PENTAKSIRAN"])
                    self.assertIn("\n3. Guru ",revised["AKTIVITI UTAMA"])
                    self.assertIn("\n4. Murid ",revised["AKTIVITI UTAMA"])
                    self.assertIn(extra["teacher"],revised["AKTIVITI UTAMA"])
                    self.assertIn(extra["pupil"],revised["AKTIVITI UTAMA"])
                else:
                    self.assertEqual(revised["STANDARD PEMBELAJARAN"],sp)
                    self.assertNotIn("\n3. Guru ",revised["AKTIVITI UTAMA"])
                    self.assertNotIn("\n4. Murid ",revised["AKTIVITI UTAMA"])

    def test_three_integrated_sp_have_textbook_dskp_evidence_but_not_release(self):
        path=Path(__file__).resolve().parents[1] / "audits/sains_y3_three_integrated_sp_book_text_20261106.json"
        evidence=json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            evidence["review_status"],
            "TEXT_LAYER_CONFIRMED__VISUAL_PAGE_AND_TEACHER_REVIEW_PENDING",
        )
        self.assertIn("NOT_PRODUCTION_RELEASE",evidence["intended_use"])
        self.assertEqual(len(evidence["evidence"]),3)
        self.assertEqual(
            {(e["primary_sp"],e["integrated_sp"]) for e in evidence["evidence"]},
            {(primary, data["sp"]) for primary,data in INTEGRATED_SP_DRAFT.items()},
        )
        self.assertEqual(
            {e["pdp_code"] for e in evidence["evidence"]},
            {"SCI-Y3-PDP-006","SCI-Y3-PDP-010","SCI-Y3-PDP-011"},
        )
        for e in evidence["evidence"]:
            self.assertEqual(e["qa"],"TEXT_MATCH__VISUAL_PENDING")
            self.assertTrue(e["book_printed_pages"])

    def test_acid_demos_do_not_invite_chemical_tasting_or_touching(self):
        for sp in ("8.1.1","8.1.2","8.1.3","8.1.4"):
            row=next(x for x in self.ledger.values() if x["sp_code"]==sp)
            state={"subject":"Sains","year":"Tahun 3","sp_code":sp,
                   "sk_code":"8.1","pdp_sequence_code":row["pdp_code"]}
            txt=adapt_rows(state,{})["AKTIVITI UTAMA"].lower()
            self.assertNotIn("mencuba rasa bahan kimia",txt)
            self.assertNotIn("merasa sampel",txt)
        row=next(x for x in self.ledger.values() if x["sp_code"]=="8.1.2")
        s={"subject":"Sains","year":"Tahun 3","sp_code":"8.1.2",
           "sk_code":"8.1","pdp_sequence_code":row["pdp_code"]}
        self.assertIn("tanpa ujian rasa",adapt_rows(s,{})["AKTIVITI UTAMA"])
if __name__=="__main__":
    unittest.main()
