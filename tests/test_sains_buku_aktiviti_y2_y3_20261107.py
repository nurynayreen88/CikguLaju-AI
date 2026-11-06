"""Workbook integration guard: 96 original Sains Year2/Year3 PdP mappings.

This is printed TOC evidence only. Do not claim teacher-verified academic
exercise-to-SP match or a production runtime deployment.
"""
import unittest
from tools.sains_buku_aktiviti_mapping_20261107 import (
    activity_for, activity_note, load_activity_books, EXPECTED, is_direct_sp_match
)
from tools.render_sains_y2_51_rph_draf_20261107 import get_y2_records, markdown
from web.sains_y3_rph_activity_preview_20261106 import adapt_rows, source_ledgers

class TestSainsYear2Year3ActivityBook(unittest.TestCase):
    def test_original_scanned_workbooks_96_exact_pages(self):
        by_year=load_activity_books()
        self.assertEqual(len(by_year[2]),51)
        self.assertEqual(len(by_year[3]),45)
        for year,count in EXPECTED.items():
            self.assertEqual({x["workbook_pdf_page"]-x["workbook_printed_page"]
                              for x in by_year[year].values()},{4 if year==2 else 5})
            self.assertTrue(all(x["activity_title"] for x in by_year[year].values()))
            self.assertTrue(all(x["academic_approval"] is False for x in by_year[year].values()))
        self.assertEqual(sum(is_direct_sp_match(r) for entries in by_year.values() for r in entries.values()),94)
        self.assertEqual(sum(not is_direct_sp_match(r) for entries in by_year.values() for r in entries.values()),2)

    def test_y2_corrected_growth_no_inheritance_mismatch(self):
        x=activity_for(2,"SCI-Y2-PDP-003","3.1.3")
        self.assertEqual(x["workbook_printed_page"],16)
        self.assertIn("Berat",x["activity_title"])
        self.assertEqual(x["workbook_printed_sp_codes"],["3.1.3"])
        self.assertTrue(is_direct_sp_match(x))
        self.assertFalse(is_direct_sp_match(activity_for(2,"SCI-Y2-PDP-010","4.1.7")))
        self.assertFalse(is_direct_sp_match(activity_for(2,"SCI-Y2-PDP-022","6.1.6")))
        self.assertIn("JANGAN",activity_note(activity_for(2,"SCI-Y2-PDP-010","4.1.7"),2))
        self.assertEqual(activity_for(2,"SCI-Y2-PDP-051","10.1.6")["workbook_printed_page"],84)
        with self.assertRaises(ValueError):
            activity_for(2,"SCI-Y2-PDP-003","3.1.2")

    def test_remaps_from_inspected_full_exercise_pages(self):
        self.assertEqual(activity_for(2,"SCI-Y2-PDP-016","5.1.6")["workbook_printed_page"],36)
        self.assertEqual(activity_for(2,"SCI-Y2-PDP-029","7.1.7")["workbook_printed_page"],54)
        self.assertEqual(activity_for(2,"SCI-Y2-PDP-034","8.1.5")["workbook_printed_page"],62)
        self.assertEqual(activity_for(2,"SCI-Y2-PDP-042","9.2.3")["workbook_printed_page"],73)
        self.assertEqual(activity_for(2,"SCI-Y2-PDP-045","9.2.6")["workbook_printed_page"],72)
        self.assertEqual(activity_for(3,"SCI-Y3-PDP-008","3.2.3")["workbook_printed_page"],30)
        self.assertEqual(activity_for(3,"SCI-Y3-PDP-027","6.1.7")["workbook_printed_page"],59)

    def test_year3_science_measurement_and_system_suria(self):
        self.assertEqual(activity_for(3,"SCI-Y3-PDP-026","6.1.6")["workbook_printed_page"],61)
        self.assertEqual(activity_for(3,"SCI-Y3-PDP-037","9.1.2")["workbook_printed_page"],80)
        self.assertEqual(activity_for(3,"SCI-Y3-PDP-044","10.1.4")["workbook_printed_page"],90)

    def test_51_y2_existing_rph_kept_and_workbook_added(self):
        entries=get_y2_records()
        self.assertEqual(len(entries),51)
        for item in entries:
            self.assertEqual(item["activity_book"]["sp"],item["sp"])
            self.assertEqual(item["activity_book"]["pdp_code"],item["pdp_code"])
            self.assertIn("Buku Aktiviti:",markdown(item))
            self.assertIn("Guru",markdown(item))
            self.assertIn("**Aktiviti 1:",markdown(item))
            self.assertIn("**Aktiviti 2:",markdown(item))
            self.assertIn("drive.google.com",markdown(item))

    def test_45_y3_adapter_preserves_original_and_adds_workbook_pbd(self):
        pages,_=source_ledgers()
        self.assertEqual(len(pages),45)
        sample=next(v for v in pages.values() if v["sp_code"]=="6.1.6")
        state={"subject":"Sains","year":"Tahun 3","year_label":"Tahun 3",
               "pdp_sequence_code":sample["pdp_code"],"sp_code":sample["sp_code"],
               "sk_code":sample["sp_code"].rsplit(".",1)[0]}
        original={"SOURCE":"IMMUTABLE"}
        out=adapt_rows(state,original)
        self.assertIsNot(out,original)
        self.assertEqual(original,{"SOURCE":"IMMUTABLE"})
        self.assertIn("Buku Aktiviti Sains Tahun 3",out["BUKU AKTIVITI / LATIHAN"])
        self.assertIn("m/s bercetak 61",out["BUKU AKTIVITI / LATIHAN"])
        self.assertIn("Buku Aktiviti",out["PENTAKSIRAN"])
        self.assertIn("BAHAN BANTU MENGAJAR",out)
        self.assertIn("drive.google.com",out["BUKU AKTIVITI URL"])
        state["sp_code"]="6.1.5"
        self.assertIs(adapt_rows(state,original),original)

if __name__=="__main__":
    unittest.main()
