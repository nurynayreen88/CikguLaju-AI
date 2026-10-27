"""Regression checks for Jawi PDF source-preservation and RAQM requirement.

These checks inspect the active implementation without importing app.py (which
has application startup side effects). Run: python -m unittest tests/test_jawi_render_guards.py
"""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

def latest_function(name):
    return next(node for node in reversed(TREE.body)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)

def latest_renderer():
    return next(node for node in reversed(TREE.body)
                if isinstance(node, ast.ClassDef) and node.name == "_JawiRasterParagraph_v25213")

class JawiRenderGuards(unittest.TestCase):
    def test_markup_preserves_source_terms_and_joiners(self):
        nodes = [latest_function("_pi_safe_unicode_v2602"),
                 latest_function("_pi_markup_to_plain_v2605")]
        scope = {}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "<jawi-parser>", "exec"), scope)
        sample = "<b>ݢورو‌ ممباچ‍ gallery walk</b><br/>موريد"
        actual, bold = scope["_pi_markup_to_plain_v2605"](sample)
        self.assertEqual(actual, "ݢورو‌ ممباچ‍ gallery walk\nموريد")
        self.assertFalse(bold)  # bold wrapper does not cover the final line
        self.assertNotIn("ݢاليري", actual)

    def test_jawi_activity_heading_is_marked_up(self):
        node = latest_function("_rph_activity_heading_markup_v25184")
        import re
        from xml.sax.saxutils import escape
        scope = {"re": re, "escape": escape,
                 "_pi2639_split_existing_activity_labels": lambda text: text,
                 "_pi2639_prev_activity_markup": lambda text: "<b>" + escape(text.split("\\n")[0]) + "</b><br/>" + escape(text.split("\\n")[1])}
        exec(compile(ast.Module(body=[node], type_ignores=[]), "<jawi-heading>", "exec"), scope)
        format_lines = scope["_rph_activity_heading_markup_v25184"]
        sample = "اکتيۏيتي 1 – ممباچ\\nموريد ممباچ"
        self.assertEqual(format_lines(sample), "<b>اکتيۏيتي 1 – ممباچ</b><br/>موريد ممباچ")

    def test_renderer_requires_raqm_without_silent_basic_fallback(self):
        node = latest_renderer()
        method = next(n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == "_font")
        scope = {"ImageFont": None}
        class FakeCore:
            HAVE_RAQM = False
        class FakeImageFont:
            core = FakeCore()
        scope["ImageFont"] = FakeImageFont
        # _font imports ImageFont internally; inspect AST instead of executing import.
        calls = [n for n in ast.walk(method) if isinstance(n, ast.Call)]
        self.assertEqual(sum(isinstance(n.func, ast.Attribute) and n.func.attr == "truetype" for n in calls), 1)
        self.assertTrue(any(isinstance(n, ast.Raise) for n in ast.walk(method)))
        self.assertIn("HAVE_RAQM", ast.unparse(method))

if __name__ == "__main__":
    unittest.main()
