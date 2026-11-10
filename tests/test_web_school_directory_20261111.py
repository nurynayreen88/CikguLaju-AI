"""Regression for authenticated Supabase directory and non-destructive teacher profiles.

All authentication, HTTP and database writes are mocked. Does not touch
production teacher profiles or real account data.
"""
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from web.teacher_profile_routes import bp
from web.teacher_profile_store import (
    ProfileValidation, clean_profile, get_profile, save_profile,
)
from web.school_directory_store import states, districts, schools, school_by_code


class SchoolProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = Flask(__name__)
        app.register_blueprint(bp)
        cls.client = app.test_client()

    @staticmethod
    def school():
        return {"school_code": "JBA0001",
                "school_name": "SEKOLAH KEBANGSAAN LUBOK",
                "state_name": "Johor", "district_name": "PPD BATU PAHAT",
                "school_level": "Rendah"}

    @staticmethod
    def form(**changed):
        return {
            "display_name": "Cikgu Ahmad",
            "school_name": "fake manually typed name",
            "state_name": "Johor",
            "district_name": "PPD BATU PAHAT",
            "school_code": "JBA0001",
            "class_names": ["4 Amanah"],
            "version": "",
            **changed,
        }

    def test_cascade_reads_supabase_dimensions_without_exposing_keys(self):
        calls = []
        def read(url, secret, table, query, **kwargs):
            calls.append((table, query))
            if table == "school_states":
                return [{"state_name": "Johor"}]
            if table == "school_districts":
                return [{"district_name": "PPD BATU PAHAT"}]
            if "school_code" in query:
                return [self.school()]
            return [{k:self.school()[k] for k in ("school_code","school_name")}
                    | {"school_level":"Rendah"}]
        with patch("web.school_directory_store._read",side_effect=read):
            self.assertEqual(states("https://db.example.invalid","TEST_KEY"),
                             [{"value":"Johor","label":"Johor"}])
            self.assertEqual(districts("https://db.example.invalid","TEST_KEY","Johor"),
                             [{"value":"PPD BATU PAHAT","label":"PPD BATU PAHAT"}])
            self.assertEqual(schools("https://db.example.invalid","TEST_KEY","Johor",
                                     "PPD BATU PAHAT")[0]["label"],
                             "SEKOLAH KEBANGSAAN LUBOK")
            self.assertEqual(school_by_code("https://db.example.invalid",
                                             "TEST_KEY","JBA0001"), self.school())
        self.assertEqual(calls[1][1]["state_name"],"eq.Johor")
        self.assertEqual(calls[2][1]["district_name"],"eq.PPD BATU PAHAT")
        self.assertEqual(calls[2][1]["school_level"],"eq.Rendah")
        self.assertEqual(calls[3][1]["school_code"],"eq.JBA0001")
        self.assertEqual(calls[3][1]["school_level"],"eq.Rendah")

    @patch("web.teacher_profile_routes._auth",
           return_value=(None,None,({"error":"Sila log masuk"},401)))
    def test_anonymous_cannot_enumerate_school_directory(self, *_):
        r=self.client.get("/api/web/teacher/school-directory?kind=states")
        self.assertEqual(r.status_code,401)

    @patch("web.teacher_profile_routes._auth",
           return_value=({"supabase_url":"https://db.example.invalid",
                          "supabase_key":"TEST"},123,None))
    def test_authenticated_directory_and_parameter_validation(self, *_):
        with patch("web.school_directory_store.states",
                   return_value=[{"value":"Johor","label":"Johor"}]) as lookup:
            r=self.client.get("/api/web/teacher/school-directory?kind=states")
            self.assertEqual(r.status_code,200)
            self.assertEqual(r.get_json()["items"][0]["label"],"Johor")
            self.assertEqual(r.get_json()["source_period"],"2022-06")
            self.assertNotIn("supabase_key",str(r.get_json()))
            lookup.assert_called_once()
        for params in (
            "kind=schools&state=Johor", "kind=states&state=Johor",
            "kind=states&kind=schools", "kind=districts",
            "kind=schools&state=Johor&district=PPD+A&uid=5",
        ):
            with self.subTest(params=params):
                self.assertEqual(self.client.get(
                    "/api/web/teacher/school-directory?"+params).status_code,400)

    def test_server_replaces_untrusted_full_name_with_database_name(self):
        captured = {}
        def write(url,key,table,uid,values,version,**kwargs):
            captured.update(values)
            return "2026-11-11T00:00:00+00:00"
        with patch("web.teacher_profile_store._profile_record",return_value=None), \
             patch("web.teacher_profile_store.school_by_code",create=True) as unused:
            # Resolver imported inside save_profile, so patch the real module.
            with patch("web.school_directory_store.school_by_code",
                       return_value=self.school()) as verified, \
                 patch("web.teacher_profile_store._save",side_effect=write):
                result=save_profile("https://db.example.invalid","TEST",123,self.form())
        self.assertTrue(result)
        self.assertEqual(captured["school_name"],"SEKOLAH KEBANGSAAN LUBOK")
        self.assertEqual(captured["school_code"],"JBA0001")
        self.assertEqual(captured["district_name"],"PPD BATU PAHAT")
        self.assertEqual(captured["class_profiles"][0]["name"],"4 Amanah")
        verified.assert_called_once()

    def test_saved_school_identity_does_not_require_directory_for_class_edit(self):
        old = {**self.school(), "telegram_user_id":123,
               "display_name":"Cikgu Ahmad",
               "updated_at":"2026-11-11T00:00:00+00:00",
               "class_profiles":[{"name":"4 Amanah","students":28,
                                  "timetable":[]}],
               "class_names":["4 Amanah"]}
        form=self.form(school_name=old["school_name"],
                       class_names=["4 Amanah","5 Amanah"],
                       version=old["updated_at"])
        with patch("web.teacher_profile_store._profile_record",return_value=old), \
             patch("web.school_directory_store.school_by_code") as directory, \
             patch("web.teacher_profile_store._save",return_value="saved") as save:
            self.assertEqual(save_profile("https://db.example.invalid","TEST",123,
                                          form),"saved")
            directory.assert_not_called()
            values=save.call_args.args[4]
            self.assertEqual(values["school_code"],"JBA0001")
            self.assertEqual(values["class_profiles"][0]["students"],28)
            self.assertEqual(values["class_profiles"][1]["name"],"5 Amanah")

    def test_school_code_cannot_be_attached_to_other_state_or_ppd(self):
        for changed in ({"state_name":"Kedah"},{"district_name":"PPD JOHOR BAHRU"}):
            with self.subTest(changed=changed), \
                 patch("web.teacher_profile_store._profile_record",return_value=None), \
                 patch("web.school_directory_store.school_by_code",
                       return_value=self.school()), \
                 patch("web.teacher_profile_store._save") as save:
                with self.assertRaises(ProfileValidation):
                    save_profile("https://db.example.invalid","TEST",123,
                                 self.form(**changed))
                save.assert_not_called()

    def test_legacy_school_name_is_never_silently_deleted(self):
        old={"telegram_user_id":123,"school_name":"SK Lama",
             "state_name":"Johor","updated_at":"2026-11-11T00:00:00+00:00",
             "class_profiles":[],"class_names":[],"school_code":None}
        form={"display_name":"Cikgu Ahmad","school_name":"SK Lama",
              "state_name":"Johor","class_names":[],
              "version":old["updated_at"]}
        with patch("web.teacher_profile_store._profile_record",
                   return_value=old), \
             patch("web.teacher_profile_store._save",
                   return_value="saved") as save:
            self.assertEqual(save_profile("https://db.example.invalid","TEST",123,
                                          form),"saved")
            values=save.call_args.args[4]
            self.assertEqual(values["school_name"],"SK Lama")
            self.assertNotIn("school_code",values)
            self.assertNotIn("district_name",values)
        with patch("web.teacher_profile_store._profile_record",
                   return_value=old), \
             patch("web.teacher_profile_store._save") as save:
            with self.assertRaises(ProfileValidation):
                save_profile("https://db.example.invalid","TEST",123,
                             {**form,"school_name":"Sekolah palsu",
                              "district_name":"","school_code":""})
            save.assert_not_called()

    def test_profile_get_reports_persistent_school_identity(self):
        record={"school_name":"SEKOLAH KEBANGSAAN LUBOK",
                "school_code":"JBA0001","district_name":"PPD BATU PAHAT",
                "state_name":"Johor","class_profiles":[],
                "class_names":[],"display_name":"Cikgu Ahmad","updated_at":"v"}
        with patch("web.teacher_profile_store._profile_record",return_value=record):
            data=get_profile("unused","unused",123)
        self.assertEqual(data["school_code"],"JBA0001")
        self.assertEqual(data["district_name"],"PPD BATU PAHAT")
        self.assertEqual(data["school_name"],"SEKOLAH KEBANGSAAN LUBOK")

    def test_browser_contains_full_name_picker_and_supabase_only(self):
        root=Path(__file__).resolve().parents[1]/"web_v1_static_preview"
        html=(root/"index.html").read_text("utf8")
        js=(root/"teacher-profile.js").read_text("utf8")
        for field in ("profile-state","profile-district","profile-school-choice",
                      "profile-school","profile-school-notice"):
            self.assertIn('id="'+field+'"',html)
        self.assertIn('name="school_name" type="text" maxlength="160"',html)
        self.assertIn("readonly",html)
        self.assertIn("/api/web/teacher/school-directory?",js)
        self.assertIn('school_code: document.getElementById("profile-school-choice").value',js)
        self.assertIn("schoolNameField.value=chosen?.label",js)
        self.assertIn('row.label+" ("+row.value+")"',js)
        self.assertNotIn("service_role",js)
        self.assertNotIn("supabase_key",js)


if __name__ == "__main__":
    unittest.main()
