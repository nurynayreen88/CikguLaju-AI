import unittest
from rph_hari_ini.class_identity import rename_class

VALID_ID = "f7bfb88c-ef6e-4d25-b08c-07d6b5a1d0bb"

class RenameSafetyTests(unittest.TestCase):
    def test_missing_old_name(self):
        result = rename_class(teacher_id=1, school_year=2027, old_name=None, new_name="New", registry={})
        self.assertIsNone(result)

    def test_invalid_unrelated_record(self):
        records = {(1, 2027, "A"): VALID_ID, (1, 2027, "B"): "invalid"}
        result = rename_class(teacher_id=1, school_year=2027, old_name="A", new_name="C", registry=records)
        self.assertEqual(result[(1, 2027, "C")], VALID_ID)
        self.assertEqual(records[(1, 2027, "A")], VALID_ID)

    def test_padded_name_collision(self):
        records = {(1, 2027, "A"): VALID_ID, (1, 2027, " B "): "invalid"}
        result = rename_class(teacher_id=1, school_year=2027, old_name="A", new_name="B", registry=records)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
