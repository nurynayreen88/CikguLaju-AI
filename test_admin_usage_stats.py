import sqlite3
import unittest
from datetime import datetime, timezone
from admin_usage_stats import initialize, record_event, record_confirmed_delivery, summary

class UsageStatsTests(unittest.TestCase):
    def test_non_destructive_and_counts(self):
        db = sqlite3.connect(':memory:')
        db.execute('CREATE TABLE existing_users (id INTEGER PRIMARY KEY, name TEXT)')
        db.execute("INSERT INTO existing_users VALUES (1,'preserved')")
        initialize(db)
        initialize(db)
        now = datetime(2026, 10, 27, 3, 0, tzinfo=timezone.utc)
        record_event(db, 123, 'bot_active', when=now)
        record_event(db, 123, 'rph_success', 'English', 'Year 1', now)
        record_event(db, 456, 'rph_failed', 'Maths', 'Year 2', now)
        result = summary(db, now)
        self.assertEqual(result['active_today'], 2)
        self.assertEqual(result['active_7d'], 2)
        self.assertEqual(result['rph_success'], 1)
        self.assertEqual(result['rph_failed'], 1)
        self.assertEqual(result['top_subjects'][0], ('English', 1))
        self.assertEqual(db.execute('SELECT name FROM existing_users').fetchone()[0], 'preserved')
        self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_delivery_idempotency(self):
        db = sqlite3.connect(':memory:')
        initialize(db)
        self.assertTrue(record_confirmed_delivery(db, 123, 900, 'BM', 'Tahun 2'))
        self.assertFalse(record_confirmed_delivery(db, 123, 900, 'BM', 'Tahun 2'))
        self.assertTrue(record_confirmed_delivery(db, 456, 900, 'BM', 'Tahun 2'))
        self.assertEqual(summary(db)['rph_success'], 2)
        self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_invalid_event_rejected(self):
        db = sqlite3.connect(':memory:')
        initialize(db)
        with self.assertRaises(ValueError):
            record_event(db, 1, 'unknown')

if __name__ == '__main__':
    unittest.main()
