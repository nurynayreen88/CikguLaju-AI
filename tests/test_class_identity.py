import unittest
from rph_hari_ini.class_identity import resolve_class_identity, rename_class

UID = "f7bfb88c-ef6e-4d25-b08c-07d6b5a1d0bb"


class ClassIdentityTests(unittest.TestCase):
    def setUp(self):
        self.registry = {(123, 2027, "5 Amanah"): UID}

    def test_resolve(self):
        item = resolve_class_identity(teacher_id=123, school_year=2027, class_name="5 Amanah", registry=self.registry)
        self.assertEqual(item.class_id, UID)

    def test_unknown_class_blocked(self):
        self.assertIsNone(resolve_class_identity(teacher_id=123, school_year=2027, class_name="5 Bestari", registry=self.registry))

    def test_wrong_teacher_blocked(self):
        self.assertIsNone(resolve_class_identity(teacher_id=456, school_year=2027, class_name="5 Amanah", registry=self.registry))

    def test_wrong_year_blocked(self):
        self.assertIsNone(resolve_class_identity(teacher_id=123, school_year=2028, class_name="5 Amanah", registry=self.registry))

    def test_rename_preserves_identity_and_original(self):
        new = rename_class(teacher_id=123, school_year=2027, old_name="5 Amanah", new_name="5 Cemerlang", registry=self.registry)
        self.assertEqual(new[(123, 2027, "5 Cemerlang")], UID)
        self.assertIn((123, 2027, "5 Amanah"), self.registry)

    def test_collision_blocked(self):
        original = dict(self.registry)
        original[(123, 2027, "5 Bestari")] = "a8b8b77a-7747-481b-a2d0-caf0188c8ad9"
        self.assertIsNone(rename_class(teacher_id=123, school_year=2027, old_name="5 Amanah", new_name="5 Bestari", registry=original))

    def test_invalid_id_blocked(self):
        self.assertIsNone(resolve_class_identity(teacher_id=123, school_year=2027, class_name="5 Amanah", registry={(123, 2027, "5 Amanah"): "bad"}))


if __name__ == "__main__":
    unittest.main()
