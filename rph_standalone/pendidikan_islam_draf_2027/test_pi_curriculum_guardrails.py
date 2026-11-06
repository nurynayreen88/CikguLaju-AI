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
