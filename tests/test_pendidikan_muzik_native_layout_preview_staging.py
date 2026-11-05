"""Non-destructive staging-only validation of future native Word/PDF input layout."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "staging" / "pendidikan_muzik" / "rpt_rph_2027"
MODULE = SOURCE / "native_layout_preview_staging.py"
spec = importlib.util.spec_from_file_location("music_native_layout_preview_staging", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MusicNativeLayoutStagingTests(unittest.TestCase):
    def test_all_175_music_rph_preserve_the_five_pedagogical_parts(self):
        for year in range(2, 7):
            for pdp in range(1, 36):
                with self.subTest(year=year, pdp=pdp):
                    preview = module.build_staging_preview(SOURCE, year, pdp)
                    self.assertFalse(preview["approved_for_live"])
                    self.assertEqual(preview["source_pdp_id"], f"MZ-Y{year}-{pdp:02d}")
                    self.assertEqual(preview["layout"]["style"], "telegram-native-rph-v1")
                    self.assertEqual(len(preview["layout"]["header"]), 20)
                    self.assertEqual(preview["layout"]["activity_header"], module.ACTIVITY_HEADER)
                    self.assertEqual(len(preview["layout"]["phases"]), 3)
                    self.assertEqual(len(preview["layout"]["footer"]), 2)
                    self.assertEqual(preview["layout"]["phases"][0]["activity"], preview["phase_text"]["induction"])
                    self.assertEqual(preview["layout"]["phases"][2]["activity"], preview["phase_text"]["closure"])
                    for kind in ("act1", "act2", "assessment"):
                        self.assertIn(preview["phase_text"][kind], preview["layout"]["phases"][1]["activity"])
                    self.assertIn("NO_REAL_WORD_PDF_RENDER", preview["warnings"])
    def test_fail_closed_for_invalid_year_or_pdp(self):
        for year, pdp in ((1, 1), (7, 1), (2, 0), (3, 36), ("2", 1)):
            with self.subTest(year=year, pdp=pdp):
                with self.assertRaises(ValueError):
                    module.build_staging_preview(SOURCE, year, pdp)


if __name__ == "__main__":
    unittest.main()
