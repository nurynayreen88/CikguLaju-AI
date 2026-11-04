"""Regression: Year 6 optional projects are distinct CikguLaju suggestions.

SOW does not mandate project topics or fixed standards. This test does not
constitute classroom or Telegram delivery approval.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "rph_standalone" / "english" / "year6"
INDEX = ROOT / "audits" / "english_primary_2_6_official_sow_index_20261103.json"
PROJECTS = {
    80: ("Project-Based Learning 1", "Our Future Careers", ("career", "skill", "three")),
    160: ("Project-Based Learning 2", "End-of-year story portfolio", ("past-tense", "three", "memory")),
}

class Year6OptionalProjects(unittest.TestCase):
    def test_project_evidence_and_teacher_choices(self):
        index = json.loads(INDEX.read_text(encoding="utf-8"))["lessons"]
        for n, (focus, title, terms) in PROJECTS.items():
            with self.subTest(lesson=n):
                rec = index[f"6/{n}"]
                self.assertTrue(rec["teacher_selected"])
                self.assertEqual(rec["focus"], focus)
                self.assertIsNone(rec["main_ls"])
                self.assertIsNone(rec["complementary_ls"])
                txt = (SRC / f"lesson_{n:03d}.md").read_text(encoding="utf-8")
                self.assertIn(title, txt)
                self.assertIn("**Main CS/LS:** PILIHAN GURU (SOW)", txt)
                self.assertIn("**Complementary CS/LS:** PILIHAN GURU (SOW)", txt)
                self.assertIn("CikguLaju suggestions", txt)
                self.assertIn("**Teacher reflection:**", txt)
                self.assertIn("**Duration:** 60 minutes", txt)
                self.assertNotIn("Explain the project challenge and present one example product", txt)
                for term in terms:
                    self.assertIn(term.casefold(), txt.casefold())
                phases = list(re.finditer(r"(?m)^## (.+?) \((\d+) minutes\)$", txt))
                self.assertEqual([int(x.group(2)) for x in phases], [5, 10, 18, 15, 8, 4])
                for i, phase in enumerate(phases):
                    end = phases[i + 1].start() if i + 1 < 6 else txt.index("## Differentiation", phase.end())
                    body = txt[phase.end():end]
                    self.assertIn("**Teacher:**", body)
                    self.assertIn("**Pupils:**", body)

    def test_all_teacher_choice_openings_and_closures_are_distinct(self):
        index = json.loads(INDEX.read_text(encoding="utf-8"))["lessons"]
        choices = sorted(int(k.split("/")[1]) for k, v in index.items()
                         if k.startswith("6/") and v["teacher_selected"])
        self.assertEqual(len(choices), 14)
        openings, closings = set(), set()
        for n in choices:
            txt = (SRC / f"lesson_{n:03d}.md").read_text(encoding="utf-8")
            a = re.search(r"(?ms)^## Set induction \(5 minutes\)\n(.*?)(?=^## Activity 1)", txt)
            b = re.search(r"(?ms)^## Closure \(4 minutes\)\n(.*?)(?=^## Differentiation)", txt)
            self.assertIsNotNone(a, f"missing opening {n}")
            self.assertIsNotNone(b, f"missing closure {n}")
            openings.add(re.sub(r"\s+", " ", a.group(1)).strip())
            closings.add(re.sub(r"\s+", " ", b.group(1)).strip())
        self.assertEqual(len(openings), 14, "Year 6 optional openings must be task-specific")
        self.assertEqual(len(closings), 14, "Year 6 optional closures must be task-specific")

if __name__ == "__main__":
    unittest.main()
