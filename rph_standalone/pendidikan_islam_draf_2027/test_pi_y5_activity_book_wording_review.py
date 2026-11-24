"""Fail-closed audit: Year5 Jawi uses 'Buku Aktiviti' ambiguously 13 times."""
import unittest

from pi_y5_activity_book_wording_review import EXPECTED, TERM, audit


class PIYear5UnverifiedBookMentions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit()

    def test_exact_source_mentions_and_fields(self):
        result = self.result
        self.assertEqual(result["source_mentions_reviewed"], 13)
        self.assertEqual(result["year5_pentaksiran_mentions"], 9)
        self.assertEqual(result["year5_activity_mentions"], 4)
        self.assertEqual({x["id"]: x["field"] for x in result["rows"]}, EXPECTED)
        self.assertTrue(all(x["year"] == 5 for x in result["rows"]))
        self.assertTrue(all(TERM.search(x["source_excerpt"]) for x in result["rows"]))
        self.assertTrue(all(len(x["original_field_sha256"]) == 64 for x in result["rows"]))

    def test_nothing_handed_to_users_or_auto_rewritten(self):
        result = self.result
        self.assertEqual(result["official_year5_buku_aktiviti_pages_verified_by_this_audit"], 0)
        self.assertEqual(result["official_year5_buku_aktiviti_exercises_verified_by_this_audit"], 0)
        self.assertEqual(result["original_rph_edits"], 0)
        self.assertEqual(result["release"], "NO_GO")
        self.assertIsNone(result["academic_quality_percent"])
        for row in result["rows"]:
            self.assertFalse(row["official_book_edition_verified"])
            self.assertFalse(row["official_book_page_verified"])
            self.assertFalse(row["official_exercise_verified"])
            self.assertTrue(row["could_be_generic_activity_workbook"])
            self.assertFalse(row["original_rph_changed"])
            self.assertFalse(row["can_publish"])
            self.assertTrue(row["editor_next_step"])


if __name__ == "__main__":
    unittest.main()
