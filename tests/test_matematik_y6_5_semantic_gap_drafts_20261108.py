"""Check 5 focused Y6 source-grounded decimal/percent/measurement drafts."""
from decimal import Decimal
from pathlib import Path
import json
import re
import unittest
from tools.build_matematik_y6_staging_rph_a4_20261108 import load_drafts, CANDIDATES

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"rph_standalone/matematik/staging_draf_y6_5_pdp_semantic_gap_20261108.md"
INV=ROOT/"audits/matematik_v60_dskp_primary_sp_inventory_20261108.json"
EXPECTED={
    "FIX6-01":("2.2.1","68–69","Darab Perpuluhan"),
    "FIX6-02":("2.2.2","70–72","Bahagi Perpuluhan"),
    "FIX6-03":("2.3.1","73–74","Perpuluhan kepada Peratus"),
    "FIX6-04":("2.3.3","77–79","Nilai Peratus"),
    "FIX6-05":("5.1.1","155–157","Panjang dengan Jisim"),
}

class FiveMathsGapDrafts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=SRC.read_text(encoding="utf-8")
        cls.drafts={d.code:d for d in load_drafts() if d.code.startswith("FIX6")}
        cls.official=set(json.loads(INV.read_text(encoding="utf-8"))["documents"]["6"]["sp_codes"])

    def test_exact_five_distinct_sp_with_book_pages_and_no_native_alias(self):
        self.assertEqual(set(self.drafts),set(EXPECTED))
        self.assertEqual(len(self.drafts),5)
        for code,(sp,pages,title) in EXPECTED.items():
            with self.subTest(code=code):
                self.assertIn(sp,self.official)
                self.assertEqual(CANDIDATES[code],("TIADA",sp,pages))
                self.assertIn(title.casefold(),self.drafts[code].title.casefold())
                self.assertIn("Objektif",self.drafts[code].body)
                self.assertIn("PBD",self.drafts[code].body)
                self.assertNotIn("Nota pembangun",self.drafts[code].body)
                self.assertNotIn("BELUM DILULUSKAN",self.drafts[code].body)

    def test_five_session_times_and_teaching_phases(self):
        sections=re.split(r"(?m)^## Calon FIX6-\d\d — ",self.text)[1:]
        self.assertEqual(len(sections),5)
        for i,sec in enumerate(sections,1):
            with self.subTest(i=i):
                for label in ("**Objektif:**","**BBM:**","**Set induksi (5 minit):**",
                              "**Aktiviti 1","**Aktiviti 2","**Aktiviti 3",
                              "**Penutup (5 minit):**","**Kriteria kejayaan:**",
                              "**Status:** BELUM DILULUSKAN"):
                    self.assertIn(label,sec)
                self.assertEqual([int(x) for x in re.findall(r"\((\d+) minit\):",sec)],
                                 [5,15,20,15,5])

    def test_original_math_worked_examples_are_arithmetically_correct(self):
        D=Decimal
        self.assertEqual(D("0.6")*D("0.39"),D("0.234"))
        self.assertEqual(D("1.2")*D("0.35"),D("0.42"))
        self.assertEqual(D("2.5")*D("0.08"),D("0.2"))
        self.assertEqual(D("0.8")*D("0.125"),D("0.1"))
        self.assertEqual(D("0.1")/D("0.002"),D("50"))
        self.assertEqual(D("7.2")/D("0.75"),D("9.6"))
        self.assertEqual(D("3.417")/D("3.4"),D("1.005"))
        self.assertEqual(D("1.75")*100,D("175"))
        self.assertEqual(D("0.9")*D("2.5"),D("2.25"))
        self.assertEqual(D("1.25")*D("8"),D("10"))
        self.assertEqual(D("1.6")*D("1.5"),D("2.4"))
        self.assertEqual(D("1.75")/D("1.4")*100,D("125"))
        self.assertEqual(D("0.6")/D("3")*D("8"),D("1.6"))
        self.assertEqual(D("1.25")/D("5")*D("8"),D("2"))
        self.assertTrue("5.1.1(ii) dan (iii) perlu PdP lain" in self.text)

if __name__=="__main__":
    unittest.main()
