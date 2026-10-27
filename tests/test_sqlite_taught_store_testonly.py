import sqlite3
import unittest
from rph_hari_ini.sqlite_taught_store_testonly import init_test_db, confirm


class TaughtStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        init_test_db(self.db)
        self.args = dict(teacher="t1", school_year=2027, class_key="5A",
                         subject_key="EN", session_id="s1", lesson=1, total=160,
                         calendar_verified=True, session_verified=True)

    def tearDown(self):
        self.db.close()

    def call(self, **changes):
        return confirm(self.db, **(self.args | changes))

    def test_first_and_idempotent_replay(self):
        self.assertEqual(self.call(), "confirmed")
        self.assertEqual(self.call(), "already_confirmed")
        self.assertEqual(self.db.execute("select count(*) from test_taught_events").fetchone()[0], 1)

    def test_skip_and_rollback(self):
        self.assertEqual(self.call(lesson=2), "non_sequential")
        self.assertEqual(self.db.execute("select count(*) from test_taught_events").fetchone()[0], 0)

    def test_distinct_year(self):
        self.assertEqual(self.call(), "confirmed")
        self.assertEqual(self.call(school_year=2028), "confirmed")

    def test_distinct_class(self):
        self.assertEqual(self.call(), "confirmed")
        self.assertEqual(self.call(class_key="5B"), "confirmed")

    def test_distinct_subject(self):
        self.assertEqual(self.call(), "confirmed")
        self.assertEqual(self.call(subject_key="BM"), "confirmed")

    def test_unverified_rejected(self):
        self.assertEqual(self.call(calendar_verified=False), "blocked")
        self.assertEqual(self.call(session_verified=False), "blocked")

    def test_reused_session_other_lesson(self):
        self.assertEqual(self.call(), "confirmed")
        self.assertEqual(self.call(lesson=2), "conflict")

    def test_other_session_same_lesson(self):
        self.assertEqual(self.call(), "confirmed")
        self.assertEqual(self.call(session_id="s2"), "non_sequential")

    def test_invalid_values(self):
        self.assertEqual(self.call(lesson=True), "blocked")
        self.assertEqual(self.call(school_year=0), "blocked")


if __name__ == "__main__":
    unittest.main()
