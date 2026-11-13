import unittest

from web.english_y1_kssr_rph import UNIT
from web.rph_shared_source_identity import source_fingerprint
from web.telegram_rph_parity import build_layout
from web.unified_rph_web import pdp_options, unit_options, verified_preview


class EnglishYearOneWebTests(unittest.TestCase):
    def test_released_lessons_are_reachable_via_unit_and_have_native_layouts(self):
        self.assertEqual(unit_options(1, "ENGLISH"), [{"label": UNIT, "value": UNIT}])
        choices = pdp_options(1, "ENGLISH", UNIT)
        self.assertEqual([x["value"] for x in choices], ["e-1-018", "e-1-019"])
        for choice in choices:
            rph = verified_preview(1, "ENGLISH", UNIT, choice["value"])
            self.assertIsNotNone(source_fingerprint(1, "ENGLISH", rph["lesson"]))
            layout = build_layout(rph, {"ENGLISH": "English"})
            self.assertIn("Workbook", layout["phases"][1]["activity"])
            self.assertIn("KSSR Semakan 2017", str(layout["header"]))
            self.assertNotIn("CONTENT DRAFT", str(layout))
        self.assertIsNone(verified_preview(1, "ENGLISH", UNIT, "e-1-016"))
        self.assertIsNone(verified_preview(1, "ENGLISH", "Friends", "e-1-018"))
        self.assertEqual(unit_options(1, "MORAL"), [])
