"""Staging QA: 79 Science Year4 distinct source-specific standalone drafts."""
import unittest

from web.sains_y4_79_activity_bank_draf_20261107 import BANK
from tools.render_sains_y4_79_rph_draf_20261107 import (
    TEXTBOOK_STATUS, kps_for, markdown, KPS
)


class TestSainsYear4Bank(unittest.TestCase):
    def test_79_complete_sp_set_and_uniqueness(self):
        groups={
          "2.1":6,"2.2":4,"2.3":5,"3.1":4,"3.2":4,
          "4.1":4,"4.2":5,"5.1":4,"5.2":4,"5.3":4,
          "6.1":5,"7.1":6,"7.2":3,"8.1":3,"8.2":4,
          "9.1":3,"9.2":4,"10.1":3,"10.2":4,
        }
        expected={f"{group}.{i}" for group,n in groups.items()
                  for i in range(1,n+1)}
        self.assertEqual(len(BANK),79)
        self.assertEqual(set(BANK),expected)
        self.assertEqual(len({x["hook"] for x in BANK.values()}),79)

    def test_each_sp_has_specific_teacher_pupil_and_pbd(self):
        for sp, lesson in BANK.items():
            for key in ("teacher1","pupil1","teacher2","pupil2","pbd","materials","safety"):
                self.assertGreater(len(lesson[key]),15,(sp,key))
            self.assertNotEqual(lesson["teacher1"],lesson["teacher2"],sp)
            self.assertNotEqual(lesson["pupil1"],lesson["pupil2"],sp)

    def test_safety_and_science_specificity(self):
        self.assertIn("tidak",BANK["2.1.5"]["safety"].lower())
        self.assertIn("peparu",BANK["2.1.2"]["teacher1"].lower())
        self.assertIn("katak",BANK["3.1.3"]["teacher1"].lower())
        self.assertIn("titisan",BANK["5.3.3"]["teacher1"].lower())
        self.assertIn("bunyi",BANK["6.1.1"]["pbd"].lower())
        self.assertIn("tidak",BANK["10.2.2"]["safety"].lower())
        self.assertIn("daya",BANK["10.1.2"]["pbd"].lower())

    def test_kps_codes_proven_by_year4_dskp(self):
        self.assertEqual(KPS["1.1.4"],"Membuat inferens")
        self.assertEqual(KPS["1.1.8"],"Mentafsir data")
        self.assertIn("1.1.3 Mengukur",kps_for("10.1.2"))
        self.assertIn("1.1.2 Mengelas",kps_for("3.2.3"))

    def test_unverified_book_pages_never_fabricated(self):
        self.assertIn("NO_PAGE_REFERENCE_APPROVED",TEXTBOOK_STATUS)
        sample={
            "pdp_number":1,"pdp_code":"SCI-Y4-PDP-001",
            "unit":"Unit 2: Manusia","tajuk":"Pernafasan","sp":"2.1.1",
            "sk":"2.1","kps":kps_for("2.1.1"),**BANK["2.1.1"],
        }
        result=markdown(sample)
        self.assertIn("**Aktiviti 1:",result)
        self.assertIn("**Aktiviti 2:",result)
        self.assertIn("\n1. Guru ",result)
        self.assertIn("\n2. Murid ",result)
        self.assertIn("halaman Buku Teks asal belum disahkan",result)
        self.assertIn("DRAF/HOLD",result)
        self.assertNotIn("Buku Teks muka surat 2",result)


if __name__=="__main__":
    unittest.main()
