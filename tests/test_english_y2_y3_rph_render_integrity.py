"""Read-only 320-Lesson English Y2/Y3 row renderer audit, no database/app import."""
import re
import unittest

from english_y2_standalone_render import apply as y2, ROOT as ROOT2
from english_y3_standalone_render import apply as y3, ROOT as ROOT3

BASE = {
    "TARIKH": "03/11/2026",
    "OBJEKTIF PEMBELAJARAN": "Legacy",
    "SET INDUKSI": "Legacy intro",
    "AKTIVITI UTAMA": "Legacy activities",
    "PENTAKSIRAN": "Legacy assessment",
    "PENUTUP": "Legacy closure",
    "BAHAN BANTU MENGAJAR": "Legacy materials",
    "REFLEKSI": "Legacy reflection",
}
FIELDS = ("SET INDUKSI", "AKTIVITI UTAMA", "PENTAKSIRAN", "PENUTUP")


class EnglishYear2Year3RenderIntegrity(unittest.TestCase):
    def test_inventory_and_render_coverage(self):
        for year, fn, root in ((2, y2, ROOT2), (3, y3, ROOT3)):
            self.assertEqual(
                sorted(int(p.stem[-3:]) for p in root.glob("lesson_???.md")),
                list(range(1, 161)), year)
            covered, missing, no_pbd, leak, unchanged = [], [], [], [], []
            for n in range(1, 161):
                old = dict(BASE)
                state = {"subject": "English", "year": f"Tahun {year}", "lesson_no": n}
                out = fn(state, old)
                self.assertEqual(old, BASE, ("mutation", year, n))
                if out is old:
                    missing.append(n)
                    continue
                covered.append(n)
                self.assertEqual(out["TARIKH"], BASE["TARIKH"])
                self.assertEqual(out["REFLEKSI"], BASE["REFLEKSI"])
                if (out.get("PENTAKSIRAN") == BASE["PENTAKSIRAN"]
                        or "Assessment / PBD" in out.get("AKTIVITI UTAMA", "")):
                    no_pbd.append(n)
                for field in FIELDS:
                    if not out.get(field):
                        unchanged.append((n, field))
                    if re.search(r"(?im)(?:QA status:|NOT READY FOR RELEASE|Teacher's Book verification pending)", out.get(field, "")):
                        leak.append((n, field))
            print(f"YEAR{year}_RENDER_COVERAGE {len(covered)}/160; MISSING {missing}; PBD_NOT_MAPPED {no_pbd}; LEAK {leak}; EMPTY {unchanged}", flush=True)
            self.assertEqual(missing, [], f"Y{year} standalone renderer failed to map these lessons")
            self.assertEqual(no_pbd, [], f"Y{year} PBD must be mapped for every lesson")
            self.assertEqual(leak, [], f"Y{year} internal QA strings must not reach teacher-facing rows")
            self.assertEqual(unchanged, [])

    def test_non_target_fail_closed_and_no_cross_year(self):
        for year, fn in ((2, y2), (3, y3)):
            for state in (
                {"subject":"Matematik", "year":f"Tahun {year}", "lesson_no":1},
                {"subject":"English", "year":"Tahun 5", "lesson_no":1},
                {"subject":"English", "year":f"Tahun {year}", "lesson_no":0},
                {"subject":"English", "year":f"Tahun {year}", "lesson_no":161},
                {"subject":"English", "year":f"Tahun {year}", "lesson_no":"../1"},
                {"subject":"English", "year":f"Tahun {year}", "lesson_no":True},
                {"subject":"English", "year":f"Tahun {year}", "lesson_no":1.5},
                {"subject":"English", "year":f"Tahun {year}", "lesson_no":0, "textbook_lesson_no":1},
            ):
                original = dict(BASE)
                self.assertIs(fn(state, original), original)

    def test_year2_lesson82_uses_precise_materials(self):
        rows = y2({"subject":"English", "year":"Tahun 2", "lesson_no":82}, dict(BASE))
        self.assertNotEqual(rows["BAHAN BANTU MENGAJAR"], BASE["BAHAN BANTU MENGAJAR"])
        self.assertIn("outfit picture", rows["BAHAN BANTU MENGAJAR"])
        self.assertNotIn("QA", rows["PENUTUP"])

    def test_critical_year3_lesson93(self):
        rows = y3({"subject":"English", "year":"Tahun 3", "lesson_no":93}, dict(BASE))
        self.assertIn("Tony", rows["AKTIVITI UTAMA"])
        self.assertIn("Workbook p.48", rows["AKTIVITI UTAMA"] + rows["PENTAKSIRAN"])
        self.assertIn("printed Track 97", rows["BAHAN BANTU MENGAJAR"])
        self.assertIn("disc not specified", rows["BAHAN BANTU MENGAJAR"])
        self.assertNotIn("Class CD1 Track 97 (teacher-confirmed", rows["BAHAN BANTU MENGAJAR"])

if __name__ == "__main__":
    unittest.main()
