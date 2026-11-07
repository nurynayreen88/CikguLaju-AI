"""Reviewer-only paper layout normalization must not invent official SP."""
import unittest
from pi_held_six_editor_candidate_packet import audit
from pi_held_six_word_pdf_print_audit import normalize


class PIHeldSixLayoutNormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[normalize(row) for row in audit()["rows"]]

    def test_all_six_have_full_reviewer_layout_fields(self):
        self.assertEqual(len(self.rows),6)
        self.assertEqual([x["id"] for x in self.rows],
                         ["T2-L035","T6-L006","T6-L014",
                          "T6-L018","T6-L060","T6-L117"])
        for row in self.rows:
            self.assertTrue(all(row["fields"].values()))
            self.assertEqual(len(row["fields"]["aktiviti_utama"].splitlines()),4)
            self.assertTrue(row["fields"]["penutup"])
            self.assertTrue(row["fields"]["bahan"])

    def test_source_only_no_fake_sp(self):
        l35=self.rows[0]
        self.assertIn("224–245",l35["fields"]["sp"])
        l60=self.rows[4]
        for code in ("4.2.3","4.2.4","4.2.5"):
            self.assertIn(code,l60["fields"]["sp"])
        for row in self.rows:
            self.assertNotIn("FINAL READY",str(row))


if __name__=="__main__":
    unittest.main()
