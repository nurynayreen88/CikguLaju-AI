import unittest
from scripts.check_t2_pk_editorial import audit, CANDIDATE_IDS, EDITORIAL_SP, EXPECTED_IDS

class TestT2PKEditorialLocks(unittest.TestCase):
    def test_current_staging_inventory(self):
        errors, count, unique = audit()
        self.assertEqual((count, unique, errors), (18, 18, []))

    def test_exact_identity_partition(self):
        self.assertEqual(len(CANDIDATE_IDS), 11)
        self.assertEqual(len(EDITORIAL_SP), 7)
        self.assertFalse(CANDIDATE_IDS.intersection(EDITORIAL_SP))
        self.assertEqual(len(EXPECTED_IDS), 18)

if __name__ == "__main__":
    unittest.main()
