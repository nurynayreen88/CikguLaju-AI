import unittest
from types import SimpleNamespace
from unittest.mock import patch

from web.english_y1_kssr_rph import UNIT, install
from web.native_rph_telegram_api import build_native_input
from web.rph_shared_source_identity import source_fingerprint


class EnglishYearOneNativeTests(unittest.TestCase):
    def payload(self):
        return {
            "year": 1, "lesson": 18, "unit": UNIT, "subject": "ENGLISH",
            "component": None, "format": "word",
            "teacher": {"class": "1 Bestari", "date": "2026-11-13", "time": "", "students": "28"},
            "source_digest": source_fingerprint(1, "ENGLISH", 18),
            "layout": {
                "style": "telegram-native-rph-v1",
                "header": [{"label": "Topic", "value": UNIT}] + [
                    {"label": f"Field {i}", "value": ""} for i in range(15)
                ],
                "activity_header": ["Phase / Time", "Teaching and Learning Activities", "Notes"],
                "phases": [
                    {"label": label, "activity": "Test activity", "notes": ""}
                    for label in ("Set Induction", "Main Activities", "Closure")
                ],
                "footer": [
                    {"label": label, "value": ""}
                    for label in ("Remedial / Enrichment", "Reflection")
                ],
            },
        }

    def test_native_gate_requires_released_lesson_unit_and_matching_digest(self):
        payload = self.payload()
        state, _, _ = build_native_input(payload)
        self.assertEqual(state["_web_english_y1_kssr_lesson"], 18)
        for changes in ({"lesson": 16}, {"unit": "Friends"}, {"source_digest": "0" * 64},
                        {"source_digest": None}, {"subject": "MORAL"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                build_native_input({**payload, **changes})

    def test_native_rows_use_reviewed_content_without_legacy_runtime_lookup(self):
        state, _, _ = build_native_input(self.payload())
        runtime = SimpleNamespace(_rph_rows=lambda *args: {"other_lesson": True})
        with patch.object(runtime, "_rph_rows", wraps=runtime._rph_rows) as legacy:
            self.assertTrue(install(runtime))
            rows = runtime._rph_rows(state)
            legacy.assert_not_called()
            self.assertIn("1.2.1", rows["MAIN LEARNING STANDARD"])
            self.assertIn("2.1.5", rows["COMPLEMENTARY LEARNING STANDARD"])
            self.assertIn("Workbook p. 10", rows["AKTIVITI UTAMA"])
            self.assertEqual(rows["TARIKH"], "13/11/2026")
            self.assertEqual(runtime._rph_rows({}), {"other_lesson": True})
