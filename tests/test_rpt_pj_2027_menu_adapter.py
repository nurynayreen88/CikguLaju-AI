import tempfile
import unittest
from pathlib import Path
from rpt_pj_2027_delivery import FILE_PATTERN
from rpt_pj_2027_menu_adapter import menu_states, menu_years, deliver_selected_rpt


class DummyBot:
    def __init__(self):
        self.calls = []

    def send_document(self, chat_id, handle):
        self.calls.append((chat_id, handle.name))
        return {"ok": True}


class TestRPTMenuAdapter(unittest.TestCase):
    def test_only_existing_documents_appear(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(menu_states(root), [])
            self.assertEqual(menu_years(root, "Johor"), [])
            file = root / FILE_PATTERN.format(state="Johor", year=4)
            file.write_bytes(b"test")
            self.assertEqual(menu_states(root), ["Johor"])
            self.assertEqual(menu_years(root, "Johor"), [4])
            bot = DummyBot()
            with self.assertRaises(PermissionError):
                deliver_selected_rpt(bot, 123, root, negeri="Johor",
                                     tahun=4, paid_access=False)
            self.assertEqual(bot.calls, [])
            deliver_selected_rpt(bot, 123, root, negeri="Johor",
                                 tahun=4, paid_access=True)
            self.assertEqual(len(bot.calls), 1)


if __name__ == "__main__":
    unittest.main()
