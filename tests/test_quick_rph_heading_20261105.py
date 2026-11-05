"""Regression: current Telegram quick step title should match Sediakan RPH menu."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "app.py").read_text(encoding="utf-8")
TREE = ast.parse(SRC, filename="app.py")


class QuickRphStepTitleTests(unittest.TestCase):
    def test_current_quick_step_title_and_content(self):
        quick = next(node for node in reversed(TREE.body)
                     if isinstance(node, ast.FunctionDef) and node.name == "quick")
        scope = {"state": {}, "send": lambda cid, text, buttons: (cid, text, buttons)}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[quick], type_ignores=[])),
                     "app.py", "exec"), scope)
        cid, text, buttons = scope["quick"](321)
        self.assertEqual(cid, 321)
        self.assertTrue(text.startswith("📚 <b>Sediakan RPH</b>"))
        self.assertNotIn("Sediakan Bahan PdP", text)
        for value in ("Tahun/Tingkatan", "Tema/Unit/Tajuk", "Lesson/PdP",
                      "SK/SP", "RPT/SOW", "buku teks", "buku aktiviti",
                      "kelas, tarikh dan masa", "✅ SUBMIT"):
            self.assertIn(value, text)
        self.assertEqual([r[0]["callback_data"] for r in buttons],
                         ["choose_grade", "home"])
        self.assertEqual(scope["state"][321]["task"], "quick_material")

if __name__ == "__main__":
    unittest.main()
