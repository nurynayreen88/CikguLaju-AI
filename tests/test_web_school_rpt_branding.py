"""Regression tests: school logo safety, authenticated upload, RPT source preservation."""
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from flask import Flask
from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas

from web.rpt_school_cover import personalized_pdf, for_download
from web.school_logo_store import normalized_png, logo_png, profile_logo_png, save_logo_png
from web.teacher_profile_store import ProfileValidation
from web.teacher_profile_routes import bp


def sample_logo():
    buff = BytesIO()
    Image.new("RGBA", (240, 240), (12, 118, 102, 120)).save(buff, format="PNG")
    return buff.getvalue()


class Response:
    def __init__(self, data=b"", status=200):
        self.data = data
        self.status = status
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, limit=-1):
        return self.data[:limit] if limit >= 0 else self.data


class MemoryStorage:
    def __init__(self):
        self.objects = {}
        self.requests = []
    @property
    def content(self):
        return next(iter(self.objects.values()), None)
    def open(self, request, timeout=10):
        from urllib.error import HTTPError
        self.requests.append(request)
        path = request.full_url.replace("/object/authenticated/", "/object/")
        if request.get_method() == "POST":
            if request.get_header("X-upsert") == "false" and path in self.objects:
                raise HTTPError(request.full_url, 409, "already exists", {}, None)
            self.objects[path] = request.data
            return Response(b'{"Key":"private"}', status=200)
        if path not in self.objects:
            raise HTTPError(request.full_url, 404, "no logo", {}, None)
        return Response(self.objects[path])


class SchoolLogoTests(unittest.TestCase):
    def test_normalized_png_is_safe_and_strips_original_metadata(self):
        normalized = normalized_png(sample_logo())
        self.assertTrue(normalized.startswith(b"\x89PNG\r\n\x1a\n"))
        with Image.open(BytesIO(normalized)) as check:
            self.assertLessEqual(check.width, 512)
            self.assertEqual(check.format, "PNG")
        for unsafe in (b"<svg><script>bad</script></svg>", b"", b"not a real image"):
            with self.assertRaises(ProfileValidation):
                normalized_png(unsafe)
        with self.assertRaises(ProfileValidation):
            normalized_png(b"a" * (2 * 1024 * 1024 + 1))

    def test_private_storage_path_scoped_to_server_authenticated_user(self):
        store = MemoryStorage()
        self.assertIsNone(logo_png("https://school.supabase.co", "private-server-key", 812, opener=store))
        count = save_logo_png("https://school.supabase.co", "private-server-key",
                              812, sample_logo(), opener=store)
        self.assertGreater(count, 100)
        data = logo_png("https://school.supabase.co", "private-server-key",
                        812, opener=store)
        self.assertEqual(data, store.content)
        self.assertTrue(all("/cikgulaju-materials/school-logos/812/logo.png"
                            in req.full_url for req in store.requests))
        self.assertEqual(store.requests[1].get_method(), "POST")
        self.assertIn("/storage/v1/object/authenticated/cikgulaju-materials/",
                      store.requests[0].full_url)
        self.assertIn("/storage/v1/object/authenticated/cikgulaju-materials/",
                      store.requests[2].full_url)
        self.assertIn("/storage/v1/object/cikgulaju-materials/",
                      store.requests[1].full_url)
        self.assertNotIn("/object/authenticated/", store.requests[1].full_url)

    def test_switching_schools_keeps_logos_separate_and_auto_import_preserves_manual_upload(self):
        store = MemoryStorage()
        args = ("https://school.supabase.co", "private-server-key", 812)
        old_logo = normalized_png(sample_logo())
        buffer = BytesIO()
        Image.new("RGB", (64, 64), (255, 120, 120)).save(buffer, format="PNG")
        new_logo = normalized_png(buffer.getvalue())
        save_logo_png(*args, old_logo, opener=store)
        self.assertIsNone(profile_logo_png(*args, "KBA4016", "KBA4015", opener=store))
        self.assertEqual(profile_logo_png(*args, "KBA4015", "KBA4015", opener=store), old_logo)
        save_logo_png(*args, new_logo, school_code="KBA4016", opener=store)
        save_logo_png(*args, old_logo, school_code="KBA4016", automatic=True, opener=store)
        self.assertEqual(profile_logo_png(*args, "KBA4016", "KBA4015", opener=store), new_logo)
        self.assertEqual(profile_logo_png(*args, "KBA4015", "KBA4015", opener=store), old_logo)
        self.assertIsNone(profile_logo_png(*args, "KBA4017", "KBA4015", opener=store))
        self.assertTrue(any("/school-logos/812/KBA4016/logo.png" in request.full_url
                            for request in store.requests if request.get_method() == "POST"))

    def test_upload_does_not_accept_untrusted_origin_or_anonymous(self):
        app = Flask(__name__)
        app.register_blueprint(bp)
        client = app.test_client()
        with patch("web.teacher_profile_routes._auth", return_value=(
            {"supabase_url": "https://school.supabase.co",
             "supabase_key": "private-server-key"}, 812, None)):
            bad = client.post("/api/web/teacher/school-logo",
                              data={"logo": (BytesIO(sample_logo()), "logo.png")})
            self.assertEqual(bad.status_code, 400)
            with patch("web.teacher_profile_routes.get_profile",
                       return_value={"school_code": "KBA4016"}), \
                 patch("web.school_logo_store.save_logo_png", return_value=400) as save:
                correct = client.post("/api/web/teacher/school-logo",
                    data={"logo": (BytesIO(sample_logo()), "logo.png"),
                          "school_code": "KBA4016", "automatic": "1"},
                    headers={"Origin": "https://localhost"})
                self.assertEqual(correct.status_code, 200)
                self.assertTrue(correct.json["saved"])
                self.assertEqual(save.call_args.args[2], 812)
                self.assertEqual(save.call_args.kwargs, {"school_code": "KBA4016", "automatic": True})
                stale = client.post("/api/web/teacher/school-logo",
                    data={"logo": (BytesIO(sample_logo()), "logo.png"), "school_code": "KBA4015"},
                    headers={"Origin": "https://localhost"})
                self.assertEqual(stale.status_code, 409)
                self.assertEqual(save.call_count, 1)
        with patch("web.teacher_profile_routes._auth", return_value=(
            None, None, ({"error": "login"}, 401))):
            self.assertEqual(client.get("/api/web/teacher/school-logo").status_code, 401)


class MissingOptionalLogoRegressionTests(unittest.TestCase):
    """Missing optional logo is not a school-cover or RPT download failure."""

    @staticmethod
    def failure_open(code, payload):
        from urllib.error import HTTPError

        class Response:
            def open(self, request, timeout=8):
                raise HTTPError(
                    request.full_url, code, "Storage object missing", {},
                    BytesIO(payload)
                )
        return Response()

    def test_400_missing_object_not_found_is_optional(self):
        missing_versions=[
            b'{"statusCode":"404","error":"not_found","message":"Object not found"}',
            b'{"statusCode":"400","errorCode":"NoSuchKey","message":"Object not found"}',
        ]
        for payload in missing_versions:
            with self.subTest(payload=payload):
                self.assertIsNone(
                    logo_png("https://school.supabase.co", "private-server-key",812,
                             opener=self.failure_open(400,payload))
                )

    def test_bad_credentials_permissions_and_missing_bucket_stay_errors(self):
        from web.teacher_profile_store import ProfileUnavailable
        for code,payload in (
            (403,b'{"error":"unauthorized","message":"Not allowed"}'),
            (400,b'{"error":"not_found","message":"Bucket not found"}'),
            (400,b'{"error":"unauthorized","message":"Object not found"}'),
            (400,b'not json'),
        ):
            with self.subTest(code=code,payload=payload):
                with self.assertRaises(ProfileUnavailable):
                    logo_png("https://school.supabase.co","private-server-key",812,
                             opener=self.failure_open(code,payload))

    def test_school_identity_without_uploaded_logo_still_builds_personalized_pdf(self):
        from web.rpt_school_cover import school_identity, for_download
        from tempfile import TemporaryDirectory
        with patch("web.rpt_school_cover._get_one",return_value={
                "telegram_user_id":812,"school_name":"SK Taman Jaya",
                "display_name":"Cikgu Ali","state_name":"Johor"}), \
             patch("web.rpt_school_cover.profile_logo_png",return_value=None):
            identity=school_identity({"supabase_url":"https://school.supabase.co",
                                      "supabase_key":"private-key"},812)
        self.assertEqual(identity["school"],"SK Taman Jaya")
        self.assertIsNone(identity["logo"])
        with TemporaryDirectory() as tmp:
            pdf=Path(tmp)/"RPT.pdf"
            pdf.write_bytes(b"%PDF-"+b"x"*9000)
            with patch("web_v1_telegram_auth_routes._config",return_value={
                    "supabase_url":"https://school.supabase.co",
                    "supabase_key":"private-key","account_backend":"supabase"}), \
                 patch("web.rpt_school_cover.school_identity",return_value=identity), \
                 patch("web.rpt_school_cover.request_telegram_school_rpt",
                       return_value=BytesIO(b"%PDF-"+b"y"*9000)) as call:
                result=for_download({"telegram_user_id":812},pdf,"pjpk",2)
                self.assertTrue(result.getvalue().startswith(b"%PDF-"))
                self.assertEqual(call.call_args.args[0],pdf)
                self.assertEqual(call.call_args.args[3]["school"],"SK Taman Jaya")


class RptSchoolSheetTests(unittest.TestCase):
    def test_original_rpt_pages_and_file_are_preserved(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "RPT_2027.pdf"
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=(842, 595))
            c.drawString(30, 520, "ASAL MUKA DEPAN")
            c.showPage()
            c.drawString(30, 520, "RPH TIDAK DIUBAH")
            c.showPage()
            c.save()
            original = buffer.getvalue()
            path.write_bytes(original)
            result = personalized_pdf(path, "Bahasa Melayu", 2027,
                {"school": "SK Taman Jaya", "state": "Johor",
                 "teacher": "Cikgu Ali", "logo": normalized_png(sample_logo())})
            pages = PdfReader(result).pages
            self.assertEqual(len(pages), 3)
            first = pages[0].extract_text()
            self.assertIn("SK Taman Jaya", first)
            self.assertIn("Bahasa Melayu", first)
            self.assertIn("Johor", first)
            self.assertIn("Cikgu Ali", first)
            self.assertIn("ASAL MUKA DEPAN", pages[1].extract_text())
            self.assertIn("RPH TIDAK DIUBAH", pages[2].extract_text())
            self.assertEqual(path.read_bytes(), original)
            self.assertAlmostEqual(float(pages[0].mediabox.width), 842)

    def test_unknown_profile_keeps_original_rpt(self):
        path = Path("/unrelated.pdf")
        self.assertEqual(for_download({}, path, "English", 2027), path)
        self.assertEqual(for_download({"telegram_user_id": "bad"}, path, "English", 2027), path)

    def test_interface_has_upload_preview_and_teacher_fallback(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "web_v1_static_preview/index.html").read_text("utf-8")
        js = (root / "web_v1_static_preview/teacher-profile.js").read_text("utf-8")
        self.assertIn('id="sidebar-teacher-name">Cikgu', html)
        self.assertIn('id="school-logo-file"', html)
        self.assertIn('id="school-logo-upload"', html)
        self.assertIn('id="workspace-teacher-name">Cikgu', html)
        self.assertIn('setTeacherIdentity({...profile,school_name:schoolNameField.value});', js)
        self.assertIn('setTeacherIdentity(body);', js)
        self.assertIn('/api/web/teacher/school-logo', js)


if __name__ == "__main__":
    unittest.main()
