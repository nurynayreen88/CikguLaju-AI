import sqlite3
import unittest
from pioneer_entitlements import ensure_pioneer_schema, approve_verified_payment, is_pioneer


class PioneerEntitlementTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE legacy_users (id INTEGER PRIMARY KEY, vip_until TEXT)")
        self.db.execute("INSERT INTO legacy_users VALUES (7, '2020-01-01')")
        ensure_pioneer_schema(self.db)

    def test_lifetime_survives_schema_migration(self):
        self.assertTrue(approve_verified_payment(self.db, telegram_user_id=7,
                        payment_reference="DN-123", approved_by=1, verified=True))
        ensure_pioneer_schema(self.db)
        self.assertTrue(is_pioneer(self.db, 7))
        self.assertEqual(self.db.execute("SELECT vip_until FROM legacy_users").fetchone()[0], "2020-01-01")

    def test_unverified_rejected(self):
        with self.assertRaises(ValueError):
            approve_verified_payment(self.db, telegram_user_id=7,
                        payment_reference="DN-123", approved_by=1, verified=False)

    def test_replay_and_duplicate_reference(self):
        args = dict(telegram_user_id=7, payment_reference="DN-123", approved_by=1, verified=True)
        self.assertTrue(approve_verified_payment(self.db, **args))
        self.assertFalse(approve_verified_payment(self.db, **args))
        with self.assertRaises(sqlite3.IntegrityError):
            approve_verified_payment(self.db, telegram_user_id=8,
                        payment_reference="DN-123", approved_by=1, verified=True)


if __name__ == "__main__":
    unittest.main()
