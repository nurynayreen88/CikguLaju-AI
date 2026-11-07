"""Sains KSSR2017 original wording vs legacy numeric-code collision regression."""
import unittest
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
