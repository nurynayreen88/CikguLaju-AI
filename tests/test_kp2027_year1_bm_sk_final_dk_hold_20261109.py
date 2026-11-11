"""Check that the 2026-11-09 BM Year 1 DK search cannot mark drafts READY."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "curriculum" / "kp2027" / "year1"


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class BMT1FinalDKSourceHold(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load("bm_sk_final_dk_source_check_20261109.json")
        cls.master = load("bm_sk_26_training_sp_draft_master_20261107.json")

    def test_2027_bm_sk_final_subject_dk_not_claimed(self):
        a = self.audit
        self.assertEqual(a["curriculum"], "KP2027")
        self.assertEqual(a["school_stream"], "SK")
        self.assertEqual(a["source_status"], "FINAL_SUBJECT_DK_NOT_RETRIEVED")
        self.assertEqual(a["release_status"], "DRAFT_HOLD_NOT_READY")
        checks = a["checks"]
        self.assertIs(checks["has_original_final_dk_pdf"], False)
        self.assertIsNone(checks["original_final_dk_sha256"])
        for key in ("official_sk_sp_spi_transcribed",
                    "school_stream_separation_proven_in_final_dk",
                    "textbook_kp2027_pages_confirmed",
                    "ready_for_rph_word_pdf", "ready_for_web",
                    "ready_for_telegram"):
            self.assertIs(checks[key], False)

    def test_training_candidates_remain_non_public(self):
        a = self.audit["drafts"]
        m = self.master
        self.assertEqual(a["bm_sk_training_candidates"], 26)
        self.assertEqual(a["verified_against_final_dk"], 0)
        self.assertEqual(a["approved_for_release"], 0)
        self.assertEqual(m["release_status"], "DRAFT_HOLD_NOT_READY")
        self.assertFalse(m["gate"]["final_dk_document_received"])
        self.assertEqual(m["coverage"]["approved_rph"], 0)
        for row in m["records"]:
            self.assertEqual(row["school_type"], "SK")
            self.assertEqual(row["release_status"], "DRAFT_HOLD_NOT_READY")
            self.assertFalse(row["sp_candidate"]["final_dk_verified"])
            self.assertIsNone(row["official_sp"])
            self.assertIsNone(row["official_spi"])
            self.assertFalse(row["ready_for_web"])
            self.assertFalse(row["ready_for_telegram"])

    def test_sources_are_leads_not_final_subject_dk(self):
        sources = self.audit["source_audit"]
        self.assertGreaterEqual(len(sources), 4)
        self.assertFalse(any(s["role"] == "VERIFIED_FINAL_SUBJECT_DK"
                             for s in sources))


if __name__ == "__main__":
    unittest.main()
