"""Three finance drafts are content candidates, never native Year6 Telegram replacements."""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"rph_standalone/matematik/staging_draf_y6_rpt2027_wang_3_sumber_primer_20261108.md"


class FinanceDraftContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=PATH.read_text(encoding="utf-8")

    def test_uses_actual_kpm_2021_financial_topics(self):
        s=self.text
        for token in ("FIN-T6-01","FIN-T6-02","FIN-T6-03",
                      "3.1.1","3.2.1","3.3.1",
                      "103–106","121–122","123–130",
                      "RPT Matematik Tahun 6 2027", "Kumpulan A dan B",
                      "blok kandungan 010", "011 Insurans/Takaful",
                      "012 Penyelesaian Masalah Wang"):
            with self.subTest(token=token):
                self.assertIn(token,s)

    def test_each_has_full_pdp_and_pbd(self):
        sections=re.split(r"^## Calon FIN-T6-",self.text,flags=re.M)[1:]
        self.assertEqual(len(sections),3)
        for i,part in enumerate(sections,1):
            with self.subTest(section=i):
                for key in ("**Objektif:**","**Set induksi", "**Aktiviti 1",
                            "**Aktiviti 2","**Aktiviti 3", "**Penutup",
                            "**Kriteria kejayaan", "BBM",
                            "60 minit", "PBD", "BELUM DILULUSKAN"):
                    self.assertIn(key,part)
                durations=[int(x) for x in re.findall(
                    r"\((\d+) minit\)",part)]
                self.assertEqual(durations, [5,15,20,15,5])
                self.assertEqual(sum(durations),60)

    def test_no_aliasing_old_native_lesson_numbers_or_publishing(self):
        s=self.text
        self.assertIn("tidak menggantikan PdP 034–045",s)
        self.assertIn("BELUM DILULUSKAN",s)
        self.assertIn("Jangan aktifkan",s)
        self.assertNotIn("final_ready=true",s)
        self.assertIn("RPT",s)


if __name__=="__main__":
    unittest.main()
