"""Staging-only academic and arithmetic checks: Year 6 Math PBD 082–084.

These checks are not a curriculum/DSKP teacher sign-off. They do not activate
materials, call live services or consume user credits.
"""
from pathlib import Path
from math import gcd
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MATH = ROOT / "rph_standalone" / "matematik"
PUPIL = MATH / "staging_pbd_y6_pdp082_084_lembaran_murid_20261111.md"
TEACHER = MATH / "staging_pbd_y6_pdp082_084_skema_guru_20261111.md"
RPH = MATH / "staging_draf_y6_pdp082_084_nisbah_kadaran_20261110.md"
HEADER = re.compile(r"(?m)^## MT6-PDP-(082|083|084) — (Lembaran Murid|Skema Guru)[^\n]*$")
ITEM = re.compile(r"(?m)^([1-9])\. ")


def sections(text, expected_kind):
    found = list(HEADER.finditer(text))
    result = {}
    for i, match in enumerate(found):
        assert match.group(2) == expected_kind, "Pupil and teacher material mixed"
        code = match.group(1)
        assert code not in result, "Repeated lesson ID"
        end = found[i + 1].start() if i + 1 < len(found) else len(text)
        result[code] = text[match.end():end]
    return result


class Year6MathPbdStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pupil = PUPIL.read_text(encoding="utf-8")
        cls.teacher = TEACHER.read_text(encoding="utf-8")
        cls.rph = RPH.read_text(encoding="utf-8")
        cls.pupils = sections(cls.pupil, "Lembaran Murid")
        cls.keys = sections(cls.teacher, "Skema Guru")

    def test_three_worksheets_and_keys_with_exact_question_counts(self):
        expected = {"082": 5, "083": 4, "084": 3}
        self.assertEqual(set(self.pupils), set(expected))
        self.assertEqual(set(self.keys), set(expected))
        for code, count in expected.items():
            with self.subTest(code=code):
                pupil_numbers = list(map(int, ITEM.findall(self.pupils[code])))
                key_numbers = list(map(int, ITEM.findall(self.keys[code])))
                self.assertEqual(pupil_numbers, list(range(1, count + 1)))
                self.assertEqual(key_numbers, pupil_numbers)
                self.assertIn("**Pentaksiran:**", self.keys[code])
                self.assertIn("Nama:", self.pupils[code])
                self.assertIn("Kelas:", self.pupils[code])
                self.assertIn("Tarikh:", self.pupils[code])

    def test_answer_key_is_physically_separate_from_student_handout(self):
        self.assertNotEqual(PUPIL.resolve(), TEACHER.resolve())
        self.assertNotIn("Skema Guru", self.pupil)
        self.assertNotIn("Pentaksiran:", self.pupil)
        self.assertNotIn("25 : 25 = 1 : 1", self.pupil)
        self.assertIn("JANGAN EDAR KEPADA MURID", self.teacher)
        self.assertIn("BELUM DILULUSKAN", self.teacher)
        self.assertIn("BELUM DILULUSKAN", self.pupil)

    def test_082_answer_key_matches_original_ratio_and_proportion_questions(self):
        pupil, key = self.pupils["082"], self.keys["082"]
        for prompt in ("18 : 30", "2 kg kepada 800 g", "12 buku",
                       "21 buku nota", "35 orang"):
            self.assertIn(prompt, pupil)
        self.assertEqual((18//gcd(18,30),30//gcd(18,30)),(3,5))
        self.assertEqual((2000//gcd(2000,800),800//gcd(2000,800)),(5,2))
        self.assertEqual((12//3)*4,16)
        self.assertEqual((21//7)*5,15)
        self.assertEqual((35//7*3,35//7*4),(15,20))
        for answer in ("3 : 5", "5 : 2", "4 × 4 = 16",
                       "5 × 3 = 15", "Lelaki `15`, perempuan `20`"):
            self.assertIn(answer,key)

    def test_083_answer_key_matches_ratio_and_unit_conversion(self):
        pupil, key = self.pupils["083"], self.keys["083"]
        for prompt in ("6 : 9", "1.5 L kepada 500 mL",
                       "8 kuntum bunga merah", "28 cawan air"):
            self.assertIn(prompt,pupil)
        self.assertEqual((6//gcd(6,9),9//gcd(6,9)),(2,3))
        self.assertEqual((1500//gcd(1500,500),500//gcd(1500,500)),(3,1))
        self.assertEqual((8//2)*5,20)
        self.assertEqual((28//7)*4,16)
        for answer in ("2 : 3","3 : 1","5 × 4 = 20","4 × 4 = 16"):
            self.assertIn(answer,key)
        self.assertIn("bunga putih `5 × 4 = 20` kuntum", key)
        self.assertIn("bunga merah kepada bunga putih", pupil)
        self.assertNotIn("20 kuntum", pupil)
        self.assertIn("bunga putih", self.rph)
        self.assertIn("1.5 L kepada 500 mL", self.rph)

    def test_084_two_step_word_problems_are_mathematically_coherent(self):
        pupil,key=self.pupils["084"],self.keys["084"]
        self.assertIn("45 biji",pupil)
        self.assertIn("30 m",pupil)
        self.assertIn("48 buah",pupil)
        red,blue=45//9*4,45//9*5
        self.assertEqual((red+5,blue),(25,25))
        a,b=30//5*2,30//5*3
        self.assertEqual((a,b-6),(12,12))
        oranges,apples=48//8*3,48//8*5
        self.assertEqual((oranges,apples-6),(18,24))
        self.assertEqual((oranges//gcd(oranges,apples-6),
                          (apples-6)//gcd(oranges,apples-6)),(3,4))
        for answer in ("25 : 25 = 1 : 1", "12 : 12 = 1 : 1",
                       "18 : 24 = 3 : 4", "Asal oren `18`, epal `30`"):
            self.assertIn(answer,key)
        self.assertNotIn("`18)",key)

    def test_pbd_objectives_match_rph_and_academic_hold_is_explicit(self):
        expected={"082":"4 daripada 5","083":"3 daripada 4","084":"2 daripada 3"}
        for code, criterion in expected.items():
            with self.subTest(code=code):
                self.assertIn(criterion, self.rph)
                self.assertIn(criterion.split(" daripada ")[0]+"/"+
                              criterion.split(" daripada ")[1], self.keys[code])
        self.assertEqual(self.rph.count("**Status:** HOLD"),3)
        self.assertIn("JANGAN AKTIFKAN UNTUK PENGGUNA",self.rph)
        self.assertIn("calon",self.teacher.lower())
        self.assertIn("Bukan petikan Buku Teks atau Buku Aktiviti",self.pupil)
        self.assertNotIn("FINAL READY",self.pupil)
        self.assertNotIn("FINAL READY",self.teacher)


if __name__ == "__main__":
    unittest.main()
