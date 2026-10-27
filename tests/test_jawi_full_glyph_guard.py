"""Source-level regression for full glyph coverage in the active Jawi renderer.

Does not import app.py or touch the DB. Run with:
python -m unittest tests/test_jawi_full_glyph_guard.py
"""
import ast
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

class FullJawiGlyphGuard(unittest.TestCase):
    def test_active_renderer_checks_all_visible_codepoints(self):
        classes = [node for node in TREE.body
                   if isinstance(node, ast.ClassDef) and node.name == "_JawiRasterParagraph_v25213"]
        self.assertTrue(classes)
        latest = classes[-1]
        constructor = next(node for node in latest.body
                           if isinstance(node, ast.FunctionDef) and node.name == "__init__")
        source = ast.get_source_segment(SOURCE, constructor)
        # Current v26.06 code filters to U+0600..U+08FF, missing punctuation and Latin.
        # This test intentionally fails until full glyph fallback is integrated.
        self.assertNotIn("0x0600 <= ord(c) <= 0x08FF", source,
                         "Active renderer still validates only Arabic/Jawi glyphs")
        self.assertIn("_font_cmap_v25226", source)

if __name__ == "__main__":
    unittest.main()
