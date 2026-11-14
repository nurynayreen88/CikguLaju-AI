"""Prevent cross-user reads/writes and verify new profile/timetable editor."""
import unittest
from io import BytesIO
import os
from unittest.mock import patch
from flask import Flask

from web.teacher_profile_store import (
    ProfileValidation, ProfileConflict, clean_profile, clean_schedule,
    _endpoint,
)
from web.teacher_profile_routes import bp as teacher_profile_bp
from tools.run_web_production import app as production_web


def period(day="Isnin", start="07:30", end="08:30", cls="4 Bestari", subject="Matematik"):
    return {"day": day, "start": start, "end": end, "class_name": cls, "subject": subject}


def profile_form(**overrides):
    return {
        **{"display_name": "Cikgu Aminah", "school_name": "SK Mawar",
           "state_name": "Johor", "class_names": ["4 Bestari"], "version": ""},
        **overrides,
    }


class StoreValidatorTests(unittest.TestCase):
    def test_profile_cleans_pii_without_touching_access(self):
        clean,version=clean_profile(profile_form(display_name=" Cikgu Aminah "))
        self.assertEqual(clean["display_name"],"CIKGU AMINAH")
        self.assertEqual(clean["class_names"],["4 Bestari"])
        self.assertEqual(version,"")
        self.assertEqual(set(clean),{"display_name","school_name","state_name","class_names"})

    def test_teacher_name_is_uppercase_even_when_api_receives_lowercase(self):
        fields,_=clean_profile(profile_form(display_name="  siti nur binti ali  "))
        self.assertEqual(fields["display_name"],"SITI NUR BINTI ALI")
        fields,_=clean_profile(profile_form(display_name="Nurul 'Ain"))
        self.assertEqual(fields["display_name"],"NURUL 'AIN")

    def test_web_teacher_name_input_forces_capitals_on_typing_and_paste(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]/"web_v1_static_preview"
        html=(root/"index.html").read_text("utf8")
        js=(root/"teacher-profile.js").read_text("utf8")
        self.assertIn('id="profile-name"',html)
        self.assertIn('autocapitalize="characters"',html)
        self.assertIn('teacherNameField.addEventListener("input", uppercaseTeacherName)',js)
        self.assertIn('teacherNameField.value.trim().toLocaleUpperCase("ms-MY")',js)
        self.assertIn("setSelectionRange",js)

    def test_profile_rejects_extra_fields_or_duplicate_classes(self):
        for bad in (profile_form(telegram_user_id=123),profile_form(credits=99),
                    profile_form(class_names=["4 Bestari","4 bestari"]),
                    profile_form(class_names=["4 <script>"]),
                    profile_form(display_name=""),
                    profile_form(state_name="Kepala Batas")):
            with self.subTest(bad=bad),self.assertRaises(ProfileValidation):
                clean_profile(bad)

    def test_schedule_weekdays_and_no_overlap(self):
        schedule={"entries":[period(),period("Ahad","09:00","09:35","5 Amanah","Sains")],
                  "version":""}
        rows,_=clean_schedule(schedule,["4 Bestari","5 Amanah"])
        self.assertEqual(len(rows),2)
        for bad in (
            [period(day=["Isnin"])],
            [period(start="99:00")],
            [period(start="09:00",end="08:00")],
            [period(cls="Other Class")],
            [period(subject="<script>")],
            [period(),period(start="08:00",end="08:30")],
            [period(),period()],
        ):
            with self.subTest(bad=bad),self.assertRaises(ProfileValidation):
                clean_schedule({"entries":bad,"version":""},["4 Bestari"])

    def test_rejects_arbitrary_database_table(self):
        with self.assertRaises(Exception):
            _endpoint("https://test.supabase.co","payments",{"select":"*"})

    def test_version_required_and_timezone_aware(self):
        with self.assertRaises(ProfileValidation):
            clean_profile(profile_form(version="2026-11-05T10:00:00"))
        with self.assertRaises(ProfileValidation):
            clean_schedule({"entries":[],"version":"not-a-date"},[])


class TeacherProfileHttpTests(unittest.TestCase):
    def setUp(self):
        self.flask=Flask(__name__)
        self.flask.register_blueprint(teacher_profile_bp)
        self.client=self.flask.test_client()
        self.url="/api/web/teacher/profile"
        self.origin={"Origin":"https://cikgulaju-web.onrender.com"}
        self.base="https://cikgulaju-web.onrender.com"
        self.config={"CIKGULAJU_WEB_SESSION_SECRET":"x"*40,
                     "account_backend":"supabase",
                     "supabase_url":"https://unit.supabase.co",
                     "supabase_key":"server-test-key-never-public"}
        self.context=[
            patch("web.teacher_profile_routes._config",return_value=self.config),
            patch("web.teacher_profile_routes.verify_session_ticket",return_value=123),
            patch("web.teacher_profile_routes._lookup",return_value={"telegram_user_id":123}),
        ]
        for item in self.context:
            item.start()
            self.addCleanup(item.stop)

    def test_get_profile_uses_session_uid_never_client_uid(self):
        expected={"display_name":"Cikgu","school_name":"","class_names":[],"version":""}
        with patch("web.teacher_profile_routes.get_profile",return_value=expected) as profile, \
             patch("web.teacher_profile_routes.get_schedule",return_value={"entries":[],"version":""}) as schedule:
            res=self.client.get(self.url,base_url=self.base)
        self.assertEqual(res.status_code,200)
        profile.assert_called_once_with(self.config["supabase_url"],self.config["supabase_key"],123)
        schedule.assert_called_once_with(self.config["supabase_url"],self.config["supabase_key"],123)
        self.assertNotIn("server-test-key",res.get_data(as_text=True))
        self.assertEqual(res.headers["Cache-Control"],"no-store, private")
        self.assertEqual(res.headers["Vary"],"Cookie")

    def test_profile_write_same_origin_only(self):
        with patch("web.teacher_profile_routes.save_profile",return_value="2026-11-05T11:00:00+00:00") as save:
            bad=self.client.put(self.url,json=profile_form(),base_url=self.base,
                                headers={"Origin":"https://evil.example"})
            self.assertEqual(bad.status_code,400)
            save.assert_not_called()
            good=self.client.put(self.url,json=profile_form(),base_url=self.base,headers=self.origin)
            self.assertEqual(good.status_code,200,good.get_json())
            save.assert_called_once()
            self.assertEqual(save.call_args.args[2],123)

    def test_timetable_write_isolated_from_user_input(self):
        with patch("web.teacher_profile_routes.save_schedule",return_value="2026-11-05T11:00:00+00:00") as save:
            payload={"entries":[period()],"version":""}
            response=self.client.put("/api/web/teacher/timetable",json=payload,
                                     base_url=self.base,headers=self.origin)
            self.assertEqual(response.status_code,200)
            self.assertEqual(save.call_args.args[2],123)

    def test_ocr_preview_checks_paid_access_and_uses_saved_classes(self):
        url = "/api/web/teacher/timetable/read"
        data = b"%PDF-1.7 example"
        result = {"entries": [period()], "uncertain": 0, "unreadable_pages": 0}

        def upload(headers=None):
            return self.client.post(url, data={"timetable": (BytesIO(data), "jadual.pdf")},
                                    base_url=self.base, headers=headers or self.origin)

        with patch.dict(os.environ, {"CIKGULAJU_WEB_ADMIN_IDS": "555"}), \
             patch("web.teacher_profile_routes.get_profile", return_value={"class_names": ["4 Bestari"]}) as profile, \
             patch("web.timetable_reader_client.read_uploaded_timetable", return_value=result) as read, \
             patch("web.teacher_profile_routes.save_schedule") as save:
            with patch("web.teacher_profile_routes.verify_session_ticket", return_value=None):
                self.assertEqual(upload().status_code, 401)
            self.assertEqual(upload().status_code, 403)
            with patch("web.teacher_profile_routes._lookup", return_value={
                "telegram_user_id": 123, "authenticated": True, "rakan_pembangun": True,
            }):
                self.assertEqual(upload({"Origin": "https://evil.example"}).status_code, 400)
                read.assert_not_called()
                response = upload()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, result)
            self.assertEqual(response.headers["Cache-Control"], "no-store, private")
            profile.assert_called_once_with(self.config["supabase_url"], self.config["supabase_key"], 123)
            read.assert_called_once_with(data, ["4 Bestari"])
            save.assert_not_called()

    def test_anonymous_and_unregistered_blocked(self):
        with patch("web.teacher_profile_routes.verify_session_ticket",return_value=None):
            for method in ("get","put"):
                response=getattr(self.client,method)(self.url,base_url=self.base)
                self.assertEqual(response.status_code,401)
        with patch("web.teacher_profile_routes._lookup",return_value={"telegram_user_id":333}):
            self.assertEqual(self.client.get(self.url,base_url=self.base).status_code,403)

    def test_conflict_does_not_claim_success(self):
        with patch("web.teacher_profile_routes.save_profile",side_effect=ProfileConflict("changed")):
            res=self.client.put(self.url,json=profile_form(),base_url=self.base,headers=self.origin)
            self.assertEqual(res.status_code,409)
            self.assertNotIn("saved",res.get_json())

    def test_no_arbitrary_query_ids(self):
        res=self.client.get(self.url+"?telegram_user_id=999",base_url=self.base)
        self.assertEqual(res.status_code,400)

    def test_production_registers_private_routes_and_serves_editor(self):
        routes={rule.rule for rule in production_web.url_map.iter_rules()}
        self.assertIn(self.url,routes)
        self.assertIn("/api/web/teacher/timetable",routes)
        asset=production_web.test_client().get("/assets/teacher-profile.js")
        self.assertEqual(asset.status_code,200)
        self.assertIn("application/javascript",asset.content_type)
        self.assertNotIn("server-test-key",asset.get_data(as_text=True))


class WebTeacherProfileUiTests(unittest.TestCase):
    def test_profile_guide_uses_only_saved_data_and_does_not_block_rph(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]/"web_v1_static_preview"
        html=(root/"index.html").read_text("utf-8")
        js=(root/"teacher-profile.js").read_text("utf-8")
        self.assertIn('id="profile-setup-status"',html)
        self.assertIn('id="profile-setup-next"',html)
        self.assertIn("RPH biasa masih boleh dicuba",html)
        self.assertIn("function savedProfileReadiness()",js)
        self.assertIn("teacherProfileState.savedProfile",js)
        self.assertIn("teacherProfileState.savedPeriods>0",js)
        self.assertIn("teacherProfileState.loaded=true;",js)
        self.assertIn("renderProfileReadiness();",js)
        self.assertIn('profileSetupNext.addEventListener("click"',js)
        self.assertNotIn("fetch('/api/web/teacher/profile-readiness",js)
        self.assertNotIn("supabase_key",js)

    def test_profile_fields_and_schedule_editor_are_present(self):
        from pathlib import Path
        html=(Path(__file__).resolve().parents[1]/"web_v1_static_preview"/"index.html").read_text(encoding="utf-8")
        for ident in ("profile-name","profile-school","profile-state","profile-district","profile-school-choice","profile-classes",
                      "teacher-profile-form","timetable-rows","timetable-add",
                      "timetable-save","profile-save","profile-access-summary"):
            self.assertIn('id="'+ident+'"',html)
        self.assertRegex(html, r'src="/assets/teacher-profile\.js\?v=[a-z0-9-]+"')
        self.assertIn("loadTeacherProfile();",html)
        self.assertIn('id="view-rpt"',html)
        self.assertIn('id="view-rph"',html)


if __name__ == "__main__":
    unittest.main()
