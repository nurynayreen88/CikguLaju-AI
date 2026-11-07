"""Sains Tahun5: 83 SP-specific DRAF lessons, curriculum and safety checks."""
import unittest
from web.sains_y5_83_activity_bank_draf_20261107 import BANK
from tools.render_sains_y5_83_rph_draf_20261107 import (
    KPS, TEXTBOOK_STATUS, markdown, kps_for, get_y5_records,
)
from tools.sains_y5_83_textbook_original_sp_pages_20261107 import (
    checked_book_pages,source_part_for_printed_page,RANGES


)

class TestScienceYear5SourceBank(unittest.TestCase):
    def test_original_year5_book_drive_pdf_part1_only_is_incomplete(self):
        from tools.render_sains_y5_83_rph_draf_20261107 import ROOT
        import json
        p=ROOT/"audits/sains_y5_original_textbook_pdf_incomplete_20261107.json"
        source=json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(source["source_sha256"],"322b8ea0e19fc5b6da1c41ff64a25d22e470917027d9b293c85efc045a6be3e2")
        self.assertEqual(source["actual_pdf_page_count"],43)
        self.assertEqual(source["last_printed_page_in_file"],35)
        self.assertGreater(source["table_of_contents_max_printed_page"],200)
        self.assertEqual(source["exact_page_assignment_per_sp_approved"],0)
        self.assertEqual(source["original_year5_pdp"],83)
        self.assertEqual(source["status"],"SOURCE_PDF_INCOMPLETE__NO_EXACT_SP_PAGE_RELEASE")
        self.assertFalse(source["upload_production"])

    def test_exact_83_sps_and_distinct_activities(self):
        groups={
            "2.1":5,"2.2":4,"2.3":4,"3.1":6,"3.2":4,
            "3.3":7,"4.1":3,"4.2":4,"5.1":1,"5.2":7,
            "5.3":4,"6.1":7,"7.1":6,"8.1":5,"8.2":4,
            "9.1":4,"9.2":3,"10.1":5,
        }
        all_codes={f"{g}.{i}" for g,n in groups.items() for i in range(1,n+1)}
        self.assertEqual(len(BANK),83)
        self.assertEqual(set(BANK),all_codes)
        self.assertEqual(len({x["hook"] for x in BANK.values()}),83)

    def test_actual_staged_source_83_records_are_year5_not_year4(self):
        items=get_y5_records()
        self.assertEqual(len(items),83)
        self.assertTrue(all(x["tahun"]==5 and x["year"]==5 for x in items))
        self.assertEqual(items[0]["pdp_code"],"SCI-Y5-PDP-001")
        self.assertEqual(items[-1]["pdp_code"],"SCI-Y5-PDP-083")
        self.assertTrue(all(x["status"]=="DRAF_HOLD" for x in items))
        self.assertTrue(all(x["textbook_pages"] and x["textbook_page_primary"]==x["textbook_pages"][0]
                            and x["textbook_reference_status"].endswith("TEACHER_HOLD")
                            for x in items))
        self.assertEqual([x["textbook_page_primary"] for x in items[:3]],[20,22,23])

    def test_teacher_and_pupil_actions_not_repeated(self):
        for sp,lesson in BANK.items():
            for field in ("hook","teacher1","pupil1","teacher2",
                          "pupil2","pbd","materials","safety"):
                self.assertGreater(len(lesson[field]),16,(sp,field))
            self.assertNotEqual(lesson["teacher1"],lesson["teacher2"],sp)
            self.assertNotEqual(lesson["pupil1"],lesson["pupil2"],sp)

    def test_dskp_science_process_skills_are_exact_year5_codes(self):
        self.assertEqual(KPS["1.1.10"],"Mengawal pemboleh ubah")
        self.assertEqual(KPS["1.1.12"],"Mengeksperimen")
        self.assertIn("1.1.12 Mengeksperimen",kps_for("7.1.3"))
        self.assertIn("1.1.10 Mengawal pemboleh ubah",kps_for("5.2.4"))
        self.assertIn("1.1.3 Mengukur",kps_for("6.1.2"))

    def test_year5_specific_accuracy_and_safety(self):
        self.assertIn("bonggol simpanan lemak",BANK["3.1.3"]["pupil1"])
        self.assertNotIn("simpan air",BANK["3.1.3"]["pupil1"].lower())
        self.assertIn("Matahari",BANK["3.3.3"]["pupil1"])
        self.assertIn("suis",BANK["5.2.4"]["safety"])
        self.assertIn("guru",BANK["6.1.3"]["safety"])
        self.assertIn("guru",BANK["7.1.3"]["safety"])
        self.assertIn("Jangan",BANK["9.1.1"]["safety"])
        self.assertIn("haba",BANK["8.2.2"]["pupil1"])

    def test_full_year5_original_3part_textbook_sp_page_evidence(self):
        data=checked_book_pages()
        self.assertEqual(len(data),83)
        self.assertEqual(len({x for entry in data.values() for x in entry["printed_pages"]}),103)
        self.assertEqual(RANGES,((1,35,43),(36,130,95),(131,234,104)))
        self.assertEqual(source_part_for_printed_page(35),(1,42))
        self.assertEqual(source_part_for_printed_page(36),(2,0))
        self.assertEqual(source_part_for_printed_page(130),(2,94))
        self.assertEqual(source_part_for_printed_page(131),(3,0))
        self.assertEqual(source_part_for_printed_page(234),(3,103))
        self.assertEqual(data["5.2.6"]["printed_pages"],[129,131])
        self.assertEqual(data["6.1.1"]["primary_page"],146)
        self.assertEqual(data["10.1.5"]["primary_page"],219)
        self.assertTrue(all(x["teacher_academic_approved"] is False for x in data.values()))

    def test_only_source_verified_not_academic_grade_and_draft_label(self):
        self.assertIn("SP_PAGE_TOKENS_VERIFIED",TEXTBOOK_STATUS)
        p=get_y5_records()[0]
        text=markdown(p)
        self.assertIn("**Aktiviti 1:",text)
        self.assertIn("**Aktiviti 2:",text)
        self.assertIn("\n1. Guru ",text)
        self.assertIn("\n2. Murid ",text)
        self.assertIn("m/s 20, 27",text)
        self.assertIn("kesesuaian isi dan PBD belum disahkan panitia",text)
        self.assertIn("DRAF/HOLD",text)

if __name__=="__main__":
    unittest.main()
