import unittest
import sqlite3
from admin_usage_telegram import format_usage_summary, is_admin
from admin_usage_adapter import show_admin_usage

class AdminUsageTelegramTests(unittest.TestCase):
    def test_exact_admin_id_only(self):
        self.assertTrue(is_admin(123, ['123', '456']))
        self.assertFalse(is_admin(12, ['123']))
        self.assertFalse(is_admin(None, ['123']))
        self.assertFalse(is_admin(123, []))

    def test_admin_id_matching_rejects_prefix_and_similar_values(self):
        allowed_ids = ['123', '456']
        for candidate in (1, 12, 1234, 4567, None, ''):
            with self.subTest(candidate=candidate):
                self.assertFalse(is_admin(candidate, allowed_ids))
        self.assertTrue(is_admin(123, allowed_ids))
        self.assertTrue(is_admin(456, allowed_ids))

    def test_admin_id_matching_does_not_accept_whitespace_in_request(self):
        self.assertFalse(is_admin(' 123', ['123']))
        self.assertFalse(is_admin('123 ', ['123']))
        self.assertTrue(is_admin(123, [' 123 ']))

    def test_non_admin_cannot_open_database(self):
        sent = []
        def forbidden_database():
            raise AssertionError('Unauthorized database access')
        allowed = show_admin_usage(
            42, lambda cid: False, forbidden_database,
            lambda cid, message, **kwargs: sent.append(message))
        self.assertFalse(allowed)
        self.assertIn('hanya untuk admin', sent[0])

    def test_admin_report_closes_database_before_sending(self):
        sent = []
        class TrackedConnection:
            def __init__(self):
                self.db = sqlite3.connect(':memory:')
                self.closed = False
            def executescript(self, sql):
                return self.db.executescript(sql)
            def execute(self, *args):
                return self.db.execute(*args)
            def close(self):
                self.closed = True
                self.db.close()
        tracked = TrackedConnection()
        self.assertTrue(show_admin_usage(
            42, lambda cid: cid == 42, lambda: tracked,
            lambda cid, message, **kwargs: sent.append((tracked.closed, message))))
        self.assertEqual(len(sent), 1)
        self.assertTrue(sent[0][0], 'Database should close before Telegram send')

    def test_admin_report_closes_database_on_query_failure(self):
        class FailingConnection:
            closed = False
            def executescript(self, sql):
                raise sqlite3.OperationalError('simulated database failure')
            def close(self):
                self.closed = True
        tracked = FailingConnection()
        with self.assertRaises(sqlite3.OperationalError):
            show_admin_usage(42, lambda cid: True, lambda: tracked,
                             lambda *args, **kwargs: self.fail('Must not send a partial report'))
        self.assertTrue(tracked.closed, 'Database must close after report failure')

    def test_admin_report_closes_database_on_summary_failure(self):
        class FailingSummaryConnection:
            closed = False
            def executescript(self, sql):
                return None
            def execute(self, *args):
                raise sqlite3.OperationalError('simulated summary failure')
            def close(self):
                self.closed = True
        tracked = FailingSummaryConnection()
        with self.assertRaises(sqlite3.OperationalError):
            show_admin_usage(42, lambda cid: True, lambda: tracked,
                             lambda *args, **kwargs: self.fail('Must not send partial summary'))
        self.assertTrue(tracked.closed)

    def test_admin_summary_navigation(self):
        sent = []
        def db_factory():
            return sqlite3.connect(':memory:')
        allowed = show_admin_usage(
            42, lambda cid: cid == 42, db_factory,
            lambda cid, message, **kwargs: sent.append((message, kwargs)))
        self.assertTrue(allowed)
        self.assertIn('STATISTIK ADMIN', sent[0][0])
        self.assertEqual(
            sent[0][1]['kb'][1][0]['callback_data'], 'admin_panel')

    def test_refresh_is_authorized_and_reopens_summary(self):
        sent = []
        opened = []
        def db_factory():
            opened.append(True)
            return sqlite3.connect(':memory:')
        for _ in range(2):
            self.assertTrue(show_admin_usage(
                42, lambda cid: cid == 42, db_factory,
                lambda cid, message, **kwargs: sent.append((message, kwargs))))
        self.assertEqual(len(opened), 2)
        self.assertEqual(len(sent), 2)
        for message, kwargs in sent:
            self.assertIn('STATISTIK ADMIN', message)
            self.assertEqual(kwargs['kb'][0][0]['callback_data'], 'admin_usage_stats')
            self.assertEqual(kwargs['kb'][1][0]['callback_data'], 'admin_panel')

    def test_non_admin_refresh_rejected(self):
        sent = []
        def forbidden_database():
            raise AssertionError('Non-admin refresh accessed database')
        self.assertFalse(show_admin_usage(
            99, lambda cid: False, forbidden_database,
            lambda cid, message, **kwargs: sent.append(message)))
        self.assertIn('hanya untuk admin', sent[0])

    def test_html_escapes_malicious_subject_names(self):
        stats = dict(active_today=0, active_7d=0, active_30d=0,
                     rph_success=1,
                     top_subjects=[('<script>alert("x")</script> & Bahasa', 1)])
        output = format_usage_summary(stats)
        self.assertNotIn('<script>', output)
        self.assertIn('&lt;script&gt;', output)
        self.assertIn('&amp; Bahasa', output)

    def test_html_escaped_and_zero_stats(self):
        stats = dict(active_today=1, active_7d=2, active_30d=3,
                     rph_success=4, rph_failed=0,
                     top_subjects=[('<English & BM>', 4)])
        output = format_usage_summary(stats)
        self.assertIn('&lt;English &amp; BM&gt;', output)
        self.assertNotIn('<English & BM>', output)
        self.assertIn('RPH berjaya: <b>4</b>', output)

if __name__ == '__main__':
    unittest.main()
