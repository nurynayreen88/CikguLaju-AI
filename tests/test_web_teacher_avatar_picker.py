"""Avatar choices must remain restricted and never overwrite class/timetable data."""
import unittest
from web.teacher_profile_store import clean_profile, ProfileValidation, AVATAR_CODES
from pathlib import Path


def form(**updates):
    return dict({"display_name":"Cikgu A","school_name":"SK Contoh",
                 "state_name":"Selangor","class_names":["4 Bestari"],
                 "avatar_code":"books","version":""}, **updates)


class AvatarContractTests(unittest.TestCase):
    def test_save_valid_avatar_code(self):
        values, version=clean_profile(form())
        self.assertEqual(values["avatar_code"],"books")
        self.assertEqual(values["class_names"],["4 Bestari"])
        self.assertEqual(version,"")

    def test_invalid_avatar_rejected(self):
        for bad in ("<script>", "custom-image-url", "cat", "", None, ["books"]):
            with self.subTest(bad=bad), self.assertRaises(ProfileValidation):
                clean_profile(form(avatar_code=bad))

    def test_old_telegram_profile_payload_preserves_existing_avatar(self):
        old=form()
        old.pop("avatar_code")
        values,_=clean_profile(old)
        self.assertNotIn("avatar_code",values)

    def test_web_no_longer_displays_or_submits_avatar(self):
        root=Path(__file__).resolve().parents[1]/"web_v1_static_preview"
        html=(root/"index.html").read_text("utf-8")
        js=(root/"teacher-profile.js").read_text("utf-8")
        for field in ('id="sidebar-avatar"', 'id="profile-avatar-options"',
                      'id="profile-avatar-code"', 'data-avatar-code=',
                      'teacher-avatar-fieldset', 'teacher-avatar-grid'):
            with self.subTest(field=field):
                self.assertNotIn(field,html)
        for field in ('avatarValue', 'teacherAvatars', 'showTeacherAvatar',
                      'selectTeacherAvatar', 'avatar_code:'):
            with self.subTest(field=field):
                self.assertNotIn(field,js)
        # Teacher name, school, class list and timetable stay fully editable.
        self.assertIn('id="sidebar-teacher-name"',html)
        self.assertIn('id="profile-name"',html)
        self.assertIn('id="profile-classes"',html)
        self.assertIn('id="timetable-rows"',html)
        self.assertIn('setTeacherIdentity(profile)',js)
        self.assertIn('class_names: teacherClassLines()',js)

    def test_new_web_profile_payload_does_not_overwrite_legacy_avatar(self):
        # Backend allows omission of the legacy field, preserving stored data.
        payload=form()
        del payload["avatar_code"]
        values,_=clean_profile(payload)
        self.assertNotIn("avatar_code",values)
        self.assertEqual(values["class_names"],["4 Bestari"])


if __name__ == "__main__":
    unittest.main()
