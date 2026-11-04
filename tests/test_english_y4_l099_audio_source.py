"""Source-locked Year4 Lesson099 audio reference regression, not spoken-content QA."""
import unittest
from pathlib import Path

from tools.audit_english_y4_legacy_audio_routes_20261104 import (
    _legacy_route_map, _teacher_task_refs,
)

ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "rph_standalone/english/year4/lesson_099.md"


class Lesson99AudioSourceTest(unittest.TestCase):
    def test_printed_teacher_book_track_is_used_in_instruction(self):
        text = LESSON.read_text(encoding="utf-8")
        refs = _teacher_task_refs(text)
        self.assertEqual(refs, ["CD2 Track 24"])
        self.assertIn("SB p.72", text)
        self.assertIn("TB p.110", text)
        self.assertIn("Listening SP 1.2.3", text)
        self.assertIn("Reading SP 3.3.1", text)
        self.assertIn("not infer listening achievement from written answers", text)

    def test_actual_legacy_media_route_agrees_with_task(self):
        routing = _legacy_route_map()
        routes = routing.get(99) or routing.get("99")
        self.assertIsInstance(routes, list)
        self.assertEqual([row.get("audio_reference") for row in routes],
                         ["CD2 Track 24"])
        self.assertTrue(all(row.get("storage_file_id") for row in routes))


if __name__ == "__main__":
    unittest.main()
