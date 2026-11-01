import unittest

from web_v1_sessions import issue_session_ticket, verify_session_ticket

SECRET = "test-only-session-secret-with-at-least-32-chars"


class WebSessionTests(unittest.TestCase):
    def test_valid_session(self):
        ticket = issue_session_ticket(12345, SECRET, now=1800000000)
        self.assertEqual(verify_session_ticket(ticket, SECRET, now=1800000010), 12345)

    def test_tampered_user_id(self):
        ticket = issue_session_ticket(12345, SECRET, now=1800000000)
        self.assertIsNone(verify_session_ticket(ticket.replace(".12345.", ".99999."), SECRET, now=1800000010))

    def test_expired_session(self):
        ticket = issue_session_ticket(12345, SECRET, now=1800000000)
        self.assertIsNone(verify_session_ticket(ticket, SECRET, now=1800050000))

    def test_future_session(self):
        ticket = issue_session_ticket(12345, SECRET, now=1800000000)
        self.assertIsNone(verify_session_ticket(ticket, SECRET, now=1799999999))

    def test_wrong_secret(self):
        ticket = issue_session_ticket(12345, SECRET, now=1800000000)
        self.assertIsNone(verify_session_ticket(ticket, "another-test-secret-with-at-least-32-chars", now=1800000010))

    def test_short_secret_is_rejected(self):
        with self.assertRaises(ValueError):
            issue_session_ticket(12345, "short", now=1800000000)


if __name__ == "__main__":
    unittest.main()
