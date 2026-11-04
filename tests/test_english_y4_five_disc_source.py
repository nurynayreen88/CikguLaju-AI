"""Compare five English Year4 RPH CD labels with visually checked original TB pages.

The test validates printed source references against historical routing only;
MP3 speech, Telegram user delivery and final teacher approval remain separate.
"""
import unittest
from pathlib import Path

from tools.audit_english_y4_legacy_audio_routes_20261104 import (
    _legacy_route_map, _teacher_task_refs,
)

ROOT=Path(__file__).resolve().parents[1]
CASES={8:(22,11),12:(30,17),17:(32,19),24:(36,25),59:(67,61)}


class FiveYear4AudioDiscReferences(unittest.TestCase):
    def test_printed_tb_audio_reference_matches_legacy_route(self):
        mapping=_legacy_route_map()
        for number,(page,track) in CASES.items():
            with self.subTest(lesson=number):
                source=(ROOT/"rph_standalone/english/year4"/
                        f"lesson_{number:03d}.md").read_text(encoding="utf-8")
                label=f"CD1 Track {track}"
                self.assertIn(label,_teacher_task_refs(source))
                self.assertIn(f"p.{page}",source)
                self.assertIn("recording content/Telegram delivery unverified",source)
                routes=mapping.get(number) or mapping.get(str(number))
                self.assertTrue(routes)
                self.assertIn(label,[r.get("audio_reference") for r in routes])


if __name__=="__main__":
    unittest.main()
