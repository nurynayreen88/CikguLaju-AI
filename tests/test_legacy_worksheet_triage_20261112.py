"""Non-destructive quality triage contract for old worksheet records."""
import unittest
from pathlib import Path

from tools.triage_legacy_worksheet_candidates_20261112 import audit


class LegacyWorksheetTriageTests(unittest.TestCase):
    def test_original_five_banks_read_only_and_unapproved(self):
        root = Path(__file__).resolve().parents[1]
        output = audit(root)
        self.assertEqual(output["classification"], "INTERNAL_REVIEW_ONLY")
        self.assertEqual(output["production_worksheet_gate"], "OFF")
        self.assertEqual(output["approved_for_release"], 0)
        self.assertTrue(output["counts_are_records_not_final_worksheets"])
        self.assertGreater(output["worksheet_blueprint_count"], 100)
        self.assertEqual(output["worksheet_blueprint_count"], output["item_template_count"])
        self.assertGreater(output["shared_resource_records"], output["worksheet_blueprint_count"])
        self.assertGreater(output["visual_asset_records"], 0)
        self.assertTrue(all(v["status"] == "SAMPLE_NOT_APPROVED"
                            for v in output["review_samples"]))
        self.assertTrue(all(len(v["instructions"]) <= 135
                            for v in output["review_samples"]))
        self.assertTrue(all(len(v["question_pattern"]) <= 135
                            for v in output["review_samples"]))
        self.assertTrue(output["blueprint_year_subject"])
        # A source requiring manual review does not automatically become a
        # CikguLaju delivery record even if a legacy column says 'approved'.
        self.assertNotIn("ready_files", output)
        self.assertNotIn("public_links", output)

    def test_missing_bank_aborts_instead_of_fabricating_entries(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as root:
            with self.assertRaises(FileNotFoundError):
                audit(Path(root))


if __name__ == "__main__":
    unittest.main()
