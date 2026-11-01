import sqlite3
import unittest

from web_v1_pairing_cleanup import purge_expired_pairings
from web_v1_pairing_store import initialize_pairing_store, register_pairing


class PairingCleanupTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        initialize_pairing_store(self.db)

    def tearDown(self):
        self.db.close()

    def test_expired_removed_active_preserved(self):
        register_pairing(self.db, "a" * 64, 1000)
        register_pairing(self.db, "b" * 64, 3000)
        self.assertEqual(purge_expired_pairings(self.db, now=2000), 1)
        rows = self.db.execute("SELECT challenge_hash FROM web_v1_pairing_challenges").fetchall()
        self.assertEqual(rows, [("b" * 64,)])

    def test_cleanup_is_bounded(self):
        for i in range(5):
            register_pairing(self.db, format(i, "064x"), 1000)
        self.assertEqual(purge_expired_pairings(self.db, now=2000, batch_size=2), 2)
        self.assertEqual(self.db.execute("SELECT count(*) FROM web_v1_pairing_challenges").fetchone()[0], 3)

    def test_invalid_batch_size_rejected(self):
        with self.assertRaises(ValueError):
            purge_expired_pairings(self.db, batch_size=0)


if __name__ == "__main__":
    unittest.main()
