"""Source-gated review checks for 26 Year-1 SK BM lesson candidates from a training PDF.

These tests establish internal consistency only, not approval of a final DK.
"""
import json
from collections import Counter
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "curriculum" / "kp2027" / "year1"
MASTER = "bm_sk_26_training_sp_draft_master_20261107.json"
SOURCE_INDEX = "bm_year1_training_sp_page_index_20261107_v2_SK_SJK.json"
EXPECTED_COUNTS = {"Mendengar": 7, "Bertutur": 8, "Membaca": 6, "Menulis": 5}

def load(filename):
    return json.loads((ROOT / filename).read_text(encoding="utf-8"))

class BMYear1SK26CandidateGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master = load(MASTER)
        cls.index = load(SOURCE_INDEX)

    def test_exactly_one_candidate_per_training_code(self):
        rows = self.master["records"]
        idxcodes = [r["code"] for r in self.index["code_page_index"]]
        actualcodes = [r["sp_candidate"]["code"] for r in rows]
        self.assertEqual(len(rows), 26)
        self.assertEqual(Counter(r["skill"] for r in rows), EXPECTED_COUNTS)
        self.assertEqual(len(set(actualcodes)), 26)
        self.assertEqual(set(actualcodes), set(idxcodes))
        self.assertEqual(self.master["coverage"]["by_skill"], EXPECTED_COUNTS)
        self.assertEqual(self.master["coverage"]["final_dk_sp_verified"], 0)
        self.assertEqual(self.master["coverage"]["approved_rph"], 0)
        self.assertEqual(self.master["school_type"], "SK")
        self.assertEqual(self.master["release_status"], "DRAFT_HOLD_NOT_READY")
        self.assertEqual(self.master["source"]["sha256"],
            "447b499db78253c4c3f0559afa791691a010c58d076666917a060531b9637691")

    def test_standards_keep_training_provenance_and_release_hold(self):
        rows = self.master["records"]
        ids = [r["id"] for r in rows]
        self.assertEqual(len(set(ids)), 26)
        self.assertFalse(self.master["gate"]["final_dk_document_received"])
        self.assertFalse(self.master["gate"]["web_publish_disabled"] is False)
        for r in rows:
            with self.subTest(lesson=r["id"]):
                self.assertEqual(r["school_type"], "SK")
                self.assertEqual(r["level"], "Tahun 1")
                self.assertEqual(r["release_status"], "DRAFT_HOLD_NOT_READY")
                self.assertFalse(r["sp_candidate"]["final_dk_verified"])
                self.assertTrue(r["sp_candidate"]["text"].strip())
                self.assertTrue(all(1 <= p <= 118 for p in r["sp_candidate"]["source_pdf_pages_one_based"]))
                for key in ("official_sk", "official_sp", "official_spi", "official_book_page", "duration_minutes"):
                    self.assertIsNone(r[key])
                for key in ("academic_approved", "ready_for_web", "ready_for_telegram", "rpt_scheduled"):
                    self.assertIs(r[key], False)
                self.assertEqual([s["phase"] for s in r["stages"]],
                    ["Set induksi", "Aktiviti 1", "Aktiviti 2", "Pengukuhan/PBD dan penutup"])
                self.assertTrue(r["materials"])
                self.assertTrue(r["character_values"])
                self.assertGreater(len(r["objective_candidate"]), 70)
                self.assertGreater(len(r["formative_assessment"]), 40)
                for s in r["stages"]:
                    self.assertGreater(len(s["teacher_action"]), 60)
                    self.assertGreater(len(s["pupil_action"]), 45)

    def test_school_stream_wording_must_not_be_conflated(self):
        rows = {r["sp_candidate"]["code"]: r for r in self.master["records"]}
        for pair in self.index["school_stream_verified_variants"]:
            if pair["type"] == "SK":
                self.assertEqual(rows[pair["code"]]["sp_candidate"]["text"], pair["text"])
        self.assertIn("rumah dan di sekolah", rows["2.2.1"]["sp_candidate"]["text"])
        self.assertIn("berdasarkan konteks", rows["2.2.2"]["sp_candidate"]["text"])
        self.assertEqual(rows["1.2.2"]["sp_candidate"]["enumerated_source_items"],
                         ["ucapan selamat", "ucapan penghargaan", "permohonan maaf"])
        self.assertEqual(self.master["gate"]["school_stream"], "SK")

    def test_training_spi_tables_are_cited_but_never_auto_assigned(self):
        spi = load("bm_sk_training_spi_4skills_tp1_tp3_20261107.json")
        v2 = load("bm_sk_26_training_sp_draft_master_20261107_v2_spi_refs.json")
        self.assertEqual(spi["release_status"], "TRAINING_REFERENCE_HOLD_NOT_OFFICIAL_DK")
        self.assertFalse(spi["claimed_final_dk_spi_verified"])
        self.assertEqual(spi["source_pages_visual_reviewed"], [33, 62, 91, 114])
        self.assertEqual(len(spi["rows"]), 12)
        for skill, n in EXPECTED_COUNTS.items():
            rows = [r for r in spi["rows"] if r["skill"] == skill]
            self.assertEqual({r["training_tp_level"] for r in rows}, {1, 2, 3})
            self.assertTrue(all(r["training_tafsiran_text"] for r in rows))
            self.assertTrue(all(not r["auto_assign_tp"] for r in rows))
        self.assertEqual(v2["source_skills_spi_index"],
                         "bm_sk_training_spi_4skills_tp1_tp3_20261107.json")
        self.assertTrue(v2["assessment_policy"]["do_not_auto_assign_tp"])
        self.assertEqual(len(v2["records"]), 26)
        old_by_id = {r["id"]: r for r in self.master["records"]}
        for r in v2["records"]:
            with self.subTest(lesson=r["id"]):
                self.assertEqual(r["sp_candidate"], old_by_id[r["id"]]["sp_candidate"])
                self.assertEqual(r["stages"], old_by_id[r["id"]]["stages"])
                self.assertEqual(r["spi_training_reference"]["skill"], r["skill"])
                self.assertEqual(r["spi_training_reference"]["training_levels"], [1, 2, 3])
                self.assertTrue(r["spi_training_reference"]["auto_tp_assignment_prohibited"])
                self.assertFalse(r["spi_training_reference"]["original_final_dk_verified"])
                self.assertIsNone(r["official_spi"])
                self.assertFalse(r["ready_for_web"])

    def test_cross_file_assembly_is_lossless(self):
        files = self.master["input_files"]
        self.assertEqual(len(files), 4)
        all_source_rows = []
        for f in files:
            source = load(f)
            all_source_rows.extend(source["records"])
        self.assertEqual(len(all_source_rows), 26)
        by_id = {r["id"]: r for r in self.master["records"]}
        for r in all_source_rows:
            with self.subTest(source_id=r["id"]):
                merged = by_id[r["id"]]
                self.assertEqual(merged["sp_candidate"]["code"], r["sp_training_code"])
                self.assertEqual(merged["sp_candidate"]["text"], r["sp_training_text"])
                self.assertEqual(merged["stages"], r["stages"])

if __name__ == "__main__":
    unittest.main()
