"""Focused, no-network regression for #322: direct class entry after PdP selection.

Does not start the Telegram bot, fetch profile data, or write SQLite.
Authenticated end-to-end field testing remains a separate release gate.
"""
import ast
import html
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "app.py"


def load_prompt():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    matches = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name == "_prompt_rph_class"]
    if len(matches) != 1:
        raise AssertionError(f"Expected exactly one class prompt; got {len(matches)}")
    fn = matches[0]
    return compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
                   str(SOURCE), "exec")


class TelegramRphClassPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = load_prompt()

    def invoke(self, s, classes, prefix=""):
        messages = []
        def send(cid, message, buttons):
            messages.append((cid, message, buttons))
        namespace = {
            "_dynamic_class_example": lambda s: "3 Melur",
            "_profile_class_records": lambda cid: classes,
            "send": send,
            "html": html,
        }
        exec(self.code, namespace)
        namespace["_prompt_rph_class"](123, s, prefix)
        return messages

    def test_direct_class_input_is_armed_and_curriculum_unchanged(self):
        original = {
            "waiting": "rph_date",
            "subject": "Matematik", "year": "3", "topic": "Wang",
            "pdp_sequence_code": "MT3-PDP-060",
            "sk": "4.1", "sp": "4.1.1",
            "rph_date": "2026-11-10", "rph_time": "08:00-09:00",
        }
        s = dict(original)
        sent = self.invoke(s, [], "Sila isi kelas")
        self.assertEqual(s["waiting"], "rph_class")
        self.assertEqual({k: v for k, v in s.items() if k != "waiting"},
                         {k: v for k, v in original.items() if k != "waiting"})
        self.assertEqual(len(sent), 1)
        self.assertIn("Pilih atau masukkan kelas", sent[0][1])
        self.assertIn("Tulis Nama Kelas Manual", str(sent[0][2]))

    def test_profile_class_buttons_still_present(self):
        s = {"subject": "Bahasa Melayu", "year": "2"}
        sent = self.invoke(s, [{"name": "2 Amanah", "students": 30}])
        self.assertEqual(s["waiting"], "rph_class")
        self.assertEqual(s["subject"], "Bahasa Melayu")
        self.assertIn("2 Amanah", str(sent[0][2]))
        self.assertIn("30 murid", str(sent[0][2]))
        self.assertIn("rphclass_manual", str(sent[0][2]))


if __name__ == "__main__":
    unittest.main()
