"""Sains Year6 KPS evidence is sourced, but cannot certify RPH/DSKP."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from rpt_2027.common.sains_y6_bpk_2020_panduan_43_sp_source import source_index
from scripts.audit_sains_y6_bpk_panduan_43_sp_kps_staging import audit,write_report

class BPK2020PanduanSainsYear6QA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=audit()

    def test_16_original_activity_blocks_43_sp_with_three_duplicate_page_references(self):
        d=source_index()
        self.assertEqual(len(d),43)
        self.assertEqual(sum(len(refs) for refs in d.values()),46)
        self.assertEqual([r["pdf_page"] for r in d["2.2.3"]],[23,26])
        self.assertEqual([r["pdf_page"] for r in d["6.3.1"]],[94,97])
        self.assertEqual([r["pdf_page"] for r in d["6.3.2"]],[94,97])
        self.assertEqual([r["pdf_page"] for r in d["3.1.4"]],[51])
        self.assertTrue(all(not code.startswith("1.1.") for code in d))

    def test_43_actual_year6_pdp_guide_references_no_fictitious_lessons(self):
        r=self.report
        self.assertEqual(r["historical_pdp_count"],84)
        self.assertEqual(r["historical_pdp_with_bpk_2020_example"],43)
        self.assertEqual(r["historical_pdp_without_specific_2020_example"],41)
        self.assertEqual(r["source_page_to_pdp_references"],46)
        self.assertEqual(r["guide2020_year6_sp_edition_conflict_codes"],["7.1.1","7.1.2","7.1.3"])
        self.assertEqual(r["guide2020_sp_codes_without_known_edition_conflict_NOT_APPROVED"],40)
        self.assertEqual({x["original_year6_sp"] for x in r["rows"]
                          if x["2020_guide_sp_focus_differs_from_2021_dskp"]},
                         {"7.1.1","7.1.2","7.1.3"})
        self.assertEqual(len(r["rows"]),84)
        self.assertEqual(len({v["original_year6_sp"] for v in r["rows"]}),84)
        self.assertEqual(r["approved_rph_count"],0)
        self.assertEqual(r["original_2021_dskp_source_sp_wording_signoffs"],0)
        self.assertEqual(r["kps_not_separately_timetabled_but_integrated_into_rph_verified"],0)
        self.assertFalse(r["ready_for_web_telegram"])
        self.assertEqual(r["database_writes"],0)
        self.assertTrue(all(
            x["historical_rph_kps_implementation_verified"] is False
            and x["official_2021_sp_text_verified"] is False
            and x["approved_for_user_download"] is False
            and x["bpk_panduan_2020_has_example"] is bool(x["source_pdf_pages"])
            for x in r["rows"]))

    def test_source_only_renders_draf_report(self):
        with TemporaryDirectory() as td:
            file=Path(td)/"Sains_Y6_BPK_KPS_DRAF.json"
            self.assertTrue(write_report(file).exists())
            data=json.loads(file.read_text(encoding="utf-8"))
            self.assertEqual(data["status"],self.report["status"])
            with self.assertRaises(ValueError):
                write_report(Path(td)/"Sains_Y6_BPK_KPS_FINAL.json")

if __name__=="__main__":
    unittest.main()
