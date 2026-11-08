"""Detect recurrence of badal/'iwad mixups in PI tajwid RPH."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pi_quality_audit import ROOT, COUNT
from pi_tajwid_crossfield_mad_audit import audit, kinds

class PITajwidMadCrossfieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.result=audit()

    def test_all_30_single_target_mad_source_rph(self):
        d=self.result
        self.assertEqual(d["source_catalog_total"],696)
        self.assertEqual(d["single_named_mad_source_lessons_checked"],30)
        self.assertEqual(d["conflicting_mad_labels_remaining"],0)
        self.assertEqual(d["source_corrected_year5_lessons"],3)
        self.assertEqual(d["source_corrected_fields"],7)
        self.assertEqual({x["id"] for x in d["source_corrections"]},
                         {"T5-L041","T5-L045","T5-L049"})
        self.assertEqual(d["expert_tajwid_approvals"],0)
        self.assertEqual(d["teacher_ready"],0)
        self.assertFalse(d["source_rpt_modified"])
        self.assertEqual(d["release"],"NO_GO")
        self.assertTrue(all(x["conflicting_other_mad_count"]==0 and
                            x["expert_tajwid_approved"] is False
                            for x in d["rows"]))

    def test_guard_recognizes_distinct_hukum(self):
        self.assertEqual(kinds("مد عوض مد عوض"),{"عوض"})
        self.assertEqual(kinds("مد بدل مد عوض"),{"بدل","عوض"})
        self.assertEqual(kinds("مد بدل"),{"بدل"})

    def test_mismatched_original_pbd_is_rejected_by_guard(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)
            for year in COUNT:
                (p/f"year{year}.json").write_bytes((ROOT/f"year{year}.json").read_bytes())
            y5=p/"year5.json"
            doc=json.loads(y5.read_text(encoding="utf-8"))
            item=next(x for x in doc["records"] if x["id"]=="T5-L049")
            current=item["fields"]["pentaksiran"]
            self.assertIn("مد عوض",current)
            item["fields"]["pentaksiran"]=current.replace("مد عوض","مد بدل")
            y5.write_text(json.dumps(doc,ensure_ascii=False),encoding="utf-8")
            with self.assertRaisesRegex(AssertionError,"Source tajwid hukum differs"):
                audit(p)

if __name__=="__main__":unittest.main()
