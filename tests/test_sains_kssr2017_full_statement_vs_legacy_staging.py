"""Sains KSSR2017 original wording vs legacy numeric-code collision regression."""
import unittest
import json
from pathlib import Path
from scripts.audit_sains_v26_vs_kssr2017_original_year4_year5_codes import original_codes
from scripts.build_rpt2027_sains_kssr2017_y4y5_original_source_staging import EXPECTED
from scripts.audit_sains_kssr2017_full_statement_vs_legacy_staging import (
    compare_official_to_legacy,
)

def row(code,text,year=4):
    return dict(year=year, sk_code=".".join(code.split(".")[:2]),
                sk_text="Original KPM DSKP", sp_code=code,
                sp_text_source_extract_NEEDS_VISUAL_REVIEW=text,
                original_pdf_page=61)

class OriginalKSSR2017WordingQA(unittest.TestCase):
    def test_numeric_overlap_never_automatically_becomes_approved(self):
        official=[
            row("2.3.1","Menyatakan manusia bergerak balas apabila organ deria menerima rangsangan."),
            row("2.3.2","Menjelas dengan contoh gerak balas manusia terhadap rangsangan dalam kehidupan harian."),
            row("2.3.3","Membuat inferens tentang kepentingan gerak balas manusia terhadap rangsangan."),
        ]
        legacy={
            "2.3.1":{"sp_text":"Menyatakan manusia bergerak balas apabila organ deria menerima rangsangan."},
            "2.3.2":{"sp_text":"Pernyataan legacy berbeza daripada asal 2017."},
            "3.4.1":{"sp_text":"Pewarisan lama yang tidak wujud dalam Tahun 4 DSKP asal."},
        }
        d=compare_official_to_legacy(4,official,legacy,{"2.3.1","2.3.2","2.3.3"})
        self.assertEqual(d["counts"],{
            "SAME_CODE_SAME_WORDING_NEEDS_CONTEXT":1,
            "SAME_CODE_DIFFERENT_WORDING":1,
            "OFFICIAL_CODE_NOT_IN_LEGACY":1,
        })
        self.assertEqual(d["legacy_codes_not_in_original_kssr2017"],["3.4.1"])
        self.assertFalse(d["release_ready"])
        self.assertTrue(d["no_auto_code_migration"])
        self.assertEqual(d["source_text_visual_signoff_count"],0)
        self.assertTrue(all(not x["academic_sp_signoff"] for x in d["rows"]))
        self.assertTrue(all(not x["pdp_rph_book_mapped"] for x in d["rows"]))

    def test_complete_committed_original_186_sp_source_index_keeps_draft_gates(self):
        source=(Path(__file__).resolve().parents[1] / "rpt_2027/sains/"
                "kssr2017_y4_y5_186_official_sp_source_extraction_20261107_DRAF.json")
        data=json.loads(source.read_text(encoding="utf-8"))
        self.assertEqual(len(data["rows"]),186)
        self.assertFalse(data["academic_release_ready"])
        self.assertFalse(data["ready_for_web_telegram"])
        self.assertEqual(data["total_official_sp"],186)
        expected=original_codes()
        for year in (4,5):
            p=[r for r in data["rows"] if r["year"]==year]
            self.assertEqual({r["sp_code"] for r in p},expected[year])
            self.assertEqual(data["source"][str(year)]["official_pdf_sha256"],EXPECTED[year][0])
            self.assertEqual(data["source"][str(year)]["visual_signoff_count"],0)
            self.assertTrue(all(r["visual_signoff"] is False
                                and len(r["sp_text_source_extract_UNVERIFIED"])>=18
                                and 51<=r["original_pdf_page"]<=92 for r in p))

    def test_kpm_pdf_hyphenated_line_wrap_is_only_layout_difference(self):
        source=[row("5.1.2",("Membanding dan membezakan bayang- bayang yang terhasil "
                    "apabila cahaya dihalang oleh objek lutsinar, lutcahaya dan legap "
                    "dengan menjalankan aktiviti."))]
        legacy={"5.1.2":{"sp_text":("Membanding dan membezakan bayang-bayang yang terhasil "
                    "apabila cahaya dihalang oleh objek lutsinar, lutcahaya dan legap "
                    "dengan menjalankan aktiviti.")}}
        result=compare_official_to_legacy(4,source,legacy,{"5.1.2"})
        self.assertEqual(result["counts"]["SAME_CODE_SAME_WORDING_NEEDS_CONTEXT"],1)
        self.assertFalse(result["release_ready"])

    def test_missing_or_duplicated_original_codes_are_rejected(self):
        official=[row("2.3.1","Menyatakan manusia bergerak balas apabila organ deria menerima rangsangan.")]
        with self.assertRaises(ValueError):
            compare_official_to_legacy(4,official,{},{"2.3.1","2.3.2"})
        with self.assertRaises(ValueError):
            compare_official_to_legacy(4,official+official,{},{"2.3.1"})
        with self.assertRaises(ValueError):
            compare_official_to_legacy(4,[row("2.3.1","too short")],{},{"2.3.1"})
        with self.assertRaises(ValueError):
            compare_official_to_legacy(4,[row("2.3.1","Pernyataan berkaitan pembelajaran sains.",5)],{},{"2.3.1"})
        with self.assertRaises(ValueError):
            compare_official_to_legacy(6,official,{},{"2.3.1"})

if __name__=="__main__":
    unittest.main()
