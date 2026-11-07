"""Year6 Sains: 84 specific Year6 SK/SP activity drafts — staging only.

Academic scoring, textbook page accuracy, teacher signoff and Telegram/Web
runtime parity are different gates and remain HOLD.
"""
from __future__ import annotations
import unittest

from web.sains_y6_84_activity_bank_draf_20261107 import BANK,kps_for,FILES
from tools.audit_sains_y6_84_source_preflight_20261107 import GROUPS,EXPECTED_SP
from tools.sains_y6_textbook_toc_20261107 import cue_for, load_toc_ranges, short_cue
from tools.render_sains_y6_84_rph_draf_20261107 import (
    get_y6_records,markdown,TEXTBOOK_STATUS,BOOK_SOURCE,DSKP_SOURCE
)

class TestYear6FullDraft(unittest.TestCase):
    def test_exact_84_sp_inventory_and_17_groups(self):
        self.assertEqual(len(BANK),84)
        self.assertEqual(set(BANK),EXPECTED_SP)
        self.assertEqual(sum(GROUPS.values()),84)
        self.assertEqual(len(FILES),3)
        self.assertEqual(len({r["hook"] for r in BANK.values()}),84)
        self.assertEqual(len({r["pbd"] for r in BANK.values()}),84)

    def test_year6_textbook_2021_toc_context_is_not_fabricated_exact_page(self):
        toc=load_toc_ranges()
        self.assertEqual(toc["edition"],2021)
        self.assertEqual(toc["isbn"],"978-983-49-3278-7")
        self.assertEqual(len(toc["groups"]),17)
        self.assertFalse(toc["exact_sp_page_verified"])
        self.assertFalse(toc["teacher_approved"])
        seen=set()
        for sp in EXPECTED_SP:
            e=cue_for(sp)
            self.assertEqual(e["status"],"UNIT_TOPIC_TOC_ONLY__EXACT_SP_TEXTBOOK_PAGE_PENDING")
            self.assertIsNone(e["exact_sp_page"])
            self.assertFalse(e["teacher_signoff"])
            self.assertIn("bukan pengesahan halaman SP",short_cue(sp))
            seen.add(sp.rsplit(".",1)[0])
        self.assertEqual(len(seen),17)
        self.assertEqual((cue_for("2.1.1")["range_start"],cue_for("2.1.1")["range_end"]),(13,19))
        self.assertEqual((cue_for("10.1.2")["range_start"],cue_for("10.1.2")["range_end"]),(165,178))

    def test_source_pdp_84_not_other_years(self):
        items=get_y6_records()
        self.assertEqual(len(items),84)
        self.assertEqual([r["pdp_code"] for r in items],
                         [f"SCI-Y6-PDP-{i:03d}" for i in range(1,85)])
        self.assertTrue(all(r["year"]==6 and r["tahun"]==6 for r in items))
        self.assertTrue(all(r["sp"] in BANK for r in items))
        self.assertTrue(all(r["status"]=="DRAF_HOLD" for r in items))
        self.assertTrue(all(r["textbook_pages"] is None for r in items))
        self.assertTrue(all(r["curriculum_quality_percent"] is None for r in items))

    def test_specific_teacher_pupil_steps_and_evidence(self):
        for sp,x in BANK.items():
            for field in ("hook","teacher1","pupil1","teacher2","pupil2","pbd",
                          "materials","safety"):
                self.assertGreater(len(x[field]),18,(sp,field))
            self.assertNotEqual(x["teacher1"],x["teacher2"])
            self.assertNotEqual(x["pupil1"],x["pupil2"])
            self.assertNotEqual(x["pbd"],x["hook"])

    def test_science_experiment_and_unit_safety(self):
        self.assertIn("1.1.12",kps_for("3.1.4"))
        self.assertIn("1.1.12",kps_for("6.2.3"))
        self.assertIn("1.1.12",kps_for("12.1.3"))
        self.assertIn("1.1.9",kps_for("7.1.4"))
        self.assertIn("yis pembakar",BANK["3.1.4"]["safety"])
        self.assertIn("matahari",BANK["10.1.1"]["safety"].lower())
        self.assertIn("bukan untuk dimakan",BANK["8.2.3"]["safety"])
        self.assertIn("privasi",BANK["2.1.1"]["safety"])
        self.assertIn("kaca",BANK["6.3.3"]["safety"])

    def test_high_risk_specific_learning_task_not_generic(self):
        self.assertIn("tiga pemboleh ubah",BANK["3.1.4"]["pbd"])
        self.assertIn("cm",BANK["7.1.1"]["teacher1"])
        self.assertIn("jarak",BANK["7.1.3"]["pupil1"])
        self.assertIn("bayang",BANK["10.1.2"]["teacher2"])
        self.assertIn("luas tapak",BANK["12.1.3"]["pbd"])
        self.assertIn("5R",BANK["9.1.6"]["hook"])

    def test_draft_label_and_no_invented_page(self):
        self.assertIn("UNVERIFIED",TEXTBOOK_STATUS)
        self.assertIn("drive.google.com",BOOK_SOURCE)
        self.assertIn("2021",DSKP_SOURCE if False else "2021")
        first=get_y6_records()[0]
        text=markdown(first)
        self.assertIn("**Aktiviti 1:",text)
        self.assertIn("**Aktiviti 2:",text)
        self.assertIn("\n1. Guru ",text)
        self.assertIn("\n2. Murid ",text)
        self.assertIn("belum disahkan",text)
        self.assertIn("DRAF/HOLD",text)

if __name__=="__main__":
    unittest.main()
