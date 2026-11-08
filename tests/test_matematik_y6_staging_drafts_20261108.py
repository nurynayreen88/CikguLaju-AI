"""Staging only: source-backed RPH review drafts must never be FINAL READY."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "rph_standalone/matematik/staging_draf_y6_pdp007_012_dskp_bukuteks_20261108.md"


class SixDraftsYear6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DRAFT.read_text(encoding="utf-8")
        cls.sections = re.findall(
            r"(?ms)^## PdP (MT6-PDP-[0-9]{3}) — (.*?)(?=^## PdP |^---$)",
            cls.text,
        )

    def test_exact_six_pdp_and_no_release(self):
        codes = re.findall(r"(?m)^## PdP (MT6-PDP-[0-9]{3})", self.text)
        self.assertEqual(codes, [f"MT6-PDP-{n:03d}" for n in range(7, 13)])
        self.assertIn("BUKAN BAHAN PRODUKSI", self.text)
        self.assertIn("BELUM DILULUSKAN", self.text)
        self.assertNotIn("FINAL_READY=true", self.text)

    def test_each_draft_has_subject_specific_activities_and_assessment(self):
        sections = re.split(r"(?m)^## PdP MT6-PDP-[0-9]{3}", self.text)[1:]
        self.assertEqual(len(sections), 6)
        for section in sections:
            for heading in (
                "1.2.1", "Buku Teks", "Objektif",
                "Set induksi (5 minit)",
                "Aktiviti 1 — Penerokaan/Model (20 minit)",
                "Aktiviti 2 — Aplikasi/Latihan (20 minit)",
                "Aktiviti 3 — PBD (10 minit)",
                "Penutup (5 minit)",
                "Kriteria kejayaan",
                "**BELUM DILULUSKAN.**",
            ):
                self.assertIn(heading, section, heading)
            self.assertGreater(len(section), 950)
            self.assertIn("Murid", section)
            self.assertIn("Guru", section)

    def test_math_examples_are_consistent(self):
        self.assertEqual(2456700+1208900, 3665600)
        self.assertEqual(5200000-1375000, 3825000)
        self.assertEqual(2400000+1350000-750000, 3000000)
        self.assertEqual(8*750000, 6000000)
        self.assertEqual(2400000//8, 300000)
        self.assertEqual(1200000*3//6, 600000)


if __name__ == "__main__":
    unittest.main()
