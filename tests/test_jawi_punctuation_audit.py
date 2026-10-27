"""Unit checks for Jawi punctuation audit; no app import, database, or font files."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "audit_jawi_punctuation.py"
spec = importlib.util.spec_from_file_location("audit_jawi_punctuation", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class JawiPunctuationCoverageTests(unittest.TestCase):
    def test_fallback_covers_dash_without_rewriting_text(self):
        source = "ڤ–چ"
        primary = {ord("ڤ"), ord("چ")}
        fallback = {ord("–")}
        result = audit.build_report([("jawi.ttf", primary), ("latin.ttf", fallback)], [source])
        self.assertEqual(result["missing"], [])
        self.assertEqual(result["fallback_needed"], [
            {"character": "–", "codepoint": "U+2013", "font": "latin.ttf"}
        ])
        self.assertEqual(source, "ڤ–چ")

    def test_mixed_jawi_latin_and_punctuation_supported_by_fallback(self):
        source = "ڤنديديقن اسلام – Jawi/Rumi (1)"
        primary = {ord(c) for c in source if "\\u0600" <= c <= "\\u08ff"}
        latin = {ord(c) for c in source if not c.isspace() and ord(c) not in primary}
        report = audit.build_report([("naskh.ttf", primary), ("dejavu.ttf", latin)], [source])
        self.assertEqual(report["missing"], [])
        self.assertIn({"character": "–", "codepoint": "U+2013", "font": "dejavu.ttf"},
                      report["fallback_needed"])

    def test_missing_glyph_is_reported(self):
        result = audit.build_report([("jawi.ttf", {ord("ڤ")})], ["ڤ—"])
        self.assertEqual(result["missing"], [{"character": "—", "codepoint": "U+2014"}])
        self.assertEqual(result["fallback_needed"][0]["font"], None)

    def test_requires_primary_font(self):
        with self.assertRaises(ValueError):
            audit.build_report([], ["ڤ"])

if __name__ == "__main__":
    unittest.main()
