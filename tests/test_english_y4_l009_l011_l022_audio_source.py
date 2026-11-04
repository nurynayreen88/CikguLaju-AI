"""Printed TB audio-reference checks only; no sound or Telegram delivery approval."""
import unittest
from pathlib import Path
from tools.audit_english_y4_legacy_audio_routes_20261104 import (
    _legacy_route_map, _teacher_task_refs,
)

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    9: (23, {"CD1 Track 12", "CD1 Track 13"}),
    11: (28, {"CD1 Track 16"}),
    22: (34, {"CD1 Track 22"}),
}


class SourceAudioTest(unittest.TestCase):
    def test_printed_source_matches_rph_and_legacy_route(self):
        mapping = _legacy_route_map()
        for lesson, (printed_page, expected) in CASES.items():
            with self.subTest(lesson=lesson):
                path = ROOT / "rph_standalone/english/year4" / f"lesson_{lesson:03d}.md"
                source = path.read_text(encoding="utf-8")
                self.assertIn(f"p.{printed_page}", source)
                self.assertIn("Telegram delivery remain unverified", source)
                refs = set(_teacher_task_refs(source))
                self.assertTrue(expected.issubset(refs), (lesson, refs))
                routes = mapping.get(lesson) or mapping.get(str(lesson))
                self.assertIsInstance(routes, list)
                routed = {r.get("audio_reference") for r in routes}
                self.assertTrue(expected.issubset(routed), (lesson, routed))


if __name__ == "__main__":
    unittest.main()
