import unittest
from unittest.mock import patch
from rpt_pj_2027_handlers import show_years, handle_year, handle_document

class FakeBot:
    def __init__(self):
        self.messages = []
    def send_message(self, chat_id, message, reply_markup=None):
        self.messages.append((chat_id, message, reply_markup))
        return self.messages[-1]

class TestHandlers(unittest.TestCase):
    def test_free_user_sees_locked_teaser(self):
        bot = FakeBot()
        with patch("rpt_pj_2027_handlers.year_markup", return_value="menu"):
            show_years(bot, 10, "/missing", authorized=False)
        self.assertIn("Pengguna percuma", bot.messages[0][1])

    def test_year_routes_to_state_markup(self):
        bot = FakeBot()
        with patch("rpt_pj_2027_handlers.state_markup", return_value="states"):
            handle_year(bot, 10, "/missing", "rptpj27year:4")
        self.assertEqual(bot.messages[0][2], "states")

    def test_access_denied_never_sends_document(self):
        bot = FakeBot()
        handle_document(bot, 10, "/missing", "rptpj27:Johor:4",
                        user_id=20, access_resolver=lambda user_id: {})
        self.assertIn("langganan aktif", bot.messages[0][1])

if __name__ == "__main__":
    unittest.main()
