"""Check the 2027 plan on all five English PDFs delivered by Telegram."""
from collections import Counter
from pathlib import Path
import re
import unittest

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1] / 'rpt_2027' / 'english'
WEEK_CELL = re.compile(
    r'WEEK (\d{2})\s+(?:(\d) Lessons (\d{3})-(\d{3})|(School closed))'
)


class EnglishWeeklyAllocationTests(unittest.TestCase):
    def test_all_160_lessons_and_shortened_weeks(self):
        for year in range(2, 7):
            with self.subTest(year=year):
                reader = PdfReader(ROOT / f'RPT_ENGLISH_TAHUN_{year}_2027_UNTUK_GURU.pdf')
                text = '\n'.join(page.extract_text() for page in reader.pages)
                lesson_ids = [int(n) for n in re.findall(r'LESSON:\s*(\d+)\b', text)]
                self.assertEqual(lesson_ids, list(range(1, 161)))
                found = {}
                for week, count, first, last, closed in WEEK_CELL.findall(text):
                    ids = list(range(int(first), int(last) + 1)) if count else []
                    self.assertTrue(ids or closed)
                    self.assertEqual(len(ids), int(count or 0))
                    self.assertEqual(found.setdefault(int(week), ids), ids)
                self.assertEqual(sorted(found), list(range(1, 45)))
                self.assertEqual(Counter(map(len, found.values())), {0: 2, 2: 1, 3: 6, 4: 35})
                self.assertEqual([week for week in sorted(found) if not found[week]], [6, 19])
                self.assertEqual(found[1], [1, 2, 3])
                self.assertEqual(found[39], [139, 140])
                self.assertEqual(found[44], [157, 158, 159, 160])
                self.assertEqual([n for week in sorted(found) for n in found[week]], lesson_ids)
