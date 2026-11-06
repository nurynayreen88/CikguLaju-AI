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

    def test_avatar_selection_appears_in_sidebar_and_profile(self):
        root=Path(__file__).resolve().parents[1]/"web_v1_static_preview"
        html=(root/"index.html").read_text("utf-8")
        js=(root/"teacher-profile.js").read_text("utf-8")
        self.assertIn('id="sidebar-avatar"',html)
        self.assertIn('id="profile-avatar-options"',html)
        self.assertIn('id="profile-avatar-code"',html)
        self.assertIn("aria-pressed",html)
        self.assertIn("avatar_code:avatarValue.value",js)
        self.assertIn("selectTeacherAvatar(profile.avatar_code",js)
        self.assertGreaterEqual(html.count('data-avatar-code='),len(AVATAR_CODES))


if __name__ == "__main__":
    unittest.main()
