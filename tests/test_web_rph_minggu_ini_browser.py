"""Exercise the weekly timetable controls and native RPH handoff in Chromium."""

from pathlib import Path
from unittest import TestCase
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
MONDAY = "2027-01-04"
TUESDAY = "2027-01-05"


def slot(day, code, subject, class_name):
    return {
        "day": day, "subject_code": code, "subject": subject, "class_name": class_name, "year": 2,
        "start": "08:00", "end": "09:00", "can_prepare": True, "component": None,
        "rpt_suggestion": {"week": 1, "group": "B", "lessons": {"": [1]}},
        "suggested_session": [1], "progress": {"": {"completed": None, "previous": None}},
    }


class WeeklyRphBrowserTest(TestCase):
    def test_week_uses_the_date_of_each_class_without_automatic_download(self):
        static = ROOT / "web_v1_static_preview"
        source = (static / "index.html").read_text(encoding="utf-8")
        start = source.index('<section id="view-today"')
        finish = source.index('<section id="view-rph"', start)
        markup = source[start:finish].replace("hidden>", ">", 1)
        script = (static / "rph-today.js").read_text(encoding="utf-8")
        fixture = """
          <script>
            window.readPbdRosterCount = async () => 32;
            window.showWebView = () => {};
            window.rphDownloadOptions = () => ({credentials:"same-origin"});
          </script>
          <script src="/rph-today.js"></script>
        """
        monday = slot("Isnin", "ENGLISH", "English", "2 Bestari")
        tuesday = slot("Selasa", "SCIENCE", "Sains", "2 Amanah")
        week_days = [
            {"date": MONDAY, "day": "Isnin", "entries": [monday]},
            {"date": TUESDAY, "day": "Selasa", "entries": [tuesday]},
            {"date": "2027-01-06", "day": "Rabu", "entries": [], "closure": "Cuti dalam takwim"},
        ]
        dropdown = {
            "subjects": [{"label": "English", "value": "ENGLISH"}, {"label": "Sains", "value": "SCIENCE"}],
            "units": [{"label": "Unit 1 Tajuk", "value": "U1"}],
            "pdp": [{"label": "Lesson 001 — English", "value": "L1"},
                    {"label": "PdP 002 — Sains", "value": "L2"}],
        }
        availability, downloads, errors = [], [], []

        def intercept(route):
            url = urlsplit(route.request.url)
            params = {key: values[0] for key, values in parse_qs(url.query).items()}
            if url.path == "/":
                route.fulfill(content_type="text/html", body='<!DOCTYPE html><meta charset="UTF-8">' + markup + fixture)
            elif url.path == "/rph-today.js":
                route.fulfill(content_type="application/javascript", body=script)
            elif url.path == "/api/web/rph/hari-ini":
                route.fulfill(json={"date": MONDAY, "day": "Isnin", "count": 1, "entries": [monday], "holiday_notice": ""})
            elif url.path == "/api/web/rph/minggu-ini":
                route.fulfill(json={"date": MONDAY, "start": MONDAY, "end": "2027-01-10",
                                    "count": 2, "days": week_days, "holiday_notice": "Sahkan PdP."})
            elif url.path == "/api/options":
                route.fulfill(json=dropdown[params["kind"]])
            elif url.path == "/api/web/rph/availability":
                availability.append(params)
                route.fulfill(json={"available": True, "generator": "telegram-native", "formats": ["pdf", "word"]})
            elif url.path == "/api/web/rph/extra-materials":
                route.fulfill(json={"items": []})
            elif url.path == "/api/web/rph/pdf":
                downloads.append(params)
                route.fulfill(content_type="application/pdf", body="%PDF-" + "x" * 1100)
            else:
                route.fulfill(status=404)

        with sync_playwright() as player:
            browser = player.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 430, "height": 890}, accept_downloads=True)
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route("https://week.test/**", intercept)
            page.goto("https://week.test/")
            page.evaluate("window.rphTodayLoad()")
            page.get_by_text("2 Bestari · English", exact=True).wait_for()
            self.assertEqual(page.locator("#view-today-heading").inner_text(), "RPH Pantas")
            page.get_by_role("button", name="RPH Minggu Ini", exact=True).click()
            page.get_by_text("Cuti dalam takwim", exact=True).wait_for()
            self.assertEqual(page.locator("#view-today-heading").inner_text(), "RPH Pantas")
            page.get_by_text("Cadangan slot ini: Lesson 001", exact=False).wait_for()
            for index, lesson in enumerate(("L1", "L2")):
                page.locator(f"#today-{index}-unit").select_option("U1")
                page.locator(f"#today-{index}-lesson").select_option(lesson)
            prepare = page.get_by_role("button", name="Sediakan RPH Minggu Ini")
            self.assertTrue(prepare.is_disabled())
            page.locator("#today-confirm-school-day").check()
            prepare.click()
            page.get_by_text("Semakan bahan selesai", exact=False).wait_for()
            self.assertFalse(downloads)
            english = next(row for row in availability if row["subject"] == "ENGLISH")
            self.assertEqual(english["teacher_date"], MONDAY)
            result = page.locator("#today-results-list .daily-rph-result-card").filter(has_text="2 Amanah")
            with page.expect_download():
                result.locator(".material-download-row").filter(has_text="RPH PDF").get_by_role("button", name="Download").click()
            self.assertEqual(len(downloads), 1)
            self.assertEqual((downloads[0]["teacher_class"], downloads[0]["teacher_date"], downloads[0]["teacher_start"]),
                             ("2 Amanah", TUESDAY, "08:00"))
            page.get_by_role("button", name="RPH Hari Ini", exact=True).click()
            page.locator("#today-list").get_by_text("2 Bestari · English", exact=True).wait_for()
            self.assertEqual(page.locator("#view-today-heading").inner_text(), "RPH Pantas")
            self.assertEqual(page.locator("#today-list .daily-rph-card").count(), 1)
            self.assertFalse(errors)
            browser.close()
