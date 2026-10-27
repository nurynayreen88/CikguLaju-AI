import unittest
from rph_hari_ini.class_identity import rename_class

class AlternateUUIDTests(unittest.TestCase):
    def test_unhyphenated_uuid_rename(self):
        original = "f7bfb88cef6e4d25b08c07d6b5a1d0bb"
        records = {(1, 2027, "A"): original}
        updated = rename_class(teacher_id=1, school_year=2027,
                               old_name="A", new_name="B", registry=records)
        self.assertEqual(updated[(1, 2027, "B")],
                         "f7bfb88c-ef6e-4d25-b08c-07d6b5a1d0bb")

if __name__ == "__main__":
    unittest.main()
