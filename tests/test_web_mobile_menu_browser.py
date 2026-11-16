"""Real-browser responsive regression for CikguLaju Web navigation.

Runs against the production HTML; no credentials or live services required.
"""
from pathlib import Path
import unittest
from urllib.parse import urlsplit
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

    def test_all_tabs_visible_without_horizontal_scrolling_on_phones(self):
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
                      const tabs=[...menu.querySelectorAll('.sidebar-tab:not([hidden])')];
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
                    self.assertEqual(len(metrics["tabs"]),12,metrics)
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
                        ("Buka RPH Hari Ini","today","view-today-heading"),
                    ]:
                        if view=="today":
                            with page.expect_request(HOST+"/api/web/rph/hari-ini*"):
                                page.get_by_role("button",name=label).click()
                        else:
                            page.get_by_role("button",name=label).click()
                        expect(guide).to_be_hidden()
                        expect(page.locator("#"+heading_id)).to_be_focused()
                        expect(nav.locator('[data-web-view="'+view+'"]')).to_have_attribute("aria-current","page")
                        nav.get_by_role("button",name="Panduan").click()
                        expect(guide).to_be_visible()
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
        finally:
            page.close()


if __name__=="__main__":
    unittest.main()
