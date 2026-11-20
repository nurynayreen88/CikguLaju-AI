"""Exercise the weekly timetable controls and native RPH handoff in Chromium."""

from email import policy
from email.parser import BytesParser
from pathlib import Path
from unittest import TestCase
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
MONDAY = "2027-01-04"
TUESDAY = "2027-01-05"
HOLIDAY = "2027-01-06"
THURSDAY = "2027-01-07"
NEXT_MONDAY = "2027-01-11"
CLOSURE = "Cuti negeri · Israk dan Mikraj"


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
            window.refreshSharedRphBalance = async () => ({rph_access_mode:"paid"});
            window.canGenerateRph = () => true;
            window.updateRphTrialFromDenial = () => false;
          </script>
          <script src="/pdf-lib.min.js"></script>
          <script src="/rph-today.js"></script>
        """
        monday = slot("Isnin", "ENGLISH", "English", "2 Bestari")
        monday["rpt_suggestion"]["lessons"][""] = [1, 2, 3, 4]
        tuesday = slot("Selasa", "SCIENCE", "Sains", "2 Amanah")
        thursday = slot("Khamis", "SCIENCE", "Sains", "2 Cemerlang")
        week_days = [
            {"date": MONDAY, "day": "Isnin", "entries": [monday]},
            {"date": TUESDAY, "day": "Selasa", "entries": [tuesday]},
            {"date": HOLIDAY, "day": "Rabu", "entries": [], "closure": CLOSURE},
            {"date": THURSDAY, "day": "Khamis", "entries": [thursday]},
        ]
        dropdown = {
            "subjects": [{"label": "English", "value": "ENGLISH"}, {"label": "Sains", "value": "SCIENCE"}],
            "units": [{"label": "Unit 1 Tajuk", "value": "U1"}],
            "pdp": [{"label": "Lesson 001 — English", "value": "L1"},
                    {"label": "PdP 002 — Sains", "value": "L2"}],
        }
        availability, downloads, errors = [], [], []
        pdf_parts = {}
        bundles = []
        fail_tuesday = False
        combined_pdf = b""
        weeks = [
            {"start": MONDAY, "end": "2027-01-10", "value": MONDAY, "current": True},
            {"start": NEXT_MONDAY, "end": "2027-01-17", "value": NEXT_MONDAY, "current": False},
        ]

        def intercept(route):
            url = urlsplit(route.request.url)
            params = {key: values[0] for key, values in parse_qs(url.query).items()}
            if url.path == "/":
                route.fulfill(content_type="text/html", body='<!DOCTYPE html><meta charset="UTF-8">' + markup + fixture)
            elif url.path == "/rph-today.js":
                route.fulfill(content_type="application/javascript", body=script)
            elif url.path == "/pdf-lib.min.js":
                route.fulfill(content_type="application/javascript", body=(static / "pdf-lib.min.js").read_bytes())
            elif url.path == "/api/web/rph/hari-ini":
                if params.get("date") == HOLIDAY:
                    route.fulfill(json={"date": HOLIDAY, "day": "Rabu", "count": 1, "entries": [monday],
                                        "closure": CLOSURE, "holiday_notice": ""})
                elif params.get("date") == THURSDAY:
                    route.fulfill(json={"date": THURSDAY, "day": "Khamis", "count": 1,
                                        "entries": [thursday], "holiday_notice": ""})
                else:
                    route.fulfill(json={"date": MONDAY, "day": "Isnin", "count": 1,
                                        "entries": [monday], "holiday_notice": ""})
            elif url.path == "/api/web/rph/minggu-ini":
                chosen = params.get("date", MONDAY)
                showing_next = chosen == NEXT_MONDAY
                route.fulfill(json={"date": chosen, "start": chosen,
                                    "end": weeks[showing_next]["end"], "weeks": weeks,
                                    "count": 0 if showing_next else 3,
                                    "days": [] if showing_next else week_days, "holiday_notice": "Sahkan PdP."})
            elif url.path == "/api/options":
                route.fulfill(json=dropdown[params["kind"]])
            elif url.path == "/api/web/rph/availability":
                availability.append(params)
                route.fulfill(json={"available": True, "generator": "telegram-native", "formats": ["pdf", "word"]})
            elif url.path == "/api/web/rph/extra-materials":
                route.fulfill(json={"items": []})
            elif url.path == "/api/web/rph/pdf":
                nonlocal fail_tuesday
                downloads.append(params)
                if fail_tuesday and params["teacher_date"] == TUESDAY:
                    fail_tuesday = False
                    return route.fulfill(status=503, json={"error": "Ujian slot tergendala"})
                route.fulfill(content_type="application/pdf", body=pdf_parts[params["teacher_date"]],
                              headers={"X-RPH-PDF-Receipt": params["teacher_date"]})
            elif url.path == "/api/web/rph/timetable/pdf-bundle":
                if route.request.method == "GET":
                    route.fulfill(json={"access_mode": "subscription", "available": len(bundles) < 2,
                                        "remaining": 2 - len(bundles), "usage_week_start": MONDAY,
                                        "usage_week_end": "2027-01-10"})
                    return
                headers = route.request.headers
                message = BytesParser(policy=policy.default).parsebytes(
                    ("Content-Type: " + headers["content-type"] + "\r\n\r\n").encode()
                    + route.request.post_data_buffer
                )
                receipt_values = [part.get_content() for part in message.iter_parts()
                                  if part.get_param("name", header="content-disposition") == "receipt"]
                self.assertEqual(receipt_values, [MONDAY, TUESDAY])
                bundles.append(headers["x-rph-weekly-export"])
                route.fulfill(content_type="application/pdf", body=combined_pdf, headers={
                    "X-RPH-Weekly-Remaining": str(2 - len(bundles)),
                    "X-RPH-Weekly-Start": MONDAY, "X-RPH-Weekly-End": "2027-01-10",
                })
            else:
                route.fulfill(status=404)

        with sync_playwright() as player:
            browser = player.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 430, "height": 890}, accept_downloads=True)
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route("https://week.test/**", intercept)
            page.goto("https://week.test/")
            for day, width in ((MONDAY, 595), (TUESDAY, 600)):
                raw = page.evaluate("""async width => {
                    const pdf = await PDFLib.PDFDocument.create();
                    pdf.addPage([width,842]);
                    return Array.from(await pdf.save());
                }""", width)
                pdf_parts[day] = bytes(raw) + b" " * 1200
            combined_pdf = bytes(page.evaluate("""async () => {
                const pdf = await PDFLib.PDFDocument.create();
                pdf.addPage([595,842]);
                pdf.addPage([600,842]);
                return Array.from(await pdf.save());
            }""")) + b" " * 1200
            page.evaluate("window.rphTodayLoad()")
            page.get_by_text("2 Bestari · English", exact=True).wait_for()
            self.assertEqual(page.locator("#view-today-heading").inner_text(), "RPH Pantas")
            page.get_by_text("Cadangan slot ini: Lesson 001.", exact=True).wait_for()
            self.assertEqual(page.get_by_text("Cadangan RPT · Minggu", exact=False).count(), 0)
            page.get_by_role("button", name="RPH Minggu Ini", exact=True).click()
            week_select = page.get_by_label("Pilih minggu", exact=True)
            expect(week_select).to_have_value(MONDAY)
            self.assertIn("Jan", week_select.locator("option").first.inner_text())
            week_select.select_option(NEXT_MONDAY)
            page.get_by_text("Tiada waktu PdP minggu ini.", exact=False).wait_for()
            week_select.select_option(MONDAY)
            page.get_by_text(CLOSURE, exact=True).wait_for()
            self.assertEqual(page.locator("#view-today-heading").inner_text(), "RPH Pantas")
            page.get_by_text("Cadangan slot ini: Lesson 001", exact=False).wait_for()
            for index, lesson in enumerate(("L1", "L2", "L2")):
                page.locator(f"#today-{index}-unit").select_option("U1")
                page.locator(f"#today-{index}-lesson").select_option(lesson)
            prepare = page.get_by_role("button", name="Sediakan RPH Minggu Ini")
            self.assertTrue(prepare.is_disabled())
            confirm = page.locator("#today-confirm-school-day")
            confirm.check()
            excluded = page.get_by_role("checkbox", name="Tiada PdP pada Khamis", exact=False)
            excluded.check()
            self.assertFalse(confirm.is_checked())
            self.assertTrue(prepare.is_disabled())
            self.assertFalse(page.locator("#today-2-lesson").is_visible())
            expect(page.locator("#today-status")).to_contain_text("2 slot PdP.")
            self.assertFalse(page.get_by_role("checkbox", name="Tiada PdP pada Rabu", exact=False).count())
            confirm.check()
            prepare.click()
            page.get_by_text("Semakan bahan selesai", exact=False).wait_for()
            self.assertFalse(downloads)
            self.assertEqual(sorted(row["subject"] for row in availability), ["ENGLISH", "SCIENCE"])
            self.assertFalse(page.locator("#today-results-list").get_by_text("2 Cemerlang · Sains", exact=True).count())
            english = next(row for row in availability if row["subject"] == "ENGLISH")
            self.assertEqual(english["teacher_date"], MONDAY)
            result = page.locator("#today-results-list .daily-rph-result-card").filter(has_text="2 Amanah")
            with page.expect_download():
                result.locator(".material-download-row").filter(has_text="RPH PDF").get_by_role("button", name="Download").click()
            self.assertEqual(len(downloads), 1)
            self.assertEqual((downloads[0]["teacher_class"], downloads[0]["teacher_date"], downloads[0]["teacher_start"]),
                             ("2 Amanah", TUESDAY, "08:00"))
            downloads.clear()
            fail_tuesday = True
            group_download = page.get_by_role("button", name="Download Semua RPH")
            group_download.click()
            page.get_by_text("1 RPH sudah disimpan dalam tab ini", exact=False).wait_for()
            self.assertEqual([row["teacher_date"] for row in downloads], [MONDAY, TUESDAY])
            with page.expect_download() as saved:
                group_download.click()
            bundled = saved.value
            self.assertTrue(bundled.suggested_filename.endswith(".pdf"))
            raw = bundled.path().read_bytes()
            widths = page.evaluate("""async bytes => {
                const doc = await PDFLib.PDFDocument.load(Uint8Array.from(bytes));
                return doc.getPages().map(page => page.getWidth());
            }""", list(raw))
            self.assertEqual(widths, [595, 600])
            self.assertEqual([row["teacher_date"] for row in downloads], [MONDAY, TUESDAY, TUESDAY])
            expect(page.locator("#week-bundle-quota")).to_contain_text("1 daripada 2")
            with page.expect_download():
                group_download.click()
            expect(page.locator("#week-bundle-quota")).to_contain_text("0 daripada 2")
            group_download.click()
            page.get_by_text("Had dua muat turun RPH mingguan telah dicapai.", exact=False).wait_for()
            self.assertEqual(len(set(bundles)), 2)
            self.assertEqual(len(downloads), 3)
            page.get_by_role("button", name="RPH Hari Ini", exact=True).click()
            page.locator("#today-list").get_by_text("2 Bestari · English", exact=True).wait_for()
            self.assertEqual(page.locator("#view-today-heading").inner_text(), "RPH Pantas")
            self.assertEqual(page.locator("#today-list .daily-rph-card").count(), 1)
            self.assertFalse(group_download.is_visible())
            page.locator("#today-date").fill(THURSDAY)
            page.locator("#today-refresh").click()
            page.get_by_text("Slot hari ini dikecualikan sehingga halaman dimuat semula.", exact=True).wait_for()
            self.assertTrue(excluded.is_checked())
            self.assertFalse(page.locator("#today-confirm-wrap").is_visible())
            self.assertTrue(page.locator("#today-generate-all").is_disabled())
            excluded.uncheck()
            page.get_by_text("2 Cemerlang · Sains", exact=True).wait_for()
            self.assertTrue(page.locator("#today-confirm-wrap").is_visible())
            page.locator("#today-date").fill(HOLIDAY)
            page.locator("#today-refresh").click()
            page.get_by_text(CLOSURE + ". Tiada slot RPH untuk tarikh ini.", exact=True).wait_for()
            self.assertEqual(page.locator("#today-list .daily-rph-card").count(), 0)
            self.assertFalse(page.locator("#today-confirm-wrap").is_visible())
            self.assertTrue(page.locator("#today-generate-all").is_disabled())
            self.assertFalse(errors)
            browser.close()
