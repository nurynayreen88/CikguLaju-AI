"""Check Jawi source characters and markup without loading the app or database."""
import ast
import html
import pathlib
import re
import unicodedata
import unittest

APP = pathlib.Path(__file__).resolve().parents[1] / "app.py"
FUNCTIONS = ("_pi_term_cleanup_v2601", "_pi_safe_unicode_v2602", "_pi_markup_to_plain_v2605")

class TextBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = APP.read_text(encoding="utf-8")
        tree = ast.parse(source)
        selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS]
        scope = {"re": re, "_html": html, "unicodedata": unicodedata}
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(APP), "exec"), scope)
        cls.prepare = staticmethod(scope["_pi_markup_to_plain_v2605"])

    def test_jawi_characters_preserved(self):
        sample = "\u06a4 \u0686 \u06a0 \u06bd \u0762 \u06cf"
        result, bold = self.prepare(sample)
        self.assertEqual(result, sample)
        self.assertFalse(bold)

    def test_linebreak_markup(self):
        result, _ = self.prepare("<b>\u06a4</b><br/>\u0686<br />\u06a0")
        self.assertEqual(result, "\u06a4\n\u0686\n\u06a0")

    def test_bold_markup(self):
        result, bold = self.prepare("<b>\u06a4\u0646\u062f\u064a\u062f\u064a\u0642\u0646</b>")
        self.assertTrue(bold)
        self.assertEqual(result, "\u06a4\u0646\u062f\u064a\u062f\u064a\u0642\u0646")

    def test_entities(self):
        result, _ = self.prepare("\u0639\u0644\u0645 &amp; \u0639\u0645\u0644")
        self.assertEqual(result, "\u0639\u0644\u0645 & \u0639\u0645\u0644")

if __name__ == "__main__":
    unittest.main()
