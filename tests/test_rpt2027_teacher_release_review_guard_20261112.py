"""Teacher-output release guard for the 56-PDF RPT 2027 preview.

The unchanged Music PDFs can still carry draft source-page qualifiers.
Keep a release HOLD without mutating source PDFs or legitimate DSKP wording.
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
        self.assertEqual(report["unchanged"], 33)
        self.assertFalse(report["ready_for_web_catalog"])
        self.assertTrue(report["teacher_release_blocked"])
        self.assertFalse(manifest["ready_for_web_catalog"])
        self.assertTrue(manifest["teacher_release_blocked"])
        self.assertFalse(manifest["academic_final_approved"])
        expected_music = {f"muzik:{year}" for year in range(2, 7)}
        found = set(report["printed_internal_note_affected_files"])
        self.assertTrue(expected_music.issubset(found), found)
        self.assertGreaterEqual(report["printed_internal_note_finding_count"], 175)
        self.assertEqual(
            found, set(manifest["printed_internal_note_affected_files"])
        )


if __name__ == "__main__":
    unittest.main()
