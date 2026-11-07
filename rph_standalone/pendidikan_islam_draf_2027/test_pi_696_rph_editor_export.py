"""All 696 proposed Pendidikan Islam RPH must have reviewable export fields."""
import unittest

from pi_696_rph_editor_export import gather, CRITICAL, HELD
from pi_quality_audit import COUNT, REQUIRED


class PIFullRPHReviewerExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=gather()

    def test_all_696_without_duplicate_or_loss(self):
        rows=self.rows
        self.assertEqual(len(rows),696)
        self.assertEqual(len({x["record"]["id"] for x in rows}),696)
        self.assertEqual({year:sum(x["record"]["tahun"]==year for x in rows)
                          for year in COUNT},COUNT)
        for row in rows:
            ident=row["record"]["id"]
            fields=row["record"]["fields"]
            self.assertTrue(all(isinstance(fields.get(k),str) and fields[k].strip()
                                for k in REQUIRED),ident)
            self.assertIn("1.",fields["aktiviti_utama"])
            self.assertIn("2.",fields["aktiviti_utama"])
            self.assertTrue(fields["penutup"])
            self.assertTrue(fields["bahan"])

    def test_held_and_critical_never_claim_to_be_ready(self):
        rows=self.rows
        held={x["record"]["id"] for x in rows
              if x["review_status"]=="ORIGINAL_HELD_EDITOR_CANDIDATE"}
        critical={x["record"]["id"] for x in rows
                  if x["review_status"]=="CRITICAL_SOURCE_HOLD"}
        self.assertEqual(held,HELD)
        self.assertEqual(critical,CRITICAL)
        self.assertEqual(sum(x["review_status"]=="UNVERIFIED_RPH_DRAFT"
                             for x in rows),687)
        self.assertEqual(sum(x["original_rumi_penutup"] is not None for x in rows),690)
        self.assertFalse(any("FINAL READY" in str(x["record"]) for x in rows))

if __name__=="__main__":
    unittest.main()
