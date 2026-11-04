"""Batch-22 Year6 fixed-SOW content and no-regeneration regression.

Primary Year6 KPM SOW PDF: Drive 1Onk874v0lSQWEo-gOMcdw4uIUg8YsI8Z
Lessons 51,52,54–57,59–62,65–68,70–73,75–78. Source-only check:
does not approve audio speech, printed workbook pictures or Telegram release.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "rph_standalone" / "english" / "year6"
INDEX = json.loads(
    (ROOT/"audits/english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8")
)["lessons"]
MARKERS = {
    51: ("yet", "already", "PB p.52", "new school"),
    52: ("How long", "for", "since", "TB p.84"),
    54: ("paramedic", "PB p.54", "family", "interview"),
    55: ("Lesson 54", "personality", "make", "do"),
    56: ("Jean", "TB p.88", "job", "listening"),
    57: ("future job", "TB p.89", "WB p.43", "make"),
    59: ("Fizz-Bump", "code", "PB p.57", "dictionary"),
    60: ("computer-programmer", "job advert", "will/won't", "MCQs"),
    61: ("Robert", "PB p.56", "WB p.46", "polite"),
    62: ("Robert", "Do you mean", "PB p.56", "robot"),
    65: ("film", "PB pp.60–61", "outdoor", "TB p.99"),
    66: ("because", "so", "but", "TB p.100"),
    67: ("schwa", "TB p.102", "as...as", "weak"),
    68: ("transport", "TB p.104", "not...enough", "environmental"),
    70: ("time travel", "TB p.108", "summary", "picture"),
    71: ("PB p.67", "six", "story", "group"),
    72: ("PB p.65", "skateboard", "price", "quality"),
    73: ("PB p.65", "poster", "need to", "have to"),
    75: ("PB p.69", "puzzle", "four", "need to"),
    76: ("penfriend", "email", "50 words", "peer"),
    77: ("PB p.68", "TB p.110", "ferry", "ticket"),
    78: ("timetable", "TB p.110", "clarification", "dialogue"),
}
CODES = {
    51: ("1.2.2", "1.2.5"), 52: ("2.1.1", "1.2.5"),
    54: ("3.2.2", "4.2.1"), 55: ("4.2.1", "4.2.4"),
    56: ("1.2.1", "1.3.1"), 57: ("2.1.1", "4.3.2"),
    59: ("3.2.2", "4.3.2"), 60: ("4.2.2", "3.2.2"),
    61: ("1.2.5", "1.3.1"), 62: ("2.2.1", "3.2.2"),
    65: ("3.3.1", "3.2.1"), 66: ("4.2.5", "1.2.3"),
    67: ("1.1.1", "3.2.2"), 68: ("2.1.1", "2.1.3"),
    70: ("3.2.1", "2.3.1"), 71: ("4.2.3", "1.2.3"),
    72: ("1.2.2", "1.3.1"), 73: ("2.1.2", "2.2.2"),
    75: ("3.2.2", "4.2.5"), 76: ("4.3.3", "4.2.5"),
    77: ("1.2.5", "1.1.1"), 78: ("2.2.1", "1.2.5"),
}
TIME = [5, 10, 18, 15, 8, 4]
class EnglishYear6SowBatch22(unittest.TestCase):
    def test_source_paired_22_lessons(self):
        self.assertEqual(len(MARKERS), 22)
        self.assertEqual(set(MARKERS), set(CODES))
        for lesson, words in MARKERS.items():
            with self.subTest(lesson=lesson):
                idx=INDEX[f"6/{lesson}"]
                self.assertFalse(idx["teacher_selected"])
                self.assertEqual((idx["main_ls"], idx["complementary_ls"]), CODES[lesson])
                content=(SRC/f"lesson_{lesson:03d}.md").read_text(encoding="utf-8")
                self.assertRegex(content.splitlines()[0],rf"\bLesson\s+0*{lesson}\b")
                for tag,code in (("Main", CODES[lesson][0]),("Complementary", CODES[lesson][1])):
                    cs=code.rsplit(".",1)[0]
                    self.assertIn(f"**{tag} CS/LS:** {cs}/{code}",content)
                self.assertIn("**Teacher reflection:**",content)
                self.assertIn("**RPT:** 2027",content)
                self.assertNotIn("FINAL READY",content)
                for phrase in words:
                    self.assertIn(phrase.casefold(),content.casefold(),(lesson,phrase))
                for phrase in (
                    "Share one accurate new sentence or fact",
                    "Check the complementary skill using the short task.",
                    "Check the lesson evidence against the target",
                ):
                    self.assertNotIn(phrase,content)
                sections=[int(m.group(1)) for m in re.finditer(
                    r"(?m)^## [^\n]+ \((\d+) minutes\)$",content)]
                self.assertEqual(sections,TIME)
                lines=content.splitlines()
                phase_positions=[i for i,v in enumerate(lines) if re.match(
                    r"^## (?:Set induction|Activity [123]|Reinforcement / PBD|Closure)",v)]
                self.assertEqual(len(phase_positions),6)
                for i in phase_positions:
                    self.assertTrue(lines[i+1].startswith("**Teacher:**"),lesson)
                    self.assertTrue(lines[i+2].startswith("**Pupils:**"),lesson)
    def test_leave_nonflagged_english_unmodified(self):
        for n in (53,58,63,64,69,74):
            self.assertTrue((SRC/f"lesson_{n:03d}.md").exists())
        self.assertTrue(INDEX["6/64"]["teacher_selected"] or (SRC/"lesson_064.md").exists())

if __name__=="__main__":
    unittest.main()
