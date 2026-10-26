"""Isolated contract tests for the final Telegram RPH delivery wrapper.

No Telegram credentials or Supabase writes are used.
"""
import ast
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "app.py"

def latest_function(name):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    assert nodes, name
    return compile(ast.Module(body=[nodes[-1]], type_ignores=[]), str(SOURCE), "exec")

class Ack:
    def __init__(self, ok):
        self.ok = ok
    def json(self):
        return {"ok": self.ok}

class TrialDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.state = {42: {"_selected_rph_delivery_pending_20261027": True}}
        self.charges = []
        self.ack = Ack(True)
        self.env = {
            "state": self.state,
            "_RPH_SEND_DOCUMENT_BEFORE_20261027": lambda *a: self.ack,
            "_telegram_delivery_ok_v25279": lambda result: result.ok and result.json()["ok"],
            "_consume_free_after_success_v25282": lambda cid, reason: self.charges.append((cid, reason)),
        }
        exec(latest_function("send_document"), self.env)

    def test_success_charges_once(self):
        send = self.env["send_document"]
        send(42, "test.pdf", "📘 RPH CikguLaju")
        send(42, "test.pdf", "📘 RPH CikguLaju")
        self.assertEqual(len(self.charges), 1)

    def test_failed_delivery_never_charges(self):
        self.ack = Ack(False)
        with self.assertRaises(RuntimeError):
            self.env["send_document"](42, "test.pdf", "📘 RPH CikguLaju")
        self.assertEqual(self.charges, [])

    def test_non_rph_document_never_charges(self):
        self.env["send_document"](42, "worksheet.pdf", "📝 Worksheet CikguLaju")
        self.assertEqual(self.charges, [])

if __name__ == "__main__":
    unittest.main()
