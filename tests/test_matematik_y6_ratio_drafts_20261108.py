"""Verify source-labelled Y6 ratio/proportion teaching drafts are never published early."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "rph_standalone/matematik/staging_draf_y6_pdp079_081_nisbah_kadaran_20261108.md"
LEDGER = ROOT / "audits/matematik_y6_pdp004_006_semantic_conflict_20261108.json"


class MathY6RatioDrafts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.draft = DRAFT.read_text(encoding="utf-8")
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_verified_primary_book_part3_mapping_is_a_candidate_only(self):
        src = self.ledger["reference_documents"]["textbook_part3"]
        self.assertEqual(src["sha256"],
                         "35006f052cea2a327415c816e08a061c963b1bf56f3fc5346ca2a491fff52571")
        cases = {c["native_pdp_code"]: c for c in self.ledger["cases"]}
        expected = {
            "MT6-PDP-079": ("8.1.1", "7.2.1", [191, 196]),
            "MT6-PDP-080": ("8.2.1", "7.3.1", [197, 200]),
            "MT6-PDP-081": ("8.3.1", "7.4.1", [201, 204]),
        }
        for pdp, (native_sp, candidate_sp, printed_range) in expected.items():
            with self.subTest(pdp=pdp):
                r=cases[pdp]
                self.assertEqual(r["native_sp"], native_sp)
                self.assertEqual(r["candidate_dskp_sp"], candidate_sp)
                self.assertEqual(r["candidate_textbook_printed_pages"], printed_range)
                self.assertFalse(r["ready"])
        self.assertFalse(self.ledger["final_ready"])
        self.assertFalse(self.ledger["production_modified"])

    def test_three_distinct_standalone_rph_drafts_have_teaching_actions(self):
        body = self.draft
        for pdp in ("MT6-PDP-079", "MT6-PDP-080", "MT6-PDP-081"):
            self.assertEqual(body.count("## PdP " + pdp + " —"), 1)
        for label in ("**Objektif:**", "**Set induksi", "**Aktiviti 1",
                      "**Aktiviti 2", "**Aktiviti 3", "PBD individu",
                      "**Penutup", "**BBM", "**Kriteria", "60 minit",
                      "191–196", "197–200", "201–204", "BELUM DILULUSKAN"):
            with self.subTest(label=label):
                self.assertIn(label, body)
        self.assertIn("**SP asal Telegram:** 8.1.1", body)
        self.assertIn("**SP asal Telegram:** 8.2.1", body)
        self.assertIn("**SP asal Telegram:** 8.3.1", body)

    def test_no_unsanctioned_activation_or_automatic_sp_rewrite(self):
        self.assertIn("tidak mengubah DB Telegram", self.draft)
        self.assertIn("fungsi Word/PDF dan kuota pengguna **tidak diubah**", self.draft)
        self.assertIn("BELUM DILULUSKAN", self.draft)


if __name__ == "__main__":
    unittest.main()
