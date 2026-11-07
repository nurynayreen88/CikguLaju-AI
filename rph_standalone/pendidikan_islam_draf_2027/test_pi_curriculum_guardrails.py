"""Content regression probes; not a professional Jawi/DSKP accreditation."""
import json
from pathlib import Path
import unittest
from pi_quality_audit import COUNT, HELD

ROOT = Path(__file__).resolve().parent


def load_all():
    return {(y, r["lesson"]): r
            for y in COUNT
            for r in json.loads((ROOT / f"year{y}.json").read_text(encoding="utf-8"))["records"]}


class PICurriculumGuardrails(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_all()

    def test_draft_safety_across_all_696(self):
        self.assertEqual(len(self.rows), 696)
        review = 0
        for (y, n), row in self.rows.items():
            self.assertIs(row["verified_ready"], False)
            self.assertEqual(row["withheld"], (y, n) in HELD)
            if (y, n) in HELD:
                self.assertNotIn("fields", row)
                continue
            fields = row["fields"]
            self.assertTrue(all(fields[k].strip() for k in
                ("sk","sp","objektif","set_induksi","aktiviti_utama","pentaksiran","penutup","bahan")))
            self.assertTrue(fields["aktiviti_utama"].lstrip().startswith("1. "))
            enriched = row.get("staging_enrichment")
            if enriched:
                review += 1
                self.assertIs(enriched["content_expert_approved"], False)
                self.assertEqual(enriched["publication"], "HOLD")
                self.assertIs(enriched["source_sp_unchanged"], True)
                self.assertTrue(enriched["original_activity"].strip())
                self.assertTrue(fields["pentaksiran"].strip())
        self.assertEqual(review, 560)

    def test_pbd_rewrite_preserves_original_and_stays_unapproved(self):
        refinements = []
        for (year, lesson), row in self.rows.items():
            if row["withheld"]:
                self.assertNotIn("staging_pbd_refinement", row)
                continue
            change = row.get("staging_pbd_refinement")
            if change is None:
                continue
            refinements.append((year, lesson))
            fields = row["fields"]
            self.assertIn("برداسركن كريتيريا دالم SP",
                          change["original_pentaksiran"])
            self.assertNotIn("برداسركن كريتيريا دالم SP",
                             fields["pentaksiran"])
            self.assertTrue(fields["pentaksiran"].startswith(
                change["original_pentaksiran"].split("ڤبد اينديويدو:")[0]))
            self.assertIn(change["assessment_criterion_review_only"],
                          fields["pentaksiran"])
            self.assertIn(change["observed_evidence_review_only"],
                          fields["pentaksiran"])
            self.assertIs(change["source_sk_sp_unchanged"], True)
            self.assertIs(change["book_or_verse_reference_added"], False)
            self.assertIs(change["jawi_orthography_approved"], False)
            self.assertIs(change["content_expert_approved"], False)
            self.assertIs(change["word_pdf_tested"], False)
            self.assertEqual(change["publication"], "HOLD")
        self.assertEqual(len(refinements), 43)
        self.assertEqual(sum(1 for y, _ in refinements if y == 2), 14)
        self.assertEqual(sum(1 for y, _ in refinements if y == 3), 29)

    def test_specific_2027_source_topic_corrections(self):
        yr3_87 = self.rows[(3, 87)]
        self.assertIn("منونتوت علمو", yr3_87["fields"]["sp"])
        self.assertIn("منونتوت علمو", yr3_87["fields"]["aktiviti_utama"])
        self.assertNotIn("ادب تيدور", yr3_87["fields"]["aktiviti_utama"])
        yr3_109 = self.rows[(3, 109)]
        self.assertIn("إقلاب", yr3_109["fields"]["sp"])
        self.assertIn("إقلاب", yr3_109["fields"]["aktiviti_utama"])
        self.assertNotIn("إخفاء حقيقي", yr3_109["fields"]["aktiviti_utama"])

    def test_khat_not_given_hamzah_treatment(self):
        for year in (5, 6):
            r = self.rows[(year, 111)]
            self.assertIn("خط", r["fields"]["sp"])
            self.assertEqual(r["staging_enrichment"]["category"], "khat")
            self.assertNotIn("كدودوقن حروف همزة", r["fields"]["aktiviti_utama"])

    def test_critical_holds_no_invented_scripture(self):
        unresolved = [(4, 83), (6, 137), (6, 141)]
        for key in unresolved:
            r = self.rows[key]
            self.assertIs(r["staging_source_review_required"], True)
            self.assertNotIn("staging_enrichment", r)
        self.assertIn("...", self.rows[(4, 83)]["fields"]["sp"])
        self.assertNotIn("أية", self.rows[(6, 137)]["fields"]["sp"])
        self.assertNotIn("أية", self.rows[(6, 141)]["fields"]["sp"])


if __name__ == "__main__":
    unittest.main()
