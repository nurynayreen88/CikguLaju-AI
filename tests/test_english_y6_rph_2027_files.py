"""English Year 6 RPH inventory and RPT mapping release-safety checks.

Data-only audit: never imports app.py, connects to a database or generates RPH.
"""
import csv
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LESSONS = ROOT / "rph_standalone" / "english" / "year6"
AUDIT = ROOT / "audits" / "audit_160_rph.csv"

class EnglishYear6RPHChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with AUDIT.open(encoding="utf-8-sig", newline="") as f:
            cls.records = list(csv.DictReader(f))

    def test_exact_160_unduplicated(self):
        paths = sorted(LESSONS.glob("lesson_[0-9][0-9][0-9].md"))
        self.assertEqual(len(paths), 160)
        self.assertEqual([int(p.stem[-3:]) for p in paths], list(range(1, 161)))
        self.assertEqual([int(r["Lesson"]) for r in self.records], list(range(1, 161)))

    def test_metadata_and_stages_match_audit(self):
        titles = set()
        for row in self.records:
            number = int(row["Lesson"])
            body = (LESSONS / f"lesson_{number:03d}.md").read_text(encoding="utf-8")
            self.assertIn(f"Lesson {number:03d}", body)
            self.assertIn("**Year:** 6", body)
            self.assertIn("**RPT:** 2027", body)
            self.assertIn(f"**Main CS/LS:** {row['MainCSLS_RPT']}", body)
            self.assertIn(f"**Complementary CS/LS:** {row['ComplementaryCSLS_RPT']}", body)
            self.assertIn("**Duration:** 60 minutes", body)
            self.assertIn("**Learning objective:**", body)
            self.assertIn("**PBD evidence:**", body)
            self.assertIn("**Teacher:**", body)
            self.assertIn("**Pupils:**", body)
            self.assertIn("## Set induction (5 minutes)", body)
            self.assertIn("## Activity 1 — Prepare (10 minutes)", body)
            self.assertIn("## Activity 2 — Guided core task (18 minutes)", body)
            self.assertIn("## Activity 3 — Apply and share (15 minutes)", body)
            self.assertIn("## Reinforcement / PBD (8 minutes)", body)
            self.assertIn("## Closure (4 minutes)", body)
            self.assertEqual(sum(int(x) for x in re.findall(r"^## .+ \((\d+) minutes\)$",body,re.M)), 60)
            titles.add(row["Topic"])
        self.assertGreaterEqual(len(titles), 20)

    def test_teacher_selected_lessons_do_not_claim_official_codes(self):
        expected = {16, 32, 48, 64, 80, 96, 112, 128, 144, 155, 156, 157, 158, 160}
        actual = {int(row["Lesson"]) for row in self.records if "PILIHAN GURU" in row["MainCSLS_RPT"]}
        self.assertEqual(expected, actual)
        for n in expected:
            text = (LESSONS / f"lesson_{n:03d}.md").read_text(encoding="utf-8")
            self.assertIn("subject to teacher selection", text)

    def test_literature_reference_discrepancies_are_explicit(self):
        for n in (15, 21):
            row = self.records[n - 1]
            self.assertIn("Messing About", row["Reference_RPT"])
            self.assertIn("The Sandwich", row["Reference_Added_RPH"])
            self.assertIn("pp.28–29", row["Reference_Added_RPH"])
            self.assertIn("RPT 2027 lists Messing About", row["Reference_Added_RPH"])

    def test_teacher_selected_late_lessons_have_no_invented_workbook_page(self):
        for n in (155, 156, 157, 158):
            content = (LESSONS / f"lesson_{n:03d}.md").read_text(encoding="utf-8")
            # The original reference permits use of an unused Workbook, but gives no page.
            self.assertNotRegex(content, r"(?i)Workbook\s+p(?:p)?\.\s*\d")
            self.assertIn("Teacher-selection notice", content)

    def test_no_fake_audio_track_numbers(self):
        for n in range(1,161):
            body=(LESSONS / f"lesson_{n:03d}.md").read_text(encoding="utf-8")
            self.assertNotRegex(body,r"(?i)\b(?:CD[123]\s*Track|Class\s*CD\d+\s*Track|audio\s*track)\s*\d+")


if __name__ == "__main__":
    unittest.main()
