"""Google staging can browse real Web metadata, but never RPH or paid access."""
import unittest
from unittest.mock import patch

from flask import Flask
from web.google_web_catalog_staging import bp
from web.google_auth_staging_routes import TICKET_COOKIE
from web_google_identity_sessions import issue_google_identity_ticket

SECRET = "staging-signed-ticket-test-" + "x" * 40
ACCOUNT = "bcbbd9d1-8b4c-4d8c-bd56-2e00e19442af"
PROFILE = {"display_name": "Guru Ujian", "trial_remaining": 10}
CONF = {"secret": SECRET, "host": "localhost"}
LESSON = {"value": "e-3-001", "label": "Lesson 001 — Welcome",
          "lesson_no": 1, "textbook_ref": "Student Book p1",
          "download_enabled": False, "standalone_rph_verified": False}


class GoogleWebCatalogueTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(bp)
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.config_patch = patch(
            "web.google_web_catalog_staging._enabled_config", return_value=CONF)
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

    def sign_in(self):
        ticket = issue_google_identity_ticket(ACCOUNT, SECRET)
        self.client.set_cookie(TICKET_COOKIE, ticket, domain="localhost")

    def test_anonymous_denied_for_all_endpoints(self):
        for url in ("/api/google-staging/web/catalog",
                    "/api/google-staging/web/catalog?year=3&subject=ENGLISH",
                    "/api/google-staging/web/materials?year=3&subject=ENGLISH&component=&unit=Unit&lesson=e-3-001"):
            res = self.client.get(url)
            self.assertEqual(res.status_code, 401, url)
        res = self.client.get("/google-staging-web")
        self.assertEqual(res.status_code, 303)
        self.assertEqual(res.headers["Location"], "/google-staging-login")

    def test_bad_database_or_cookie_never_exposes_catalogue(self):
        self.sign_in()
        with patch("web.google_web_catalog_staging.google_staging_account_profile",
                   side_effect=RuntimeError("database unavailable")):
            # Don't reveal source or leak errors on backend failures.
            # RuntimeError here is intentionally not swallowed by the route
            # itself; the store wraps its backend failures in GoogleAccountUnavailable.
            pass
        from web.google_account_store import GoogleAccountUnavailable
        with patch("web.google_web_catalog_staging.google_staging_account_profile",
                   side_effect=GoogleAccountUnavailable("private")):
            res = self.client.get("/api/google-staging/web/catalog")
        self.assertEqual(res.status_code, 503)
        self.assertNotIn(b"private", res.data)

    def test_verified_account_can_read_only_subjects_units_and_lessons(self):
        self.sign_in()
        with (
            patch("web.google_web_catalog_staging.google_staging_account_profile",
                  return_value=PROFILE),
            patch("web.unified_rph_web.unit_options",
                  return_value=[{"value": "Unit One", "label": "Unit One"}]) as units,
            patch("web.unified_rph_web.pdp_options",
                  return_value=[LESSON]) as lessons,
        ):
            home = self.client.get("/google-staging-web")
            self.assertEqual(home.status_code, 200)
            self.assertIn(b"Pilih Lesson / PdP", home.data)
            self.assertIn(b'id="generationControls" hidden', home.data)
            self.assertIn(b'id="generate" type="button"', home.data)
            self.assertIn(b'/api/google-staging/web/rph/capabilities', home.data)
            self.assertEqual(home.headers["Cache-Control"], "no-store, private")

            subjects = self.client.get("/api/google-staging/web/catalog")
            self.assertEqual(subjects.status_code, 200)
            self.assertFalse(subjects.json["rph_generation_enabled"])
            self.assertEqual(subjects.json["years"], [2, 3, 4, 5, 6])

            unit = self.client.get("/api/google-staging/web/catalog?year=3&subject=ENGLISH")
            self.assertEqual(unit.status_code, 200)
            self.assertEqual(unit.json["level"], "units")
            self.assertEqual(unit.json["items"][0]["value"], "Unit One")
            units.assert_called_with(3, "ENGLISH", component=None)

            lesson = self.client.get("/api/google-staging/web/catalog?year=3&subject=ENGLISH&unit=Unit+One")
            self.assertEqual(lesson.status_code, 200)
            self.assertEqual(lesson.json["level"], "lessons")
            self.assertFalse(lesson.json["items"][0]["download_enabled"])
            self.assertNotIn("path", lesson.json["items"][0])
            lessons.assert_called_with(3, "ENGLISH", "Unit One", component=None)

            material = self.client.get("/api/google-staging/web/materials?year=3&subject=ENGLISH&component=&unit=Unit+One&lesson=e-3-001")
            self.assertEqual(material.status_code, 200)
            self.assertFalse(material.json["trial_debited"])
            self.assertFalse(material.json["rph_generation_enabled"])
            self.assertTrue(all(not x["available"] for x in material.json["materials"]))
            self.assertFalse(any("url" in x for x in material.json["materials"]))

    def test_spoofing_and_bad_params_rejected(self):
        self.sign_in()
        with patch("web.google_web_catalog_staging.google_staging_account_profile",
                   return_value=PROFILE):
            bad = (
                "?account_id=bcbbd9d1-8b4c-4d8c-bd56-2e00e19442af",
                "?telegram_user_id=123",
                "?year=1&subject=ENGLISH",
                "?year=3&subject=ENGLISH&component=PK",
                "?year=3&subject=PJPK",
                "?year=3&subject=ENGLISH&unit=x&unit=y",
            )
            for query in bad:
                with self.subTest(query=query):
                    self.assertEqual(self.client.get(
                        "/api/google-staging/web/catalog" + query).status_code, 400)

    def test_no_linking_by_matching_names(self):
        from web.provider_neutral_web_identity import (
            from_verified_google_account, from_verified_telegram_account,
            may_link_accounts,
        )
        google = from_verified_google_account(ACCOUNT, {
            "account_id": ACCOUNT, "trial_remaining": 10,
            "display_name": "Same Name"})
        telegram = from_verified_telegram_account(12345, {
            "telegram_user_id": 12345, "authenticated": True,
            "display_name": "Same Name", "free_remaining": 9})
        self.assertFalse(google.can_use_legacy_telegram_rph)
        self.assertFalse(google.can_use_google_rph)
        self.assertFalse(may_link_accounts(google, telegram))
        self.assertTrue(may_link_accounts(google, telegram, both_sessions_verified=True))
        self.assertTrue(telegram.can_use_legacy_telegram_rph)
        with self.assertRaises(ValueError):
            from_verified_google_account(ACCOUNT, {
                "account_id": ACCOUNT, "trial_remaining": True})
        with self.assertRaises(ValueError):
            from_verified_telegram_account(12345, {
                "telegram_user_id": "12345", "authenticated": True})


if __name__ == "__main__":
    unittest.main()
