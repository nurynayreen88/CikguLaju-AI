import unittest
from rph_trial_reservation import (
    TrialReservationClient, TrialReservationError,
    deliver_with_trial, telegram_document_confirmed,
)


class Response:
    ok = True

    def __init__(self, delivered=True):
        self.delivered = delivered

    def json(self):
        return {"ok": self.delivered,
                "result": {"message_id": 123} if self.delivered else {}}


class TrialReservationTests(unittest.TestCase):
    def make_client(self, fail_commit=False):
        calls = []

        def rpc(name, payload):
            calls.append(name)
            if name.endswith("reserve_rph_trial"):
                return [{"ok": True, "remaining": 1, "reservation_status": "reserved"}]
            if name.endswith("commit_rph_trial"):
                if fail_commit:
                    raise RuntimeError("Database unavailable")
                return [{"ok": True, "remaining": 0, "reservation_status": "committed"}]
            if name.endswith("release_rph_trial"):
                return [{"ok": True, "reservation_status": "released"}]
            raise AssertionError(name)

        return TrialReservationClient(rpc), calls

    def test_success_commits_once(self):
        client, calls = self.make_client()
        response, remaining = deliver_with_trial(client, 42, "request-12345",
                                                 lambda: b"pdf", lambda _: Response())
        self.assertTrue(telegram_document_confirmed(response))
        self.assertEqual(remaining, 0)
        self.assertEqual([x.split("_")[1] for x in calls], ["reserve", "commit"])

    def test_failed_render_releases(self):
        client, calls = self.make_client()
        def broken():
            raise ValueError("render failed")
        with self.assertRaises(ValueError):
            deliver_with_trial(client, 42, "request-12345", broken, lambda _: Response())
        self.assertEqual(len(calls), 2)
        self.assertIn("release", calls[-1])

    def test_unconfirmed_delivery_retains_reservation(self):
        client, calls = self.make_client()
        with self.assertRaises(TrialReservationError):
            deliver_with_trial(client, 42, "request-12345",
                               lambda: b"pdf", lambda _: Response(False))
        self.assertEqual(calls, ["cikgulaju_reserve_rph_trial"])

    def test_transport_error_keeps_reservation(self):
        client, calls = self.make_client()
        def broken_send(_):
            raise TimeoutError("Connection dropped after upload")
        with self.assertRaises(TrialReservationError):
            deliver_with_trial(client, 42, "request-12345", lambda: b"pdf", broken_send)
        self.assertEqual(calls, ["cikgulaju_reserve_rph_trial"])

    def test_commit_failure_keeps_reservation(self):
        client, calls = self.make_client(fail_commit=True)
        with self.assertRaises(RuntimeError):
            deliver_with_trial(client, 42, "request-12345",
                               lambda: b"pdf", lambda _: Response())
        self.assertEqual(len(calls), 2)
        self.assertIn("commit", calls[-1])

    def test_ambiguous_transport_error_keeps_reservation(self):
        client, calls = self.make_client()
        def network_timeout(_):
            raise TimeoutError("Telegram response lost")
        with self.assertRaises(TrialReservationError):
            deliver_with_trial(client, 42, "request-12345",
                               lambda: b"pdf", network_timeout)
        self.assertEqual(len(calls), 1)
        self.assertIn("reserve", calls[0])

    def test_invalid_telegram_user_id(self):
        client, calls = self.make_client()
        for user_id in (True, 0, -1, "42", None):
            with self.subTest(user_id=user_id), self.assertRaises(ValueError):
                client.reserve(user_id, "request-12345")
        self.assertEqual(calls, [])

    def test_invalid_telegram_message_id(self):
        class InvalidResponse:
            ok = True
            def json(self):
                return {"ok": True, "result": {"message_id": True}}
        self.assertFalse(telegram_document_confirmed(InvalidResponse()))

    def test_missing_telegram_message_id_never_commits(self):
        client, calls = self.make_client()
        class MissingMessageId:
            ok = True
            def json(self):
                return {"ok": True, "result": {}}
        with self.assertRaises(TrialReservationError):
            deliver_with_trial(client, 42, "request-12345",
                               lambda: b"pdf", lambda _: MissingMessageId())
        self.assertEqual(calls, ["cikgulaju_reserve_rph_trial"])

    def test_failed_render_never_calls_send_or_commit(self):
        client, calls = self.make_client()
        sent = []
        def render_failure():
            raise RuntimeError("PDF failed")
        with self.assertRaises(RuntimeError):
            deliver_with_trial(client, 42, "request-12345",
                               render_failure, lambda doc: sent.append(doc))
        self.assertFalse(sent)
        self.assertEqual(calls, [
            "cikgulaju_reserve_rph_trial",
            "cikgulaju_release_rph_trial",
        ])

    def test_reconcile_only_commits_without_sending(self):
        client, calls = self.make_client()
        remaining = client.reconcile_confirmed_delivery(42, "request-12345")
        self.assertEqual(remaining, 0)
        self.assertEqual(calls, ["cikgulaju_commit_rph_trial"])

    def test_failed_release_reports_uncertain_reservation(self):
        calls = []
        def rpc(name, payload):
            calls.append(name)
            if name.endswith("reserve_rph_trial"):
                return [{"ok": True, "remaining": 1, "reservation_status": "reserved"}]
            if name.endswith("release_rph_trial"):
                raise ConnectionError("Database unreachable")
            raise AssertionError(name)
        client = TrialReservationClient(rpc)
        def broken_render():
            raise ValueError("PDF rendering failed")
        with self.assertRaisesRegex(TrialReservationError, "release is unconfirmed"):
            deliver_with_trial(client, 42, "request-12345", broken_render,
                               lambda _: self.fail("must not send"))
        self.assertEqual(calls, ["cikgulaju_reserve_rph_trial",
                                 "cikgulaju_release_rph_trial"])

    def test_reconcile_requires_valid_message_id(self):
        client, calls = self.make_client()
        for invalid in (None, 0, -1, True, "123"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    client.reconcile_confirmed_delivery(42, "request-12345", invalid)
        self.assertEqual(calls, [])

    def test_reconcile_commits_without_resend(self):
        client, calls = self.make_client()
        remaining = client.reconcile_confirmed_delivery(42, "request-12345", 123)
        self.assertEqual(remaining, 0)
        self.assertEqual(calls, ["cikgulaju_commit_rph_trial"])

    def test_invalid_request_id(self):
        client, _ = self.make_client()
        with self.assertRaises(ValueError):
            client.reserve(42, "short")


if __name__ == "__main__":
    unittest.main()
