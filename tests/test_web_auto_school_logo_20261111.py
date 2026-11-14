"""School-code-scoped auto logo: no real download, credit change or user write.

Uses mocks for the protected Supabase registry, upstream image stream and
existing private Storage upload. Verifies that the UI never accepts a random
URL and that an unrelated user cannot select another account's school.
"""
import unittest
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

from flask import Flask
from web.teacher_profile_routes import bp
from web.school_logo_candidate import (
    logo_candidate, LogoSourceUnavailable, UPSTREAM_COMMIT,
    UPSTREAM_ROOT, MAX_SOURCE_BYTES,
)


class FakeResponse:
    def __init__(self, content, content_type="image/jpeg", status=200):
        self.status=status
        self.content=content
        self.headers={"Content-Length":str(len(content)),
                      "Content-Type":content_type}
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False
    def read(self, max_size):
        return self.content[:max_size]


class FakeOpener:
    def __init__(self, content, *, missing_catalog=False):
        self.requests=[]
        self.missing_catalog=missing_catalog
        self.content=content
    def open(self, request, timeout=9):
        self.requests.append(request.full_url)
        if self.missing_catalog and "/school-logo-catalog/" in request.full_url:
            raise HTTPError(request.full_url,404,"missing",{},None)
        return FakeResponse(self.content)


class AutoLogoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app=Flask(__name__)
        app.register_blueprint(bp)
        cls.client=app.test_client()

    def test_exact_school_code_fetches_pinned_govtech_image(self):
        data=b"\xff\xd8\xff"+b"rest-of-jpeg"
        opener=FakeOpener(data, missing_catalog=True)
        with patch("web.school_logo_candidate.school_by_code",
                   return_value={"school_code":"JBA0001","school_level":"Rendah"}), \
             patch("web.school_logo_candidate._read",return_value=[{
                 "school_code":"JBA0001","image_extension":"jpg",
                 "source_commit":UPSTREAM_COMMIT
             }]) as registry:
            found=logo_candidate("https://example.supabase.co","fake", "JBA0001",opener=opener)
        self.assertEqual(found,(data,"image/jpeg"))
        self.assertEqual(opener.requests,[
            "https://example.supabase.co/storage/v1/object/authenticated/cikgulaju-materials/"
            f"school-logo-catalog/{UPSTREAM_COMMIT}/JBA0001.jpg",
            UPSTREAM_ROOT+"JBA0001.jpg",
        ])
        self.assertEqual(registry.call_args.args[2],"school_logo_sources")
        self.assertEqual(registry.call_args.args[3]["school_code"],"eq.JBA0001")

    def test_stored_catalog_image_does_not_use_external_host(self):
        data=b"\xff\xd8\xff"+b"rest-of-jpeg"
        opener=FakeOpener(data)
        with patch("web.school_logo_candidate.school_by_code",
                   return_value={"school_level":"Rendah"}), \
             patch("web.school_logo_candidate._read",return_value=[{
                "school_code":"JBA0001","image_extension":"jpg","source_commit":UPSTREAM_COMMIT,
             }]):
            found=logo_candidate("https://db.example","fake","JBA0001",opener=opener)
        self.assertEqual(found,(data,"image/jpeg"))
        self.assertEqual(len(opener.requests),1)
        self.assertIn("/school-logo-catalog/",opener.requests[0])

    def test_no_candidate_does_not_make_external_request(self):
        opener=FakeOpener(b"")
        with patch("web.school_logo_candidate.school_by_code",
                   return_value={"school_level":"Rendah"}), \
             patch("web.school_logo_candidate._read",return_value=[]):
            self.assertIsNone(logo_candidate("https://db.example","fake",
                                              "JBA0001",opener=opener))
        self.assertEqual(opener.requests,[])

    def test_non_primary_school_never_fetches_logo(self):
        opener=FakeOpener(b"")
        with patch("web.school_logo_candidate.school_by_code",
                   return_value={"school_level":"Menengah"}), \
             patch("web.school_logo_candidate._read") as registry:
            self.assertIsNone(logo_candidate("https://db.example","fake",
                                              "JEA0001",opener=opener))
            registry.assert_not_called()
        self.assertEqual(opener.requests,[])

    def test_unapproved_image_response_rejected(self):
        opener=FakeOpener(b"<html>this is not a logo</html>")
        with patch("web.school_logo_candidate.school_by_code",
                   return_value={"school_level":"Rendah"}), \
             patch("web.school_logo_candidate._read",return_value=[{
                 "school_code":"JBA0001","image_extension":"jpg",
                 "source_commit":UPSTREAM_COMMIT
             }]):
            with self.assertRaises(LogoSourceUnavailable):
                logo_candidate("https://db.example","fake","JBA0001",opener=opener)

    def test_wrong_commit_does_not_fetch(self):
        opener=FakeOpener(b"")
        with patch("web.school_logo_candidate.school_by_code",
                   return_value={"school_level":"Rendah"}), \
             patch("web.school_logo_candidate._read",return_value=[{
                 "school_code":"JBA0001","image_extension":"jpg",
                 "source_commit":"0"*40
             }]):
            with self.assertRaises(LogoSourceUnavailable):
                logo_candidate("https://db.example","fake","JBA0001",opener=opener)
        self.assertEqual(opener.requests,[])

    @patch("web.teacher_profile_routes._auth",
           return_value=(None,None,({"error":"Sila log masuk"},401)))
    def test_unauthenticated_user_denied(self, *_):
        r=self.client.get("/api/web/teacher/school-logo-candidate")
        self.assertEqual(r.status_code,401)

    @patch("web.teacher_profile_routes._auth",
           return_value=({"supabase_url":"https://db.example",
                          "supabase_key":"private"},123,None))
    def test_authenticated_route_uses_saved_school_only(self, *_):
        with patch("web.teacher_profile_routes.get_profile",
                   return_value={"school_code":"JBA0001"}) as profile, \
             patch("web.school_logo_candidate.logo_candidate",
                   return_value=(b"\xff\xd8\xffjpg","image/jpeg")) as fetch:
            r=self.client.get("/api/web/teacher/school-logo-candidate")
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.content_type,"image/jpeg")
        self.assertEqual(r.data,b"\xff\xd8\xffjpg")
        self.assertEqual(r.headers["Cache-Control"],"no-store, private")
        self.assertEqual(profile.call_args.args[-1],123)
        self.assertEqual(fetch.call_args.args[-1],"JBA0001")
        self.assertEqual(
            self.client.get("/api/web/teacher/school-logo-candidate?school_code=JBA0002").status_code,
            400,
        )

    @patch("web.teacher_profile_routes._auth",
           return_value=({"supabase_url":"https://db.example",
                          "supabase_key":"private"},123,None))
    def test_unlinked_teacher_does_not_trigger_source_lookup(self, *_):
        with patch("web.teacher_profile_routes.get_profile",
                   return_value={"school_code":""}), \
             patch("web.school_logo_candidate.logo_candidate",
                   return_value=None) as fetch:
            r=self.client.get("/api/web/teacher/school-logo-candidate")
        self.assertEqual(r.status_code,404)
        fetch.assert_called_once()

    def test_frontend_does_not_overwrite_logo_without_consent(self):
        root=Path(__file__).resolve().parents[1]/"web_v1_static_preview"
        html=(root/"index.html").read_text("utf-8")
        js=(root/"teacher-profile.js").read_text("utf-8")
        self.assertIn('id="school-logo-auto"',html)
        self.assertIn('src="/assets/teacher-profile.js?v=school-search-20261114"',html)
        self.assertIn("/api/web/teacher/school-logo-candidate",js)
        self.assertIn("savedLogoSchoolCode()",js)
        self.assertIn("schoolLogoPresent===true",js)
        self.assertIn("window.confirm",js)
        self.assertIn("schoolLogoPresent!==false",js)
        self.assertIn("saveCandidateLogoToPrivateStorage",js)
        self.assertNotIn("raw.githubusercontent.com",js)
        self.assertNotIn("supabase_key",js)


if __name__=="__main__":
    unittest.main()
