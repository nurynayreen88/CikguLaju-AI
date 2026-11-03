"""Guard the actual Year 6 English 2027 PDF served by Telegram.

Uses PDF extraction, not only file header/size; fail if original pre-correction
literature references reappear. This does not verify page visuals or live delivery.
"""
from pathlib import Path
import re
import unittest
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "rpt_2027/english/RPT_ENGLISH_TAHUN_6_2027_UNTUK_GURU.pdf"

class Year6PublishedRPTSourceGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = PdfReader(str(PDF))
        cls.pages = [page.extract_text() or "" for page in cls.reader.pages]
        cls.all_text = "\n".join(cls.pages)

    def lesson_page(self, n):
        match = re.compile(r"LESSON:\s*0*" + str(n) + r"\b", re.I)
        pages = [p for p in self.pages if match.search(p)]
        self.assertEqual(len(pages), 1, f"Y6 Lesson {n} not unique in actual PDF")
        return pages[0]

    def test_landscape_and_all_160_numbered_lessons(self):
        self.assertEqual(len(self.reader.pages), 43)
        self.assertTrue(all(float(p.mediabox.width) > float(p.mediabox.height)
                            for p in self.reader.pages))
        nums = [int(n) for n in re.findall(r"LESSON:\s*(\d+)\b", self.all_text)]
        self.assertEqual(nums, list(range(1,161)), "Missing, repeated or out-of-order lessons")

    def test_correct_literature_and_book_references(self):
        for n in (15, 21):
            text = self.lesson_page(n)
            self.assertRegex(text, r"The Sandwich")
            self.assertRegex(text, r"pp\.28-29")
            self.assertNotIn("Anthology of Poems p.27 — Messing", text)
        self.assertRegex(self.lesson_page(16), r"WB pp\.16-17")
        self.assertRegex(self.lesson_page(25), r"future-classroom\s+poster")
        for n in (26,31):
            self.assertRegex(self.lesson_page(n), r"Toes by Judith Nicholls")
            self.assertRegex(self.lesson_page(n), r"p\.30")
        self.assertRegex(self.lesson_page(37), r"Akbar.s Dream")
        self.assertRegex(self.lesson_page(37), r"pp\.35-36")

if __name__ == "__main__":
    unittest.main()
