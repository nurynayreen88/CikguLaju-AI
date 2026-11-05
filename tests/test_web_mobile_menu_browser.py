"""Real-browser responsive regression for CikguLaju Web navigation.

Runs against the production HTML; no credentials or live services required.
"""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

PAGE = (Path(__file__).resolve().parents[1] /
        "web_v1_static_preview" / "index.html").as_uri()


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
                      const tabs=[...menu.querySelectorAll('.sidebar-tab')];
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
                    self.assertEqual(len(metrics["tabs"]),5,metrics)
                    self.assertLessEqual(metrics["scroll"],metrics["client"]+1,metrics)
                    self.assertLessEqual(metrics["body"],width+1,metrics)
                    for tab in metrics["tabs"]:
                        self.assertGreaterEqual(tab["left"],metrics["left"]-1,metrics)
                        self.assertLessEqual(tab["right"],metrics["right"]+1,metrics)
                        self.assertGreaterEqual(tab["width"],60,metrics)
                    # Users must be able to navigate without a swipe.
                    page.get_by_role("button",name="Profil & Akses").click()
                    self.assertFalse(page.locator("#view-account").get_attribute("hidden") is not None)
                    self.assertEqual(page.locator('[data-web-view="account"]').get_attribute("aria-current"),"page")
                    page.get_by_role("button",name="Rakan Pembangun").click()
                    self.assertFalse(page.locator("#view-payment").get_attribute("hidden") is not None)
                    self.assertEqual(page.locator('[data-web-view="payment"]').get_attribute("aria-current"),"page")
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
