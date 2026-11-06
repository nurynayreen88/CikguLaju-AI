"""Guard 51 Year2 science RPH proposals, mismatch flags and safety."""
import unittest

from web.sains_y2_51_activities_draf_20261107 import BANK
from tools.render_sains_y2_51_rph_draf_20261107 import (
    Y2_SOURCE_CONFLICTS, CORRECTED_CANDIDATE_TITLE, markdown, kps_for
)


class TestYear2ScienceBank(unittest.TestCase):
    def test_all_51_distinct_and_source_specific(self):
        self.assertEqual(len(BANK),51)
        self.assertEqual(len({r["hook"] for r in BANK.values()}),51)
        for sp,item in BANK.items():
            self.assertRegex(sp,r"^\d+\.\d+\.\d+$")
            for key in ("teacher1","pupil1","teacher2","pupil2","pbd","materials","safety"):
                self.assertGreater(len(item[key]),18)
            self.assertNotEqual(item["teacher1"],item["teacher2"])
            self.assertNotEqual(item["pupil1"],item["pupil2"])

    def test_original_year2_process_skill_codes_only(self):
        self.assertIn("1.1.3 Mengukur",kps_for("5.1.3"))
        self.assertIn("1.1.2 Mengelas",kps_for("4.1.2"))
        self.assertNotIn("1.1.5",kps_for("7.1.4"))

    def test_inheritance_title_mismatch_never_silent(self):
        self.assertIn("3.1.3",Y2_SOURCE_CONFLICTS)
        self.assertIn("3.1.4",Y2_SOURCE_CONFLICTS["3.1.3"])
        self.assertIn("tumbesaran berbeza",CORRECTED_CANDIDATE_TITLE["3.1.3"])
        self.assertNotIn("pewarisan",CORRECTED_CANDIDATE_TITLE["3.1.3"].lower())

    def test_original_dskp_technology_printed_anomaly_preserved(self):
        self.assertIn("10.1.6",Y2_SOURCE_CONFLICTS)
        self.assertIn("campuran",Y2_SOURCE_CONFLICTS["10.1.6"])
        self.assertIn("binaan",BANK["10.1.6"]["pbd"].lower())

    def test_low_voltage_and_no_tasting_in_experiments(self):
        for sp in ("7.1.1","7.1.2","7.1.3","7.1.4","7.1.5","7.1.6","7.1.7"):
            self.assertTrue(any(x in BANK[sp]["safety"].lower()
                                for x in ("sel kering","bateri","rumah","kit","soket","elektrik")))
        for sp in ("8.1.3","8.1.4"):
            self.assertIn("jangan",BANK[sp]["safety"].lower())
        self.assertIn("individu",BANK["3.1.3"]["hook"].lower()+ " "+
                      BANK["3.1.3"]["teacher1"].lower())

    def test_draft_markdown_has_required_separate_numbered_actions(self):
        item={
          "pdp_number":3,"unit":"Unit 3: Manusia","candidate_title":
          CORRECTED_CANDIDATE_TITLE["3.1.3"],
          "sp":"3.1.3","tajuk":"legacy inheritance",
          "kps":kps_for("3.1.3"), "source_discrepancy":
          Y2_SOURCE_CONFLICTS["3.1.3"], **BANK["3.1.3"],
        }
        md=markdown(item)
        self.assertIn("**Aktiviti 1:",md)
        self.assertIn("**Aktiviti 2:",md)
        self.assertIn("\n1. Guru ",md)
        self.assertIn("\n2. Murid ",md)
        self.assertIn("DRAF/HOLD",md)
        self.assertIn("Buku Teks Tahun 2 halaman belum disahkan",md)


if __name__ == "__main__":
    unittest.main()
