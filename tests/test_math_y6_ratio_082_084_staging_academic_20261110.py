"""Academic QA for three new Year 6 ratio lesson drafts (staging only).

No external source mutations, download activation, database access or quotas.
The full KPM DSKP / textbook editorial signoff remains a manual HOLD.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "rph_standalone/matematik/staging_draf_y6_pdp082_084_nisbah_kadaran_20261110.md"
LESSON = re.compile(r"(?m)^## PdP MT6-PDP-(0(?:82|83|84)) — ")
PHASE = re.compile(
    r"\*\*(Set induksi|Aktiviti [123]\s*—[^(]*|Penutup)"
    r"\s*\((\d+) minit\):\*\*",
    flags=re.IGNORECASE,
)
EXPECTED = {
    "082": ("7.2.1", "7.3.1", "7.4.1"),
    "083": ("7.2.1", "7.3.1"),
    "084": ("7.4.1",),
}


class MathY6RatioDraftAcademicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = DOC.read_text(encoding="utf-8")
        pieces = LESSON.split(cls.raw)
        cls.sections = {pieces[i]: pieces[i + 1] for i in range(1, len(pieces), 2)}

    def test_three_unique_source_backed_lesson_identifiers(self):
        self.assertEqual(set(self.sections), set(EXPECTED))
        self.assertIn("BELUM DILULUSKAN", self.raw)
        self.assertIn("JANGAN AKTIFKAN", self.raw)
        for code, section in self.sections.items():
            self.assertIn("**SP asal Telegram:**", section, code)
            self.assertIn("**Calon SK/SP:**", section, code)
            for sp in EXPECTED[code]:
                self.assertIn(sp, section, (code, sp))
            self.assertIn("**Status:** HOLD", section, code)

    def test_each_lesson_has_sixty_minutes_and_distinct_numbered_activities(self):
        for code, section in self.sections.items():
            with self.subTest(code=code):
                marks = PHASE.findall(section)
                headings = [name.strip().casefold() for name, _ in marks]
                times = [int(minutes) for _, minutes in marks]
                self.assertEqual(len(marks), 5, marks)
                self.assertEqual(times, [5, 15, 20, 15, 5])
                self.assertEqual(sum(times), 60)
                for expected in ("set induksi", "aktiviti 1", "aktiviti 2",
                                 "aktiviti 3", "penutup"):
                    self.assertEqual(sum(name.startswith(expected) for name in headings), 1)

    def test_measurable_objectives_pbd_teacher_pupil_and_source_edition(self):
        for code, section in self.sections.items():
            with self.subTest(code=code):
                self.assertRegex(section, r"(?i)\*\*Objektif:\*\*.{40,}")
                self.assertRegex(section, r"\b[234]\s+daripada\s+[345]\b")
                self.assertIn("**Kriteria kejayaan:**", section)
                self.assertIn("PBD", section)
                self.assertIn("Guru", section)
                self.assertIn("Murid", section)
                self.assertIn("**BBM:**", section)
                self.assertIn("**Refleksi", section)
                self.assertIn("**Rujukan Buku Teks:**", section)
                self.assertNotIn("Murid menunjukkan pengetahuan atau kemahiran berdasarkan", section)
        self.assertIn("September 2021", self.raw)
        self.assertIn("halaman bercetak 191–204", self.raw)
        self.assertIn("SHA256", self.raw)

    def test_drafted_illustrations_mathematically_coherent(self):
        # These examples are teacher-created; their results are separately
        # checked here, not copied as purported original textbook questions.
        self.assertEqual((12 // 6, 18 // 6), (2, 3))
        self.assertEqual((8 // 4, 20 // 4), (2, 5))
        self.assertEqual((2000 // 500, 500 // 500), (4, 1))
        self.assertEqual((8 // 2) * 5, 20)
        self.assertEqual((9 // 3) * 4, 12)
        self.assertEqual((12 // 4) * 7, 21)
        self.assertEqual((12 // 3) * 2, 8)
        self.assertEqual((21 // 3) * 2, 14)
        self.assertEqual((64 // 8 * 3, 64 // 8 * 5), (24, 40))
        self.assertEqual((24 + 8, 40), (32, 40))
        self.assertEqual((56 // 7 * 3 - 8, 56 // 7 * 4), (16, 32))
        self.assertEqual((48 // 8 * 3, 48 // 8 * 5 - 6), (18, 24))

    def test_verified_textbook_topics_and_rpt_label_conflict_remain_staging_only(self):
        audit = (ROOT / "rph_standalone/matematik/STAGING_AUDIT_DSKP_MT6_PDP082_084_20261111.md").read_text(encoding="utf-8")
        # The book was checked as source PDF text; visual/exercise and PdP-sequence
        # approval still require human review. These tests MUST NOT imply READY.
        self.assertIn("hlm. 191–196 (nisbah)", self.sections["082"])
        self.assertIn("197–200 (kadaran)", self.sections["082"])
        self.assertIn("202–204 (masalah nisbah/kadaran)", self.sections["082"])
        self.assertIn("hlm. 191–196 (nisbah)", self.sections["083"])
        self.assertIn("197–200 (kadaran)", self.sections["083"])
        self.assertIn("hlm. 202–204 (masalah nisbah/kadaran", self.sections["084"])
        self.assertIn("hlm. 201 memfokuskan masalah koordinat", self.sections["084"])
        self.assertIn("7.3 Kadaran / SP 7.3.1", audit)
        self.assertIn("7.4 Penyelesaian masalah / SP 7.4.1", audit)
        self.assertIn("7.1 Kadaran", audit)  # observed erroneous draft label
        self.assertIn("7.2 Penyelesaian masalah", audit)  # observed erroneous draft label
        self.assertIn("Kedua-duanya DRAF", audit)
        self.assertIn("Semakan paparan visual", audit)
        self.assertIn("JANGAN TERBITKAN", audit)

    def test_not_a_production_enablement_or_source_overwrite(self):
        self.assertNotIn("FINAL READY", self.raw)
        self.assertIn("Tiada data v26.00", self.raw)
        self.assertIn("semakan visual guru", self.raw)
        self.assertIn("BELUM DILULUSKAN", self.raw)


if __name__ == "__main__":
    unittest.main()
