from hashlib import sha256
import json
from pathlib import Path
import re
import unittest

import fitz

from scripts.build_web_rpt_weekly_suggestions import read_weeks


ROOT = Path(__file__).resolve().parents[1] / "rpt_2027" / "web_2027_pdfs"


class EnglishWeeklyLabelsTests(unittest.TestCase):
    def test_all_800_lessons_and_week_labels_match_weekly_suggestions(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        suggestions_path = ROOT.parents[1] / "web/rpt_weekly_suggestions_2027.json"
        suggestions = json.loads(suggestions_path.read_text(encoding="utf-8"))
        for year in range(2, 7):
            with self.subTest(year=year):
                entry = manifest["files"][f"english:{year}"]
                path = ROOT / entry["path"]
                self.assertEqual(sha256(path.read_bytes()).hexdigest(), entry["sha256"])
                dates, weeks = read_weeks(path, "ENGLISH")
                self.assertEqual(
                    {str(n): [*dates[n], items] for n, items in weeks.items()},
                    suggestions[f"ENGLISH:{year}"],
                )
                self.assertEqual(
                    [lesson for week in sorted(weeks) for lesson in weeks[week][""]],
                    list(range(1, 161)),
                )
                with fitz.open(path) as pdf:
                    for page in list(pdf)[1:]:
                        text = page.get_text(clip=fitz.Rect(35, 66, 140, 550), sort=True)
                        printed = re.findall(r"\bM(\d{2})\s*\| Lessons (\d{3})-(\d{3})", text)
                        self.assertEqual(len(printed), len(re.findall(r"\bM\d{2}\b", text)))
                        for week, first, last in printed:
                            lessons = weeks[int(week)][""]
                            self.assertEqual((int(first), int(last)), (lessons[0], lessons[-1]))


if __name__ == "__main__":
    unittest.main()
