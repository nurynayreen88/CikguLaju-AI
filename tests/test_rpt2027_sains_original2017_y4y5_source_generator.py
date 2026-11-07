"""Sains T4/T5 original KSSR2017 source rerender can only use locked PDF hashes."""
import unittest
from pathlib import Path
from scripts.build_rpt2027_sains_kssr2017_y4y5_original_source_staging import EXPECTED,SK_TITLES,extract_official_pdf,write_five_column_preview
from scripts.audit_sains_v26_vs_kssr2017_original_year4_year5_codes import original_codes

class SainsOfficialKSSR2017SourceRefQA(unittest.TestCase):
    def test_official_code_sets_match_source_only_year4_year5(self):
        official=original_codes()
        self.assertEqual({y:len(codes) for y,codes in official.items()},{4:91,5:95})
        self.assertEqual({y:EXPECTED[y][1] for y in (4,5)},{4:91,5:95})
        for year in (4,5):
            self.assertEqual(set(SK_TITLES[year]),{".".join(code.split(".")[:2]) for code in official[year]})
            self.assertEqual(len(EXPECTED[year][0]),64)
    def test_unknown_pdf_or_year_rejected_before_any_draft_build(self):
        with self.assertRaises(ValueError):
            extract_official_pdf(3,Path("no.pdf"))
        for year in (4,5):
            with self.assertRaises(ValueError):
                extract_official_pdf(year,Path("missing-original-kpm.pdf"))
    def test_non_draft_output_refused_even_if_source_rows_look_valid(self):
        with self.assertRaises(ValueError):
            write_five_column_preview(4,[],"/tmp/official.pdf")

if __name__=="__main__":unittest.main()
