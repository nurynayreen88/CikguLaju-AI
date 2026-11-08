"""Temporary RPH Hari Ini pause regression tests, isolated from Telegram services."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
SOURCE = APP.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE, filename=str(APP))


def last_function(name):
    return next(node for node in reversed(TREE.body)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name)


def isolated_function(node, env):
    tree = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(tree, str(APP), "exec"), env)
    return env[node.name]


class PausedDailyRPHTests(unittest.TestCase):
    def test_main_menu_keeps_manual_flow_and_hides_daily(self):
        calls = []
        def send(cid, body, buttons):
            calls.append((cid, body, buttons))
            return "sent"
        menu = isolated_function(last_function("menu"), {
            "send": send,
            "_is_admin": lambda cid: False,
            "_access_info": lambda cid: {"active": False},
            "_is_permanent_vip_v25267": lambda cid: False,
            "_trial_balance": lambda cid: 10,
            "install_menu_button": lambda cid: None,
        })
        self.assertEqual(menu(321), "sent")
        cid, message, keyboard = calls.pop()
        self.assertEqual(cid, 321)
        callbacks = [b["callback_data"] for row in keyboard for b in row if "callback_data" in b]
        self.assertIn("quick", callbacks)
        self.assertIn("rpt2027_home", callbacks)
        self.assertIn("account", callbacks)
        self.assertIn("pioneer_join", callbacks)
        self.assertNotIn("todayrph272", callbacks)
        self.assertIn("SEDIAKAN RPH", message)
        self.assertIn("Lesson/PdP", message)
        self.assertNotIn("RPH HARI INI", message.upper())
        self.assertIn("Baki janaan RPH", message)

    def test_old_daily_buttons_redirect_and_manual_callbacks_unchanged(self):
        calls = []
        def send(cid, body, keyboard):
            calls.append((cid, body, keyboard))
            return "paused"
        callback = isolated_function(last_function("callback"), {
            "send": send,
            "CIKGULAJU_RPH_HARI_INI_PAUSED_20261105": True,
            "_RPH_HARI_INI_PREVIOUS_CALLBACK_20261105":
                lambda cid, value: ("unchanged", cid, value),
        })
        for value in ("todayrph272", "daily292_generate",
                      "todaybatch273_run", "quicknext275_0",
                      "quickpick275_2", "quickapply276_1"):
            self.assertEqual(callback(321, value), "paused")
            self.assertIn("direhatkan sementara", calls[-1][1])
            self.assertEqual(calls[-1][2][0][0]["callback_data"], "quick")
        count = len(calls)
        for value in ("quick", "home", "account", "rpt2027_home", "pioneer_join"):
            self.assertEqual(callback(321, value), ("unchanged", 321, value))
        self.assertEqual(len(calls), count)

    def test_old_rph_implementation_and_credit_gate_are_preserved(self):
        self.assertIn("def _generate_daily_suggestions_v25292", SOURCE)
        self.assertIn("def _today_rpt_suggestions_v25292", SOURCE)
        self.assertIn("def _submit_materials_v2528", SOURCE)
        self.assertIn("CIKGULAJU_RPH_HARI_INI_PAUSED_20261105 = True", SOURCE)


if __name__ == "__main__":
    unittest.main()
