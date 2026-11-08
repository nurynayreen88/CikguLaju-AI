"""Nine PI RPT2027 source discrepancies must be reviewed, not auto-published."""
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pi_rpt_source_errata_editor_register import audit, write


class RptSourceErrataEditorRegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=audit()

    def test_precise_scope_and_no_source_rewrite(self):
        result=self.data
        self.assertEqual(result["original_catalog_total"],696)
        self.assertEqual(result["rpt_source_conflict_lessons"],9)
        self.assertEqual(result["field_level_editor_comparisons"],13)
        self.assertEqual(result["surah_conflict_lessons"],7)
        self.assertEqual(result["puasa_conflict_lessons"],1)
        self.assertEqual(result["solat_objective_conflict_lessons"],1)
        self.assertEqual(result["rpt_source_documents_modified"],0)
        self.assertEqual(result["approved_for_automatic_rpt_update"],0)
        self.assertEqual(result["teacher_ready"],0)
        self.assertEqual(result["release"],"NO_GO")
        self.assertIsNone(result["academic_quality_percent"])
        self.assertEqual(len({x["id"] for x in result["issues"]}),9)
        self.assertEqual({x["id"] for x in result["issues"]},
                         {"T3-L059","T3-L086","T3-L089","T3-L093",
                          "T4-L009","T4-L013","T4-L081","T4-L085",
                          "T4-L107"})
        for record in result["issues"]:
            self.assertFalse(record["teacher_or_expert_approved"])
            self.assertFalse(record["jawi_expert_approved"])
            self.assertFalse(record["source_rpt_modified"])
            self.assertFalse(record["can_auto_patch_rpt"])
            self.assertTrue(record["rpt_visual_comparison_pending"])
            self.assertTrue(record["source_rpt_drive_id"])
            self.assertEqual(set(record["original_rph_fields"]),
                             set(record["proposed_editor_rph_fields"]))
            self.assertTrue(all(
                record["original_rph_fields"][k]!=new
                for k,new in record["proposed_editor_rph_fields"].items()
            ))

    def test_13_field_level_csv_provenance_and_holds(self):
        with TemporaryDirectory() as folder:
            jp=Path(folder)/"editor.json"
            cp=Path(folder)/"editor.csv"
            write(jp,cp)
            obj=json.loads(jp.read_text(encoding="utf-8"))
            self.assertEqual(obj["rpt_source_conflict_lessons"],9)
            with cp.open(encoding="utf-8-sig",newline="") as stream:
                records=list(csv.DictReader(stream))
            self.assertEqual(len(records),13)
            self.assertEqual(len({r["id"] for r in records}),9)
            self.assertEqual(sum(r["field"]=="objektif" for r in records),3)
            self.assertTrue(all(r["source_rpt_modified"]=="False" for r in records))
            self.assertTrue(all(r["teacher_or_expert_approved"]=="False" for r in records))
            self.assertTrue(all(r["rpt_visual_comparison_pending"]=="True" for r in records))
            self.assertTrue(all(r["release"]=="NO_GO" for r in records))
            self.assertTrue(all(r["original_rph"]!=r["proposed_editor_rph"] for r in records))
            fasting=[r for r in records if r["id"]=="T4-L107"]
            self.assertEqual(len(fasting),2)
            self.assertTrue(all(r["textbook_source_page"]=="130" for r in fasting))


if __name__=="__main__":
    unittest.main()
