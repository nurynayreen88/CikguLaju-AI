"""All-subject staging source triage: no false academic percentages."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.audit_rph80_all_subject_sources_20261107 import (
    SUBJECTS, audit_markdown, inventory, structural_clues, subject_for_path,
)


class TestAllSubjectSourceTriage(unittest.TestCase):
    def test_subjects_are_exhaustive_for_primary_queue(self):
        self.assertEqual(len(SUBJECTS), 13)
        self.assertEqual(SUBJECTS[0], "Sains")
        self.assertEqual(SUBJECTS[-1], "Bahasa Inggeris")

    def test_pj_and_pk_stay_distinct(self):
        self.assertEqual(subject_for_path(Path(
            "rph_standalone/pjpk/year2_pj/lesson_001.md")), "Pendidikan Jasmani")
        self.assertEqual(subject_for_path(Path(
            "rph_standalone/pjpk/year2_pk/lesson_001.md")), "Pendidikan Kesihatan")

    def test_text_not_confused_with_quality(self):
        good = ("SK 2.1 SP 2.1.1 Buku Teks m/s5\n"
                "Set induksi Guru Murid\nAktiviti 1 Guru Murid\n"
                "Aktiviti 2 Guru Murid\nPBD Penutup\n")
        clues = structural_clues(good)
        self.assertTrue(all(v for k, v in clues.items() if k != "draft_or_hold_marker"))
        self.assertFalse(clues["draft_or_hold_marker"])

    def test_scanner_never_invents_quality_score(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            english = root / "rph_standalone/english/year2/lesson_001.md"
            science = root / "rph_standalone/sains/year3/lesson_001.md"
            moral = root / "rph_standalone/pendidikan_moral/year2/lesson_001.md"
            for path in (english, science, moral):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("SK SP DRAF\nGuru Murid\nAktiviti 1\nAktiviti 2\nPBD Penutup\n",
                                encoding="utf-8")
            result, summary = inventory(root=root)
            self.assertEqual(len(result), 3)
            self.assertEqual([x["subjek"] for x in result],
                             ["Sains", "Pendidikan Moral", "Bahasa Inggeris"])
            self.assertTrue(all(x["academic_quality_percent"] == "" for x in result))
            self.assertEqual(summary["quality_scores_verified"], 0)
            self.assertIsNone(summary["subjects"]["Matematik"]["quality_percent"])
            self.assertEqual(summary["subjects"]["Matematik"]["scan_count"], 0)


if __name__ == "__main__":
    unittest.main()
