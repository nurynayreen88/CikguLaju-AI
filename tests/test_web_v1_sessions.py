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

    def test_remembered_session_valid_for_14_days_only(self):
        issued = 1800000000
        ticket = issue_session_ticket(8000000000000000003, SECRET, now=issued, remember=True)
        self.assertTrue(ticket.startswith("v2."))
        self.assertEqual(verify_session_ticket(ticket, SECRET, now=issued+8*86400),
                         8000000000000000003)
        self.assertEqual(verify_session_ticket(ticket, SECRET, now=issued+14*86400),
                         8000000000000000003)
        self.assertIsNone(verify_session_ticket(ticket, SECRET, now=issued+14*86400+1))

    def test_remembered_option_cannot_be_added_to_legacy_ticket(self):
        issued = 1800000000
        normal = issue_session_ticket(12345, SECRET, now=issued)
        self.assertTrue(normal.startswith("v1."))
        self.assertIsNone(verify_session_ticket(normal, SECRET, now=issued+86400))
        claimed_remembered = normal.replace("v1.", "v2.", 1).replace(
            ".12345.", ".12345.remember.", 1)
        self.assertIsNone(verify_session_ticket(claimed_remembered, SECRET, now=issued+5))

    def test_remembered_ticket_tampering_invalidates_signature(self):
        ticket = issue_session_ticket(12345, SECRET, now=1800000000, remember=True)
        self.assertIsNone(verify_session_ticket(ticket.replace(".12345.", ".67890."),
                                                 SECRET, now=1800000001))
        self.assertIsNone(verify_session_ticket(ticket.replace(".remember.", ".normal."),
                                                 SECRET, now=1800000001))
        self.assertIsNone(verify_session_ticket(ticket, SECRET, now=1800000001,
                                                ttl_seconds=0))
        self.assertIsNone(verify_session_ticket(ticket, SECRET, now=1800000001,
                                                ttl_seconds=True))
        self.assertEqual(verify_session_ticket(ticket, SECRET, now=1800000002,
                                               ttl_seconds=3), 12345)
        self.assertIsNone(verify_session_ticket(ticket, SECRET, now=1800000004,
                                                ttl_seconds=3))

    def test_remember_flag_must_be_real_boolean(self):
        with self.assertRaises(ValueError):
            issue_session_ticket(12345, SECRET, remember="true")
        with self.assertRaises(ValueError):
            issue_session_ticket(12345, SECRET, remember=1)


if __name__ == "__main__":
    unittest.main()
