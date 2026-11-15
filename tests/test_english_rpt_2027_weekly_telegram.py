"""Check the calendar and numbering in every published Telegram English RPT."""

import json
from pathlib import Path
import re
import unittest

from pypdf import PdfReader

from rpt_2027.english.telegram_downloads import pdf_path

ROOT = Path(__file__).resolve().parents[1]
CALENDAR = ROOT / 'rpt_2027/pendidikan_moral/induk_minggu_2027_ab.json'
WEEK = re.compile(r'\bWEEK (\d{2})\b')
LESSON = re.compile(r'\bLESSON:\s*(\d+)\b')
THREE_LESSON_WEEKS = {1, 5, 10, 11, 20, 35}


class TelegramEnglishRPTCalendarTests(unittest.TestCase):
    def test_all_five_pdfs_match_the_kpm_windows_and_the_published_allocation(self):
        calendar = json.loads(CALENDAR.read_text())['weeks']
        for year in range(2, 7):
            with self.subTest(year=year):
                pages = [page.extract_text() or '' for page in PdfReader(pdf_path(year)).pages]
                teaching_pages = [(int(match[1]), page) for page in pages if (match := WEEK.search(page))]
                self.assertEqual([week for week, _ in teaching_pages], list(range(1, 45)))
                all_lessons = []
                for week, page in teaching_pages:
                    lessons = [int(number) for number in LESSON.findall(page)]
                    if week in (6, 19):
                        self.assertEqual(lessons, [])
                        self.assertIn('School closed', page)
                    else:
                        count = 2 if week == 39 else 3 if week in THREE_LESSON_WEEKS else 4
                        self.assertEqual(len(lessons), count, f'WEEK {week:02d}')
                        self.assertIn(f'{count} Lessons {lessons[0]:03d}-{lessons[-1]:03d}', page)
                    for group in ('A', 'B'):
                        dates = calendar[group][week - 1]
                        start_year, start_month, start_day = dates['start'].split('-')
                        end_year, end_month, end_day = dates['end'].split('-')
                        self.assertEqual(start_year, end_year)
                        self.assertIn(f'{group}  {start_day}/{start_month} - {end_day}/{end_month}/{end_year}', page)
                    all_lessons.extend(lessons)
                self.assertEqual(all_lessons, list(range(1, 161)))
