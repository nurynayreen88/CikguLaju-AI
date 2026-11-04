"""Verify Year4 Lesson145/147 CD number from printed TB without claiming MP3 playback."""
import unittest
from pathlib import Path

from tools.audit_english_y4_legacy_audio_routes_20261104 import (
    _legacy_route_map, _teacher_task_refs,
)

ROOT=Path(__file__).resolve().parents[1]


class Year4HealthAudioReferences(unittest.TestCase):
    def test_printed_source_and_existing_route_agree(self):
        mapping=_legacy_route_map()
        for number, printed_page, track in ((145, 152, 68), (147, 155, 72)):
            with self.subTest(lesson=number):
                lesson=(ROOT / "rph_standalone/english/year4" /
                        f"lesson_{number:03d}.md").read_text(encoding="utf-8")
                label=f"CD2 Track {track}"
                self.assertIn(f"TB p.{printed_page} verifies {label}", lesson)
                self.assertIn("spoken content and Telegram delivery remain unverified", lesson)
                self.assertIn(label, _teacher_task_refs(lesson))
                routed=mapping.get(number) or mapping.get(str(number))
                self.assertIsInstance(routed, list)
                self.assertIn(label,[r.get("audio_reference") for r in routed])
                self.assertFalse(any(
                    ("disc remains unverified" in line.lower())
                    for line in lesson.splitlines()
                ))


if __name__=="__main__":
    unittest.main()
