"""Protect the Y6 PdP006 draft from unsafe use or wrong SK/SP reuse."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "rph_standalone/matematik/staging_draf_y6_pdp006_pola_nombor_20261108.md"
LEDGER = ROOT / "audits/matematik_y6_pdp004_006_semantic_conflict_20261108.json"


class Y6SemanticHold(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.draft = DRAFT.read_text(encoding="utf-8")
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_primary_source_identifiers_and_scope(self):
        data = self.ledger
        self.assertEqual(data["reference_documents"]["telegram_database"]["table"],
                         "verified_pdp_sequence_v2")
        self.assertEqual(data["reference_documents"]["textbook"]["sha256"],
                         "5785f6a8e3027168d16a9eecd37ddc60e582b6dbda63a60f0651656be0a51d6e")
        cases = {r["native_pdp_code"]: r for r in data["cases"]}
        self.assertEqual(len(cases), 8)
        self.assertTrue({"MT6-PDP-004", "MT6-PDP-006", "MT6-PDP-079", "MT6-PDP-080", "MT6-PDP-081"} <= set(cases))
        self.assertEqual(cases["MT6-PDP-004"]["action"], "REVIEW_RPT_AND_PREREQUISITE_ONLY")
        self.assertEqual(cases["MT6-PDP-006"]["candidate_dskp_sp"], "1.1.2")
        self.assertEqual(cases["MT6-PDP-006"]["candidate_textbook_printed_pages"], [4,5,6,7,8])
        self.assertEqual(data["approved_count"], 0)
        self.assertFalse(data["final_ready"])
        self.assertFalse(data["production_modified"])

    def test_pdp006_draft_has_all_teaching_phases_and_pbd(self):
        draft = self.draft
        for s in ("MT6-PDP-006", "Pola Nombor", "SP asal Telegram", 
                  "1.4.1", "1.1.2", "4–8", "Objektif pembelajaran",
                  "Set induksi", "Aktiviti 1", "Aktiviti 2", "Aktiviti 3",
                  "PBD individu", "Penutup", "Kriteria kejayaan", "Refleksi guru",
                  "BELUM DILULUSKAN", "Bukan RPH pengguna"):
            with self.subTest(label=s):
                self.assertIn(s, draft)
        self.assertIn("**Masa cadangan:** 60 minit", draft)
        self.assertIn("5 minit", draft)
        self.assertIn("15 minit", draft)
        self.assertIn("20 minit", draft)
        self.assertIn("hingga 10 juta", draft)

    def test_not_a_production_map(self):
        self.assertIn("Jangan guna draf ini dalam penjana Word/PDF", self.draft)
        self.assertIn("bukan pembetulan kod dalam Telegram", self.draft)


if __name__ == "__main__":
    unittest.main()
