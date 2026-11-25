import json
import unittest
from pathlib import Path

from staging.ppki.audit_year2_drafts import BANKS, audit
from staging.ppki.render_approved_subject import render_approved_lesson


class TestPPKIDraftReleaseGate(unittest.TestCase):
    def test_all_288_draft_lessons_rejected(self):
        root = Path(__file__).resolve().parents[1] / "staging" / "ppki"
        count = 0
        for name in BANKS:
            catalog = json.loads((root / name).read_text(encoding="utf-8"))
            for lesson in catalog["lessons"]:
                with self.subTest(bank=name, pdp=lesson["pdp"]):
                    for fmt in ("docx", "pdf"):
                        with self.assertRaisesRegex(ValueError, "not passed curriculum approval"):
                            render_approved_lesson(catalog, lesson, fmt, {})
                count += 1
        self.assertEqual(count, 288)

    def test_audit_never_claims_drafts_are_release_ready(self):
        result = audit()
        self.assertEqual(sum(item["lessons"] for item in result.values()), 288)
        self.assertTrue(all(not item["release_ready"] for item in result.values()))
