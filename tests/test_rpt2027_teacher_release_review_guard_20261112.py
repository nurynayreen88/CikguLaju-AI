"""Teacher-output release guard for the 56-PDF RPT 2027 preview.

The 5 legacy Music PDFs are replaced in a REVIEW-ONLY package, after
proof of old editor notes and verification that new pages have none.
Keep release HOLD without mutating originals or legitimate DSKP wording.
"""
import json
import unittest
from pathlib import Path

from scripts.prepare_rpt2027_week01_web_candidate_20261110 import (
    teacher_pdf_review_markers,
)

REVIEW_REPORT = Path("output/rpt2027_week01_review/week01_candidate_review.json")
REVIEW_MANIFEST = Path(
    "output/rpt2027_week01_review/rpt_2027/web_2027_pdfs/manifest.json"
)


class TeacherReleaseReviewGuardTests(unittest.TestCase):
    def test_draft_page_reference_is_not_teacher_ready(self):
        findings = teacher_pdf_review_markers([
            "Minggu 1 PdP 001. BT m/s: 10 (draf). Audio: 1–4.",
        ])
        self.assertEqual(
            [(f["page"], f["rule"], f["count"]) for f in findings],
            [(1, "DRAFT_PARENTHESES", 1)],
        )

    def test_actual_status_note_is_detected(self):
        notes = teacher_pdf_review_markers([
            "Kandungan buku/RPT masih draf. PdP untuk sesi seterusnya.",
            "RPT masih draf, belum siap untuk pengguna."
        ])
        self.assertGreaterEqual(len(notes), 2)

    def test_teaching_word_draf_is_not_internal(self):
        clean = "3.3.1 Menulis draf dan menghasilkan penulisan imaginatif."
        self.assertEqual(teacher_pdf_review_markers([clean]), [])

    def test_all_pages_checked(self):
        data = teacher_pdf_review_markers([
            "PdP 001. Murid mengenal nombor.",
            "BT m/s 4 (draf).",
            "BT m/s 5 (draf).",
        ])
        self.assertEqual([row["page"] for row in data], [2, 3])

    def test_generated_package_stays_quarantined(self):
        if not (REVIEW_REPORT.exists() and REVIEW_MANIFEST.exists()):
            self.skipTest("Integrated review artifact is checked in CI after build")
        report = json.loads(REVIEW_REPORT.read_text("utf-8"))
        manifest = json.loads(REVIEW_MANIFEST.read_text("utf-8"))
        self.assertEqual(report["total"], 56)
        self.assertEqual(report["target_week01_fixes"], 23)
        self.assertEqual(report["target_music_teacher_pdf_fixes"], 5)
        self.assertEqual(report["changed"], 28)
        self.assertEqual(report["unchanged"], 28)
        self.assertFalse(report["ready_for_web_catalog"])
        self.assertTrue(report["teacher_release_blocked"])
        self.assertFalse(manifest["ready_for_web_catalog"])
        self.assertTrue(manifest["teacher_release_blocked"])
        self.assertFalse(manifest["academic_final_approved"])
        academic_holds = report["academic_source_holds_not_printed"]
        self.assertEqual(set(academic_holds), {
            "bahasa_melayu:2", "bahasa_melayu:3",
        })
        self.assertEqual({k: len(v) for k, v in academic_holds.items()}, {
            "bahasa_melayu:2": 2, "bahasa_melayu:3": 7,
        })
        self.assertEqual(manifest["academic_source_holds_total"], 9)
        self.assertEqual(manifest["academic_source_holds_not_printed"],
                         academic_holds)
        info = Path("output/rpt2027_week01_review/"
                    "BACA_DULU_RPT_2027_SEMAKAN_BUKAN_FINAL.txt")
        self.assertTrue(info.is_file())
        content = info.read_text("utf-8")
        self.assertIn("JANGAN EDAR", content)
        self.assertIn("9 rekod BM", content)
        self.assertIn("\n", content)
        expected_music = {f"muzik:{year}" for year in range(2, 7)}
        found = set(report["printed_internal_note_affected_files"])
        self.assertEqual(found, set(), "No editorial notes may remain in review PDFs")
        self.assertEqual(report["printed_internal_note_finding_count"], 0)
        self.assertEqual(manifest["printed_internal_note_finding_count"], 0)
        before = report["music_legacy_editorial_counts"]
        self.assertEqual(set(before), expected_music)
        self.assertGreaterEqual(sum(before.values()), 175)
        self.assertEqual(report["music_legacy_editorial_notes_removed"],
                         sum(before.values()))
        self.assertEqual(manifest["music_legacy_editorial_notes_removed"],
                         sum(before.values()))
        self.assertEqual(manifest["candidate_replaced_files"], 28)
        self.assertEqual(manifest["candidate_unchanged_files"], 28)
        files = {r["subject_year"]: r for r in report["files"]}
        for identity in expected_music:
            item = files[identity]
            self.assertEqual(item["change_reason"], "music_teacher_text_cleanup")
            self.assertTrue(item["changed"])
            self.assertGreater(item["baseline_music_editorial_note_count"], 0)
            self.assertEqual(item["teacher_pdf_review_marker_count"], 0)
            self.assertNotEqual(item["new_sha256"], item["old_sha256"])
        for identity, item in files.items():
            if item["change_reason"] == "original_bytes_retained":
                self.assertEqual(item["new_sha256"], item["old_sha256"])
        self.assertEqual(
            sum(1 for item in files.values() if not item["changed"]), 28
        )


if __name__ == "__main__":
    unittest.main()
