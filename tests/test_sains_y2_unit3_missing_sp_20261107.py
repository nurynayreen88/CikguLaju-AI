"""Year2 KPM DSKP source conflict and missing Unit3 SP PBD gating.

Academic review remains external; tests prove only source semantics and
staging draft integrity. No official PdP IDs may be invented.
"""
import unittest
from tools.render_sains_y2_3_unmapped_sp_pbd_20261107 import TASKS,load_semantics,doc_path
from web.sains_y2_51_activities_draf_20261107 import BANK
from tools.render_sains_y2_51_rph_draf_20261107 import (
    SOURCE_CRITICAL_SHORT_NOTE,get_y2_records
)

class Year2Unit3SourceGap(unittest.TestCase):
    def test_three_content_sps_are_real_dskp_but_not_in_original_51_lessons(self):
        rows=load_semantics()
        self.assertEqual(set(rows),{"3.1.4","3.1.5","3.1.6"})
        self.assertEqual(len(BANK),51)
        self.assertTrue(set(rows).isdisjoint(BANK))
        self.assertIn("anak mewarisi ciri",rows["3.1.4"]["official_dskp_text"])
        self.assertIn("Memberi contoh ciri",rows["3.1.5"]["official_dskp_text"])
        self.assertIn("tumbesaran dan pewarisan",rows["3.1.6"]["official_dskp_text"])
        self.assertTrue(all(x["scheduled_pdp"] is None for x in rows.values()))
        self.assertEqual({sp:x["verified_textbook_printed_pages"] for sp,x in rows.items()},
                         {"3.1.4":[30],"3.1.5":[30,32],"3.1.6":[33]})
        self.assertEqual({sp:x["verified_activity_book_printed_pages"] for sp,x in rows.items()},
                         {"3.1.4":[17,18],"3.1.5":[18,19],"3.1.6":[20]})
        self.assertTrue(all(x["original_book_sp_labels_match"] for x in rows.values()))
        self.assertTrue(all(x["pedagogical_approved"] is False for x in rows.values()))

    def test_three_original_task_sheets_not_marked_official(self):
        self.assertEqual(len(TASKS),3)
        for sp,task in TASKS.items():
            self.assertEqual(len(task["criteria"]),3,sp)
            self.assertTrue(all(len(task[f"task{i}"])>50 for i in (1,2,3)))
            self.assertTrue(all("guru" in task["safety"].lower() or "murid" in task["safety"].lower() for _ in [1]))
            self.assertIn("BUKAN_PDP_RASMI",doc_path(sp).name)

    def test_fifty_one_source_ids_and_conflicts_preserved(self):
        entries=get_y2_records()
        self.assertEqual(len(entries),51)
        self.assertEqual({e["pdp_code"] for e in entries},
                         {f"SCI-Y2-PDP-{i:03d}" for i in range(1,52)})
        self.assertTrue(all(e["quality_score_percent"] is None and e["release"]=="DRAF_HOLD" for e in entries))
        self.assertEqual(set(SOURCE_CRITICAL_SHORT_NOTE),{"3.1.3","10.1.6"})
        notes={e["sp"]:e["source_warning_short"] for e in entries}
        self.assertIn("perbezaan tumbesaran",notes["3.1.3"])
        self.assertIn("3.1.4-3.1.6",notes["3.1.3"])
        self.assertIn("campuran",notes["10.1.6"])
        self.assertIn("BUKAN petikan SP rasmi",notes["10.1.6"])
        self.assertTrue(all(not notes[sp] for sp in BANK if sp not in SOURCE_CRITICAL_SHORT_NOTE))

    def test_separate_sheets_do_not_overwrite_official_workbook_mapping(self):
        from tools.sains_buku_aktiviti_mapping_20261107 import load_activity_books
        source=load_activity_books()[2]
        self.assertEqual(len(source),51)
        self.assertTrue(all(e["sp"] not in TASKS for e in source.values()))

if __name__=="__main__":
    unittest.main()
