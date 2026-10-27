import sqlite3
import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from admin_usage_stats import initialize, record_event, record_confirmed_delivery, record_daily_active, summary

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

    def test_generic_event_timezone_normalized(self):
        db = sqlite3.connect(':memory:')
        initialize(db)
        malaysia = timezone(timedelta(hours=8))
        local_time = datetime(2026, 10, 27, 0, 30, tzinfo=malaysia)
        record_event(db, 123, 'rph_success', when=local_time)
        stored = db.execute(
            "SELECT created_at FROM admin_usage_events WHERE event_type='rph_success'"
        ).fetchone()[0]
        self.assertEqual(stored, '2026-10-26T16:30:00+00:00')
        self.assertEqual(summary(db, datetime(2026, 10, 26, 17, 0, tzinfo=timezone.utc))['active_today'], 1)

    def test_generic_event_rejects_naive_timestamp(self):
        db = sqlite3.connect(':memory:')
        initialize(db)
        with self.assertRaises(ValueError):
            record_event(db, 123, 'bot_active', when=datetime(2026, 10, 27))

    def test_delivery_idempotency(self):
        db = sqlite3.connect(':memory:')
        initialize(db)
        self.assertTrue(record_confirmed_delivery(db, 123, 900, 'BM', 'Tahun 2'))
        self.assertFalse(record_confirmed_delivery(db, 123, 900, 'BM', 'Tahun 2'))
        self.assertTrue(record_confirmed_delivery(db, 456, 900, 'BM', 'Tahun 2'))
        self.assertEqual(summary(db)['rph_success'], 2)
        self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_daily_activity_deduplicated(self):
        db = sqlite3.connect(':memory:')
        initialize(db)
        now = datetime(2026, 10, 27, 3, 0, tzinfo=timezone.utc)
        self.assertTrue(record_daily_active(db, 123, now))
        self.assertFalse(record_daily_active(db, 123, now))
        self.assertTrue(record_daily_active(db, 456, now))
        self.assertEqual(summary(db, now)['active_today'], 2)

    def test_daily_activity_persists_across_connections(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / 'usage.sqlite')
            first = sqlite3.connect(path)
            initialize(first)
            now = datetime(2026, 10, 27, 3, 0, tzinfo=timezone.utc)
            self.assertTrue(record_daily_active(first, 123, now))
            first.close()
            second = sqlite3.connect(path)
            self.assertFalse(record_daily_active(second, 123, now))
            self.assertEqual(summary(second, now)['active_today'], 1)
            self.assertEqual(second.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            second.close()

    def test_active_recorder_rejects_existing_transaction(self):
        db = sqlite3.connect(':memory:')
        initialize(db)
        db.execute('CREATE TABLE unrelated (value TEXT)')
        db.execute("INSERT INTO unrelated VALUES ('pending')")
        with self.assertRaises(sqlite3.OperationalError):
            record_daily_active(db, 123)
        self.assertTrue(db.in_transaction)
        db.rollback()
        self.assertEqual(db.execute('SELECT COUNT(*) FROM unrelated').fetchone()[0], 0)

    def test_active_recorder_handles_separate_utc_days(self):
        db = sqlite3.connect(':memory:')
        initialize(db)
        first = datetime(2026, 10, 27, 23, 59, tzinfo=timezone.utc)
        second = datetime(2026, 10, 28, 0, 1, tzinfo=timezone.utc)
        self.assertTrue(record_daily_active(db, 123, first))
        self.assertTrue(record_daily_active(db, 123, second))
        self.assertEqual(summary(db, second)['active_today'], 1)
        self.assertEqual(summary(db, second)['active_7d'], 1)

    def test_timezone_offset_normalized_to_utc(self):
        db = sqlite3.connect(':memory:')
        initialize(db)
        malaysia = timezone(timedelta(hours=8))
        local = datetime(2026, 10, 28, 7, 30, tzinfo=malaysia)
        utc = datetime(2026, 10, 27, 23, 30, tzinfo=timezone.utc)
        self.assertTrue(record_daily_active(db, 123, local))
        self.assertFalse(record_daily_active(db, 123, utc))
        self.assertEqual(summary(db, utc)['active_today'], 1)

    def test_invalid_event_rejected(self):
        db = sqlite3.connect(':memory:')
        initialize(db)
        with self.assertRaises(ValueError):
            record_event(db, 1, 'unknown')

if __name__ == '__main__':
    unittest.main()
