"""Focused PJPK 2027 content regression; not proof of 90% teacher approval."""
import unittest
from pathlib import Path
from scripts.check_pjpk_2027_curriculum_crosswalk import inspect

ROOT=Path(__file__).resolve().parents[1]
CHANGED={
    (2,"pj"):(1,3,5,8,11,12,13,14,15,16,17,21,28,29,30,34),
    (3,"pj"):(2,8,16,25),
    (4,"pj"):(20,),
    (5,"pj"):(8,27),
    (2,"pk"):(6,14,15,18,21,22,25,30,34),
    (3,"pk"):(6,7,10,11,14,15,18),
    (4,"pk"):(2,8),
    (5,"pk"):(2,9),
    (6,"pk"):(2,),
}
FOCUS={
    (2,"pj",5):("tali","lutut","mengayun"),
    (2,"pj",8):("lambung","tangkap"),
    (2,"pj",15):("tee","bet","pukul"),
    (2,"pj",16):("mengelecek","tangan"),
    (2,"pj",17):("mengelecek","kaki"),
    (2,"pj",30):("pemanasan","menyejukkan"),
    (2,"pj",34):("palang","belum ditaksir"),
    (3,"pj",2):("hambur kaki","pendaratan"),
    (3,"pj",25):("karom","jentikan"),
    (4,"pj",20):("halangan","langkah"),
    (5,"pj",8):("palang","belum ditaksir"),
    (5,"pj",27):("cakera","power position"),
    (2,"pk",30):("iklan","rakan"),
    (3,"pk",14):("tidak","orang dewasa"),
    (5,"pk",9):("inhalan","kesan"),
}
def source(y,sub,n):
    return (ROOT/f"rph_standalone/pjpk/year{y}_{sub}/lesson_{n:03d}.md").read_text(encoding="utf-8")

class PJPKQualityImprovements(unittest.TestCase):
    def test_all_339_rpt_and_rph_preserved_and_duplicate_activities_reduced(self):
        result=inspect(ROOT)
        self.assertEqual(result["status"],"PASS_STATIC",result["issues"])
        self.assertEqual(result["rpt_records"],339)
        self.assertEqual(result["rph_numbered_checked"],339)
        self.assertLessEqual(result["duplicate_activity_groups"],30)

    def test_44_selected_replacements_usable_and_still_draft(self):
        self.assertEqual(sum(len(v) for v in CHANGED.values()),44)
        for (year,subject),numbers in CHANGED.items():
            for n in numbers:
                with self.subTest(year=year,subject=subject,pdp=n):
                    s=source(year,subject,n)
                    self.assertIn("**Status:** DRAF",s)
                    a1=next((x for x in s.splitlines() if x.startswith("**Aktiviti 1 —")),"")
                    a2=next((x for x in s.splitlines() if x.startswith("**Aktiviti 2 —")),"")
                    pbd=next((x for x in s.splitlines() if x.startswith("**Pengukuhan/PBD:")),"")
                    self.assertGreater(len(a1),150)
                    self.assertGreater(len(a2),130)
                    self.assertGreater(len(pbd),100)
                    self.assertIn("murid",(a1+a2).casefold())

    def test_15_high_risk_subject_mismatches_do_not_regress(self):
        for (year,sub,n),words in FOCUS.items():
            with self.subTest(year=year,sub=sub,pdp=n):
                lines=source(year,sub,n).splitlines()
                content="\n".join(x for x in lines if x.startswith(("**Aktiviti 1","**Aktiviti 2","**Pengukuhan/PBD","**BBM"))).casefold()
                for word in words:
                    self.assertIn(word,content)
        self.assertNotIn("stadiometer",source(2,"pj",8))
        self.assertNotIn("stadiometer",source(3,"pj",2))
        self.assertNotIn("pembesar suara",source(4,"pj",20))
        self.assertNotIn("pemukul ringan",source(5,"pj",27))

if __name__=="__main__":
    unittest.main()
