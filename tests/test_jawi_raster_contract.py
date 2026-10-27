"""Regression checks for Jawi raster layout without importing app.py or opening DB.
Run: python -m unittest discover -s tests -p 'test_jawi_raster_contract.py'
"""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

class JawiRasterContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_no_new_character_substitutions_in_latest_renderer(self):
        classes = [n for n in self.tree.body if isinstance(n, ast.ClassDef)
                   and n.name == "_JawiRasterParagraph_v25213"]
        self.assertGreaterEqual(len(classes), 1)
        latest = classes[-1]
        latest_source = ast.get_source_segment(self.source, latest)
        self.assertIn("_pi_markup_to_plain_v2605", latest_source)
        self.assertIn("ImageFont.Layout.RAQM", latest_source)
        self.assertNotIn("_pi_runtime_glyph_compat_v2603", latest_source)

    def test_original_wrap_preserves_word_order(self):
        classes = [n for n in self.tree.body if isinstance(n, ast.ClassDef)
                   and n.name == "_JawiRasterParagraph_v25213"]
        base = classes[0]
        wrap_line = next(n for n in base.body if isinstance(n, ast.FunctionDef)
                         and n.name == "_wrap_line")
        src = ast.get_source_segment(self.source, wrap_line)
        self.assertIn("line.split()", src)
        self.assertIn("cur+' '+w", src)
        self.assertNotIn("reversed(", src)

    def test_latest_font_is_explicit_raqm(self):
        classes = [n for n in self.tree.body if isinstance(n, ast.ClassDef)
                   and n.name == "_JawiRasterParagraph_v25213"]
        method = next(n for n in classes[-1].body if isinstance(n, ast.FunctionDef)
                      and n.name == "_font")
        src = ast.get_source_segment(self.source, method)
        self.assertIn("layout_engine=ImageFont.Layout.RAQM", src)
        # RAQM is required; BASIC fallback is forbidden.
        self.assertIn("HAVE_RAQM", src)
        self.assertIn("raise RuntimeError", src)
        self.assertNotIn("except Exception", src)

if __name__ == "__main__":
    unittest.main()
