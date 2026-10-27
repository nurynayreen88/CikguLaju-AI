"""Test the actual late-bound v26.39 font resolver without importing bot."""
import ast
from pathlib import Path
import unittest

def resolver(cmap, fallback):
    tree=ast.parse(Path("app.py").read_text(encoding="utf-8"))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_pi_exact_jawi_font_v2604"]
    assert len(nodes)>=2
    scope={"_pi2639_exact_font":lambda text,bold=False:None,
           "_pi2638_best_nonfatal_font":lambda text,bold=False:fallback,
           "_pi2637_required_cps":lambda text:{ord(c) for c in str(text) if 0x600<=ord(c)<=0x8ff},
           "_font_cmap_v25226":lambda path:cmap,
           "_pi2639_prev_exact":lambda text,bold=False:None}
    exec(compile(ast.Module(body=[nodes[-1]],type_ignores=[]),"app.py","exec"),scope)
    return scope["_pi_exact_jawi_font_v2604"]

class FontCoverage(unittest.TestCase):
    def test_missing_jawi_gaf_rejected(self):
        with self.assertRaisesRegex(RuntimeError,r"U\\+0762"):
            resolver({ord("ا")},"incomplete.ttf")("اݢ")
    def test_complete_font_accepted(self):
        self.assertEqual(resolver({ord("ا"),ord("ݢ")},"complete.ttf")("اݢ"),"complete.ttf")
    def test_absent_font_rejected(self):
        with self.assertRaisesRegex(RuntimeError,"no usable font"):
            resolver(set(),None)("ݢ")

if __name__=="__main__":
    unittest.main()
