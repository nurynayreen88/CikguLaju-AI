"""Prevent premature FINAL READY for SOW teacher-choice English Year 4 lessons.

Only source-label validation. Does not verify teacher approval, textbook exercises,
actual audio playback or Telegram/PDF delivery.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = json.loads((ROOT / "audits/english_primary_2_6_official_sow_index_20261103.json").read_text(encoding="utf-8"))

class Year4TeacherChoiceReleaseGate(unittest.TestCase):
    def test_all_ten_teacher_choice_lessons_remain_draft(self):
        numbers = sorted(int(key.split("/")[1]) for key, entry in LEDGER["lessons"].items()
                         if key.startswith("4/") and entry["teacher_selected"])
        self.assertEqual(numbers, [16, 32, 48, 64, 80, 96, 112, 128, 144, 160])
        for n in numbers:
            text = (ROOT / f"rph_standalone/english/year4/lesson_{n:03d}.md").read_text(encoding="utf-8")
            status = re.search(r"(?im)^\*\*QA status:\*\*\s*(.*)$", text)
            self.assertIsNotNone(status, f"Missing QA status Y4 L{n}")
            self.assertRegex(status.group(1), r"^DRAF\b")
            self.assertNotRegex(status.group(1), r"\bREADY\s*[—:-]\s*provisional")
            self.assertIn("teacher approval", status.group(1))
            self.assertIn("Telegram", status.group(1))

if __name__ == "__main__":
    unittest.main()
