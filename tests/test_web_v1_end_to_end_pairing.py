"""Isolated end-to-end pairing test: no production bot or DB access."""
import sqlite3
import unittest

from web_v1_browser_binding import create_browser_binding
from web_v1_pairing_challenges import new_pairing_challenge
from web_v1_pairing_session import finish_verified_pairing
from web_v1_pairing_store import initialize_pairing_store, register_pairing, confirm_pairing
from web_v1_sessions import verify_session_ticket


class EndToEndPairingTests(unittest.TestCase):
    def test_phone_confirmation_issues_single_desktop_session(self):
        signing_key = "test-only-secret-with-at-least-32-characters"
        with sqlite3.connect(":memory:") as db:
            initialize_pairing_store(db)
            qr_token, qr_digest, expires_at = new_pairing_challenge(now=1000)
            browser_secret, browser_mac = create_browser_binding(qr_digest, signing_key)
            register_pairing(db, qr_digest, expires_at)

            # Only the authenticated Telegram bot handler may call confirmation.
            self.assertTrue(confirm_pairing(db, qr_token, 314159, now=1001))
            existing_account = lambda uid: {"telegram_user_id": uid} if uid == 314159 else None

            # Another browser cannot steal the pending session with the QR token.
            self.assertIsNone(finish_verified_pairing(
                db, qr_digest, "another-browser", browser_mac, signing_key,
                existing_account, signing_key, now=1002))

            ticket = finish_verified_pairing(
                db, qr_digest, browser_secret, browser_mac, signing_key,
                existing_account, signing_key, now=1002)
            self.assertEqual(verify_session_ticket(ticket, signing_key, now=1003), 314159)

            # Replay is impossible even with the original browser's valid proof.
            self.assertIsNone(finish_verified_pairing(
                db, qr_digest, browser_secret, browser_mac, signing_key,
                existing_account, signing_key, now=1004))
            self.assertIsNone(verify_session_ticket(ticket, signing_key, now=50000))

    def test_unknown_telegram_account_never_gets_session(self):
        signing_key = "test-only-secret-with-at-least-32-characters"
        with sqlite3.connect(":memory:") as db:
            initialize_pairing_store(db)
            token, digest, expiry = new_pairing_challenge(now=1000)
            browser_secret, mac = create_browser_binding(digest, signing_key)
            register_pairing(db, digest, expiry)
            self.assertTrue(confirm_pairing(db, token, 271828, now=1001))
            self.assertIsNone(finish_verified_pairing(
                db, digest, browser_secret, mac, signing_key,
                lambda uid: None, signing_key, now=1002))


if __name__ == "__main__":
    unittest.main()
