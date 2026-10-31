"""Fail-closed checks for the CikguLaju Web V1 integration boundary.

These tests do not import the production app or connect to any database.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WebV1BoundaryTests(unittest.TestCase):
    def test_preview_runner_binds_loopback_only(self):
        source = (ROOT / "tools" / "run_web_v1_preview.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "run"
        ]
        self.assertEqual(len(calls), 1)
        hosts = [kw.value.value for kw in calls[0].keywords
                 if kw.arg == "host" and isinstance(kw.value, ast.Constant)]
        self.assertEqual(hosts, ["127.0.0.1"])

    def test_preview_does_not_import_production_app(self):
        for filename in ("cikgulaju_web_v1.py", "web_v1_lesson_catalog.py",
                         "web_v1_sqlite_catalog.py", "tools/run_web_v1_preview.py"):
            with self.subTest(filename=filename):
                tree = ast.parse((ROOT / filename).read_text(encoding="utf-8"))
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.extend(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imports.append(node.module)
                self.assertNotIn("app", imports)

    def test_preview_has_no_rph_generation_route(self):
        source = (ROOT / "tools" / "run_web_v1_preview.py").read_text(encoding="utf-8")
        self.assertNotIn("/api/rph", source)
        self.assertNotIn("/generate", source)


if __name__ == "__main__":
    unittest.main()
