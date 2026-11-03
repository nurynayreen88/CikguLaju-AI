"""Isolated SQLite simulation of proposed transaction uniqueness. No live connections."""
import sqlite3
import unittest

SCHEMA = '''CREATE TABLE ledger (
 id INTEGER PRIMARY KEY,
 provider TEXT NOT NULL,
 merchant_account_key TEXT NOT NULL,
 bank_transaction_reference TEXT NOT NULL,
 payment_request_id INTEGER NOT NULL UNIQUE,
 telegram_user_id INTEGER NOT NULL,
 amount_rm NUMERIC NOT NULL CHECK(amount_rm > 0),
 verified_by INTEGER NOT NULL,
 UNIQUE(provider, merchant_account_key, bank_transaction_reference)
)'''

class TransactionLedgerTests(unittest.TestCase):
 def setUp(self):
  self.db = sqlite3.connect(':memory:')
  self.db.execute(SCHEMA)
 def tearDown(self): self.db.close()
 def add(self, ref, request, user, merchant='merchant1'):
  self.db.execute('INSERT INTO ledger(provider,merchant_account_key,bank_transaction_reference,payment_request_id,telegram_user_id,amount_rm,verified_by) VALUES(?,?,?,?,?,?,?)', ('TNG',merchant,ref,request,user,10,999))
 def test_two_distinct_transactions(self):
  self.add('TX100',1,101); self.add('TX101',2,102)
  self.assertEqual(self.db.execute('SELECT COUNT(*) FROM ledger').fetchone()[0],2)
 def test_same_transaction_two_users_rejected(self):
  self.add('TX100',1,101)
  with self.assertRaises(sqlite3.IntegrityError): self.add('TX100',2,102)
 def test_same_request_two_transactions_rejected(self):
  self.add('TX100',1,101)
  with self.assertRaises(sqlite3.IntegrityError): self.add('TX101',1,101)
 def test_same_reference_different_merchant_is_distinct(self):
  self.add('TX100',1,101,'merchant1'); self.add('TX100',2,102,'merchant2')
 def test_failed_duplicate_preserves_original(self):
  self.add('TX100',1,101)
  with self.assertRaises(sqlite3.IntegrityError): self.add('TX100',2,102)
  self.assertEqual(self.db.execute('SELECT telegram_user_id FROM ledger').fetchall(),[(101,)])

if __name__ == '__main__': unittest.main(verbosity=2)
