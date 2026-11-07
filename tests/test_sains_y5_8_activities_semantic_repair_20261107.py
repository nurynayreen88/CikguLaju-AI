"""Targeted official-SP semantic safety gate for 8 revised Year5 Science drafts.

This gate does not certify academic quality or authorize LIVE release.
"""
import json
import unittest
from pathlib import Path

from web.sains_y5_83_activity_bank_draf_20261107 import BANK
from tools.render_sains_y5_83_rph_draf_20261107 import get_y5_records
from tools.sains_y5_83_textbook_original_sp_pages_20261107 import checked_book_pages

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"audits/sains_y5_8_activities_semantic_repair_20261107.json"


class TestEightOfficialActivityFixes(unittest.TestCase):
    def test_eight_evidence_records_preserve_entire_83_pdp_bank(self):
        source=json.loads(AUDIT.read_text(encoding="utf-8"))
        rows=get_y5_records()
        self.assertEqual(source["changed_pdp"],8)
        self.assertTrue(source["source_pdp_identity_preserved"])
        self.assertEqual(len(rows),83)
        self.assertEqual(len(BANK),83)
        self.assertEqual(len({x["pdp_code"] for x in rows}),83)
        self.assertEqual(len(checked_book_pages()),83)
        self.assertEqual({x["sp"] for x in source["items"]},
                         {"6.1.3","6.1.5","7.1.3","8.1.3",
                          "8.1.4","8.2.1","8.2.2","10.1.2"})
        self.assertTrue(all(x["requires_teacher_signoff"] for x in source["items"]))
        self.assertEqual(source["teacher_approved"],0)
        self.assertIsNone(source["academic_quality_percent"])
        self.assertFalse(source["runtime_ready"])
        self.assertFalse(source["production_db_changed"])

    def test_heat_temperature_activities_are_observable_and_safe(self):
        temp=BANK["6.1.3"]
        self.assertIn("menyukat",temp["pupil1"])
        self.assertIn("memplot graf",temp["pupil2"])
        self.assertIn("guru",temp["safety"])
        self.assertNotIn("murid memanaskan",temp["teacher2"])
        expanded=BANK["6.1.5"]
        self.assertIn("meletakkan botol",expanded["teacher2"])
        self.assertIn("merekod perubahan",expanded["pupil2"])
        self.assertIn("suhu selamat",expanded["safety"])

    def test_rusting_real_observations_and_variable_control_without_sharp_iron(self):
        lesson=BANK["7.1.3"]
        self.assertIn("hipotesis",lesson["pupil1"])
        self.assertIn("pemboleh ubah",lesson["pupil1"])
        self.assertIn("meramal",lesson["pupil1"])
        self.assertIn("lapisan perang",lesson["pupil2"])
        self.assertIn("bekas bertutup",lesson["teacher2"])
        self.assertIn("murid tidak membuka",lesson["safety"])

    def test_matter_change_practice_is_not_just_cards_or_photos(self):
        self.assertIn("memindahkan",BANK["8.1.3"]["pupil1"])
        self.assertIn("udara",BANK["8.1.3"]["teacher2"])
        self.assertIn("ais menjadi air",BANK["8.1.4"]["pupil1"])
        self.assertIn("wap air tidak kelihatan",BANK["8.1.4"]["pupil2"])
        self.assertIn("memerhati ais mencair",BANK["8.2.1"]["pupil1"])
        self.assertIn("titisan",BANK["8.2.1"]["pupil1"])
        self.assertIn("air",BANK["8.2.2"]["teacher1"])
        self.assertNotIn("mentega",BANK["8.2.2"]["teacher1"])
        self.assertIn("haba",BANK["8.2.2"]["pupil1"])
        self.assertIn("empat proses",BANK["8.2.2"]["pupil2"])

    def test_machines_pupils_observe_real_safe_tool(self):
        lesson=BANK["10.1.2"]
        self.assertIn("alat sebenar",lesson["pupil1"])
        self.assertIn("fungsi",lesson["pupil2"])
        self.assertIn("tidak menyentuh bilah",lesson["safety"])


if __name__=="__main__":
    unittest.main()
