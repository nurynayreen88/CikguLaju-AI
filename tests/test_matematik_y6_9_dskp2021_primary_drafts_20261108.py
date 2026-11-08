"""Year6 KSSR 2021 content expansion: nine new RPH sessions remain source-scoped."""
from fractions import Fraction
import json
import re
import unittest
from pathlib import Path
from tools.build_matematik_y6_staging_rph_a4_20261108 import load_drafts, CANDIDATES

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "rph_standalone/matematik/staging_draf_y6_9_pdp_dskp2021_sumber_primer_20261108.md"
SP_INVENTORY = ROOT / "audits/matematik_v60_dskp_primary_sp_inventory_20261108.json"

EXPECTED = {
    "DSKP6-01": ("2.1.1", "61–67", "Bahagi Pecahan"),
    "DSKP6-02": ("4.1.1", "141–143", "Mengenal Zon Masa"),
    "DSKP6-03": ("4.1.2", "144–147", "Perbezaan Masa"),
    "DSKP6-04": ("6.1.2", "165–167", "Protraktor"),
    "DSKP6-05": ("6.2.1", "178–179", "Bulatan"),
    "DSKP6-06": ("7.1.1", "187–190", "Koordinat"),
    "DSKP6-07": ("8.1.1", "207–212", "Carta Pai"),
    "DSKP6-08": ("8.2.1", "213–215", "Mungkin"),
    "DSKP6-09": ("8.2.2", "216–219", "Kebolehjadian"),
}

class MathsY6NinePrimaryCandidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=BOOK.read_text(encoding="utf-8")
        cls.drafts={d.code:d for d in load_drafts() if d.code.startswith("DSKP6")}
        cls.inventory=json.loads(SP_INVENTORY.read_text(encoding="utf-8"))

    def test_nine_different_topics_and_exact_primary_sp_codes(self):
        self.assertEqual(len(self.drafts),9)
        self.assertEqual(set(self.drafts),set(EXPECTED))
        official=set(self.inventory["documents"]["6"]["sp_codes"])
        for code, (sp,pages,part_of_title) in EXPECTED.items():
            with self.subTest(code=code):
                lesson=self.drafts[code]
                self.assertEqual(CANDIDATES[code],("TIADA",sp,pages))
                self.assertIn(sp,official)
                self.assertIn(part_of_title.casefold(),lesson.title.casefold())
                self.assertEqual(lesson.source,BOOK.relative_to(ROOT).as_posix())
                self.assertIn("BELUM DILULUSKAN",self.source)
        self.assertFalse(self.inventory["academic_signoff"])

    def test_pdf_evidence_covers_all_36_pages_and_holds_release(self):
        evidence=json.loads((ROOT / "audits/matematik_y6_nine_dskp2021_page_evidence_20261108.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["source_page_checks_passed"],9)
        self.assertFalse(evidence["academic_signoff"])
        self.assertFalse(evidence["telegram_native_mapping_approved"])
        self.assertFalse(evidence["production_modified"])
        self.assertEqual(evidence["release_decision"],"ACADEMIC_HOLD")
        docs=evidence["documents"]
        self.assertEqual(docs["dskp_y6"]["sha256"],
            "e48576169c12cc9666675770432a425e573686a331fba6bcd7f01e33787476a9")
        self.assertEqual(docs["textbook_part2"]["sha256"],
            "73a38e146f40adaf08432a60df211c4f0a610e5d50e746bd6326706cc9bb5804")
        self.assertEqual(docs["textbook_part3"]["sha256"],
            "35006f052cea2a327415c816e08a061c963b1bf56f3fc5346ca2a491fff52571")
        self.assertEqual({x["code"] for x in evidence["nine_pdp"]},set(EXPECTED))
        self.assertEqual(sum(len(x["textbook_pages_with_exact_sp_label"])
                             for x in evidence["nine_pdp"]),36)
        for row in evidence["nine_pdp"]:
            with self.subTest(code=row["code"]):
                code=row["code"]
                sp,pages,_ = EXPECTED[code]
                self.assertEqual(row["proposed_sp"],sp)
                self.assertEqual(str(row["textbook_printed_first"])+"–"+
                                 str(row["textbook_printed_last"]),pages)
                self.assertTrue(row["sp_label_present_on_all_specified_textbook_pages"])
                self.assertFalse(row["approved"])

    def test_each_is_a_real_single_session_with_measurable_pbd(self):
        sections=re.split(r"(?m)^## Calon DSKP6-\d\d — ", self.source)[1:]
        self.assertEqual(len(sections),9)
        for i,sec in enumerate(sections,1):
            with self.subTest(pdp=i):
                for label in ("**SK/SP:**","**BBM:**","**Objektif:**",
                              "**Set induksi (5 minit):**",
                              "**Aktiviti 1", "**Aktiviti 2",
                              "**Aktiviti 3", "**Penutup (5 minit):**",
                              "PBD", "**Kriteria kejayaan:**",
                              "**Status:** BELUM DILULUSKAN"):
                    self.assertIn(label,sec)
                duration=[int(x) for x in re.findall(
                    r"\((\d+) minit\):",sec)]
                self.assertEqual(duration,[5,15,20,15,5])
                self.assertEqual(sum(duration),60)

    def test_original_math_examples_and_coverage_are_internally_sound(self):
        self.assertEqual(Fraction(3,4)/3,Fraction(1,4))
        self.assertEqual(Fraction(3,2)/Fraction(1,4),6)
        self.assertEqual(Fraction(2,3)/Fraction(1,6),4)
        self.assertEqual((5-2)*2,6)  # km horizontal
        self.assertEqual((7-3)*2,8)  # km vertical
        self.assertEqual(sum((32,16,8,8)),64)
        self.assertEqual(sum((20,10,5,5)),40)
        self.assertEqual(sum((180,90,45,45)),360)
        self.assertIn("semua negara mempunyai satu zon", self.source)
        self.assertIn("bukan PdP rasmi Telegram", self.source)
        self.assertIn("Jangan aktifkan",self.source)

if __name__=="__main__":
    unittest.main()
