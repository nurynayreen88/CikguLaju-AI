"""Tests for read-only PJPK integration preflight."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PJPKPreflightTests(unittest.TestCase):
    def test_required_modules_parse(self):
        for name in (
            "pjpk_rpt_bridge_v2659",
            "pjpk_activity_planner_v2665",
            "pjpk_activity_adapter_v2666",
            "pjpk_rph_quality_v2672",
            "pjpk_rph_composer_v2669",
        ):
            with self.subTest(module=name):
                file = ROOT / (name + ".py")
                self.assertTrue(file.is_file())
                ast.parse(file.read_text(encoding="utf-8"))

    def test_composer_calls_refinement(self):
        source = (ROOT / "pjpk_rph_composer_v2669.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = [
            node.func.id for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        self.assertIn("refine_verified_pjpk_rph", calls)

if __name__ == "__main__":
    unittest.main()
