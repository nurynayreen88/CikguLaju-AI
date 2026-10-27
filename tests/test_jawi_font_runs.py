"""Contract tests for mixed-script font run selection without importing app.py."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "tools" / "jawi_font_runs.py"
spec = importlib.util.spec_from_file_location("jawi_font_runs", PATH)
runs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runs)

class JawiFontRunsTests(unittest.TestCase):
    def test_exact_source_preserved_with_punctuation_fallback(self):
        text = "ڤنديديقن اسلام – Jawi/Rumi (1)"
        jawi = {ord(c) for c in text if 0x0600 <= ord(c) <= 0x08FF}
        latin = {ord(c) for c in text if ord(c) not in jawi and not c.isspace()}
        segments = runs.select_runs(text, ["jawi", "latin"], [jawi, latin])
        self.assertEqual("".join(value for _, value in segments), text)
        self.assertTrue(any(path == "latin" and "–" in value for path, value in segments))

    def test_missing_glyph_raises_not_tofu(self):
        with self.assertRaisesRegex(ValueError, "U\\+2014"):
            runs.select_runs("ڤ—", ["jawi"], [{ord("ڤ")}])

    def test_whitespace_and_newline_preserved(self):
        text = "ڤ  چ\nJ"
        segments = runs.select_runs(text, ["jawi", "latin"], [
            {ord("ڤ"), ord("چ")}, {ord("J")}
        ])
        self.assertEqual("".join(value for _, value in segments), text)

    def test_empty_text_and_font_list(self):
        self.assertEqual(runs.select_runs("", ["jawi"], [set()]), [])
        with self.assertRaises(ValueError):
            runs.select_runs("ڤ", [])

    def test_coverage_length_mismatch(self):
        with self.assertRaisesRegex(ValueError, "mismatch"):
            runs.select_runs("ڤ", ["jawi", "latin"], [{ord("ڤ")}])

if __name__ == "__main__":
    unittest.main()
