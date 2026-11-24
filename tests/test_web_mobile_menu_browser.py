"""Real-browser responsive regression for CikguLaju Web navigation.

Runs against the production HTML; no credentials or live services required.
"""
from pathlib import Path
import unittest
from urllib.parse import parse_qs, urlsplit
from playwright.sync_api import expect, sync_playwright

WEB = Path(__file__).resolve().parents[1] / "web_v1_static_preview"
PAGE = (WEB / "index.html").as_uri()
HOST = "https://cikgulaju-guide.test"


class PhoneMenuLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_main_menu_is_compact_and_other_tabs_fit_when_expanded(self):
        for width in (320, 360, 375, 390, 430, 600, 760):
            with self.subTest(width=width):
                page=self.browser.new_page(viewport={"width":width,"height":820})
                try:
                    page.goto(PAGE,wait_until="domcontentloaded")
                    page.evaluate("""() => {
                      document.querySelector('main.panel').hidden = true;
                      document.querySelector('#workspace').hidden = false;
                    }""")
                    metrics=page.evaluate("""() => {
                      const menu=document.querySelector('.sidebar-menu');
                      const box=menu.getBoundingClientRect();
                      const tabs=[...menu.querySelectorAll('.sidebar-tab')].filter(tab=>tab.getClientRects().length);
                      return {
                        display:getComputedStyle(menu).display,
                        columns:getComputedStyle(menu).gridTemplateColumns,
                        scroll:menu.scrollWidth,
                        client:menu.clientWidth,
                        body:document.body.scrollWidth,
                        tabs:tabs.map(tab=>{
                          const b=tab.getBoundingClientRect();
                          return {label:tab.textContent.trim(),left:b.left,right:b.right,
                                  width:b.width,top:b.top,bottom:b.bottom};
                        }),
                        left:box.left,right:box.right
                      };
                    }""")
                    self.assertEqual(metrics["display"],"grid",metrics)
                    self.assertEqual(len(metrics["tabs"]),6,metrics)
                    self.assertLessEqual(metrics["scroll"],metrics["client"]+1,metrics)
                    self.assertLessEqual(metrics["body"],width+1,metrics)
                    for tab in metrics["tabs"]:
                        self.assertGreaterEqual(tab["left"],metrics["left"]-1,metrics)
                        self.assertLessEqual(tab["right"],metrics["right"]+1,metrics)
                        self.assertGreaterEqual(tab["width"],60,metrics)
                    # Users must be able to navigate without a swipe.
                    page.get_by_role("button",name="Profil & Akses",exact=True).click()
                    self.assertFalse(page.locator("#view-account").get_attribute("hidden") is not None)
                    self.assertEqual(page.locator('[data-web-view="account"]').get_attribute("aria-current"),"page")
                    page.get_by_role("button",name="Rakan Pembangun").click()
                    self.assertFalse(page.locator("#view-payment").get_attribute("hidden") is not None)
                    self.assertEqual(page.locator('[data-web-view="payment"]').get_attribute("aria-current"),"page")
                    more=page.locator("#sidebar-more")
                    self.assertFalse(more.evaluate("(node)=>node.open"))
                    expect(page.get_by_role("button",name="Rekod PBD")).to_be_hidden()
                    more.locator("summary").focus()
                    page.keyboard.press("Enter")
                    self.assertTrue(more.evaluate("(node)=>node.open"))
                    self.assertLessEqual(more.evaluate("(node)=>node.scrollWidth"),width)
                    for tab in more.locator('.sidebar-tab:not([hidden])').all():
                        expect(tab).to_be_visible()
                        box=tab.bounding_box()
                        self.assertGreaterEqual(box["x"],0)
                        self.assertLessEqual(box["x"]+box["width"],width+1)
                    expect(more.get_by_text("Akan Datang",exact=True)).to_have_count(3)
                    expect(more.locator("#web-admin-tab")).to_be_hidden()
                    expect(more.locator("#web-referral-tab")).to_be_hidden()
                    more.get_by_role("button",name="Rekod PBD").click()
                    expect(page.locator("#view-pbd-heading")).to_be_focused()
                    expect(more.get_by_role("button",name="Rekod PBD")).to_have_attribute("aria-current","page")
                    page.get_by_role("button",name="Panduan",exact=True).click()
                    self.assertFalse(more.evaluate("(node)=>node.open"))
                finally:
                    page.close()

    def test_login_opens_guide_and_shortcuts_use_normal_navigation(self):
        for width in (390,1200):
            with self.subTest(width=width):
                page=self.browser.new_page(viewport={"width":width,"height":840})
                signed_in=False
                today_requests=[]

                def mock(route):
                    nonlocal signed_in
                    path=urlsplit(route.request.url).path
                    if path=="/":
                        return route.fulfill(status=200,content_type="text/html",
                                             body=(WEB/"index.html").read_bytes())
                    if path=="/api/auth/telegram/session":
                        return route.fulfill(status=200 if signed_in else 401,json={
                            "rph_access_mode":"trial","rph_trial_remaining":10})
                    if path=="/api/auth/telegram/widget":
                        signed_in=True
                        return route.fulfill(status=200,json={})
                    if path=="/api/auth/capabilities":
                        return route.fulfill(status=200,json={"telegram_widget_enabled":False})
                    if path.startswith("/assets/"):
                        asset=WEB/path.rsplit("/",1)[-1]
                        if asset.is_file():
                            return route.fulfill(status=200,path=asset)
                    if path=="/api/web/rph/hari-ini":
                        today_requests.append(path)
                    return route.fulfill(status=404,json={})

                page.route(HOST+"/**",mock)
                try:
                    page.goto(HOST+"/",wait_until="load")
                    guide=page.get_by_role("heading",name="Panduan Penggunaan")
                    expect(guide).to_be_hidden()
                    with page.expect_navigation(wait_until="load"):
                        page.evaluate("() => { void window.onCikguLajuTelegramAuth({id:123}); }")
                    expect(guide).to_be_visible()
                    nav=page.get_by_role("navigation",name="Menu utama")
                    expect(nav.get_by_role("button",name="Panduan")).to_have_attribute("aria-current","page")
                    self.assertEqual(today_requests,[])

                    for label, view, heading_id in [
                        ("Buka Profil & Akses","account","view-account-heading"),
                        ("Buka Sediakan RPH","rph","view-rph-heading"),
                        ("Buka RPT 2027","rpt","rpt2027-heading"),
                        ("Buka RPH Pantas","today","view-today-heading"),
                    ]:
                        if view=="today":
                            with page.expect_request(HOST+"/api/web/rph/hari-ini*"):
                                page.get_by_role("button",name=label).click()
                        else:
                            page.get_by_role("button",name=label).click()
                        expect(guide).to_be_hidden()
                        expect(page.locator("#"+heading_id)).to_be_focused()
                        expect(nav.locator('[data-web-view="'+view+'"]')).to_have_attribute("aria-current","page")
                        if view=="today":
                            expect(nav.get_by_role("button", name="RPH Pantas")).to_be_visible()
                            expect(nav.get_by_text("Hari Ini & Minggu Ini",exact=True)).to_be_visible()
                            expect(nav.locator('[data-web-view="today"] [aria-hidden="true"]')).to_have_text("⚡")
                        nav.get_by_role("button",name="Panduan").click()
                        expect(guide).to_be_visible()
                finally:
                    page.close()

    def test_year_one_book_references_appear_after_each_lesson_selection(self):
        page = self.browser.new_page(viewport={"width": 390, "height": 840})
        textbook = "Buku Teks Jilid 1, hlm. 1–4"
        activitybook = "Buku Aktiviti Jilid 1, hlm. 1–5"
        lesson = {"value": "PDP1", "label": "PdP 1 • Banding kuantiti melalui padanan",
                  "textbook_ref": textbook, "activitybook_ref": activitybook}
        unit = {"value": "u" + "a" * 24, "label": "Unit 1: Nombor Bulat Hingga 100"}
        options = {"subjects": [{"value": "MATH", "label": "Matematik"}],
                   "units": [unit], "pdp": [lesson]}

        def mock(route):
            request = urlsplit(route.request.url)
            if request.path == "/":
                return route.fulfill(content_type="text/html", path=WEB / "index.html")
            if request.path == "/api/auth/telegram/session":
                return route.fulfill(json={"rph_access_mode": "trial", "rph_trial_remaining": 10})
            if request.path == "/api/auth/capabilities":
                return route.fulfill(json={"telegram_widget_enabled": False})
            if request.path == "/api/options":
                kind = parse_qs(request.query).get("kind", [""])[0]
                return route.fulfill(json=options.get(kind, []))
            if request.path == "/api/web/rph/hari-ini":
                return route.fulfill(json={
                    "date": "2026-11-19", "day": "Khamis", "count": 1, "holiday_notice": "",
                    "entries": [{"year": 1, "class_name": "1 Bestari",
                                 "subject_code": "MATH", "subject": "Matematik",
                                 "start": "08:00", "end": "08:30", "can_prepare": True}],
                })
            if request.path.startswith("/assets/"):
                asset = WEB / request.path.rsplit("/", 1)[-1]
                if asset.is_file():
                    return route.fulfill(path=asset)
            return route.fulfill(status=404, json={})

        page.route("**/*", lambda route: route.abort())
        page.route(HOST + "/**", mock)
        try:
            page.goto(HOST + "/", wait_until="load")
            page.get_by_role("button", name="Buka Sediakan RPH").click()
            page.locator("#curriculum").select_option("kssr")
            page.locator("#year").select_option("1")
            page.locator("#rph-subject-search input").click()
            page.get_by_role("option", name="Matematik (SK)", exact=True).click()
            expect(page.locator("#unit option", has_text="Unit 1:")).to_have_count(1)
            page.locator("#unit").select_option(unit["value"])
            page.locator("#lesson").select_option("PDP1")
            expected = f"Rujukan buku: {textbook} • {activitybook}"
            expect(page.locator("#lesson-source-pages")).to_have_text(expected)
            page.locator("#lesson").select_option("")
            expect(page.locator("#lesson-source-pages")).to_be_hidden()

            page.get_by_role("navigation", name="Menu utama").get_by_role(
                "button", name="RPH Pantas").click()
            page.locator("#today-0-unit").select_option(unit["value"])
            page.locator("#today-0-lesson").select_option("PDP1")
            expect(page.locator("#today-list").get_by_text(expected, exact=True)).to_be_visible()
        finally:
            page.close()

    def test_desktop_sidebar_remains_vertical(self):
        page=self.browser.new_page(viewport={"width":1200,"height":900})
        try:
            page.goto(PAGE,wait_until="domcontentloaded")
            page.evaluate("""() => {
              document.querySelector('main.panel').hidden = true;
              document.querySelector('#workspace').hidden = false;
            }""")
            m=page.evaluate("""() => {
              const menu=document.querySelector('.sidebar-menu');
              return {display:getComputedStyle(menu).display,
                      direction:getComputedStyle(menu).flexDirection};
            }""")
            self.assertEqual(m,{"display":"flex","direction":"column"})
            self.assertFalse(page.locator("#sidebar-more").evaluate("(node)=>node.open"))
            # The admin sidebar button is deliberately hidden: admin now
            # resides above the workspace in Pusat Admin. Simulate the same
            # authorized UI state without creating a live account.
            page.evaluate("""() => {
              const admin=document.getElementById("web-admin-tab");
              const top=document.getElementById("web-admin-top");
              admin.hidden=false;
              top.hidden=false;
              top.open=true;
              admin.click();
            }""")
            expect(page.locator("#web-admin-top")).to_be_visible()
            expect(page.locator("#web-admin-top > summary")).to_contain_text("Pusat Admin")
            expect(page.locator("#web-admin-tab")).to_be_hidden()
            self.assertTrue(page.locator("#web-admin-top").evaluate("(node)=>node.open"))
            expect(page.locator("#web-admin-heading")).to_be_visible()
        finally:
            page.close()


if __name__=="__main__":
    unittest.main()
