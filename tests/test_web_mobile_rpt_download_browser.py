"""Real Chromium mobile regression: RPT click preopens viewer before async profile stamp."""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

HTML=(Path(__file__).resolve().parents[1]/"web_v1_static_preview"/"index.html").as_uri()

class MobileRptDownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright=sync_playwright().start()
        cls.browser=cls.playwright.chromium.launch(headless=True)
    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    @staticmethod
    def prepare(page, *,allowed=True, ready=True):
        page.goto(HTML,wait_until="domcontentloaded")
        return page.evaluate("""({allowed, ready}) => {
          document.querySelector('main.panel').hidden=true;
          document.querySelector('#workspace').hidden=false;
          document.querySelector('#view-rpt').hidden=false;
          const item={code:'pjpk',label:'PJPK',years:[{
            year:2,status:'DRAF',pdf_ready:ready,
            download_enabled:allowed&&ready}]};
          rptCatalog={allowed,subjects:[item]};
          const s=document.getElementById('rpt-subject');
          s.replaceChildren(new Option('Pilih Subjek',''),new Option('PJPK','pjpk'));
          s.value='pjpk';
          const y=document.getElementById('rpt-year');
          y.replaceChildren(new Option('Tahun 2','2'));
          y.value='2';
          refreshRptDownload();
          const b=document.getElementById('rpt-download');
          const a=document.getElementById('rpt-download-mobile');
          return {
             href:a.getAttribute('href'),
             linkHidden:a.hidden,
             linkDisplay:getComputedStyle(a).display,
             desktopButtonDisabled:b.disabled,
             desktopButtonDisplay:getComputedStyle(b).display,
             status:document.getElementById('rpt-status').textContent,
             linkTarget:a.getAttribute('target')
          };
        }""",{"allowed":allowed,"ready":ready})

    def test_phone_uses_safe_placeholder_link_for_personalized_rpt(self):
        for width in (320,360,375,390,430,760):
            with self.subTest(width=width):
                page=self.browser.new_page(viewport={"width":width,"height":840})
                try:
                    result=self.prepare(page)
                    self.assertEqual(result["href"],"#")
                    self.assertFalse(result["linkHidden"])
                    self.assertEqual(result["linkDisplay"],"inline-flex")
                    self.assertEqual(result["desktopButtonDisplay"],"none")
                    self.assertEqual(result["linkTarget"],"_blank")
                    self.assertFalse(result["desktopButtonDisabled"])
                    self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"),width+1)
                finally:
                    page.close()

    def test_phone_click_opens_viewer_synchronously_for_profile_pdf(self):
        page=self.browser.new_page(viewport={"width":390,"height":844})
        popup=None
        try:
            self.prepare(page)
            page.evaluate("""() => {
                window.__rptMobileCalls=[];
                window.downloadCikguLajuRPT=(code,year,name,output,button,viewer)=>{
                    window.__rptMobileCalls.push({
                        code,year,name,hasViewer:!!viewer,
                        expectedStatusElement:output?.id==="rpt-status"
                    });
                    return Promise.resolve(true);
                };
            }""")
            with page.expect_popup() as opened:
                page.locator("#rpt-download-mobile").click()
            popup=opened.value
            result=page.evaluate("window.__rptMobileCalls")
            self.assertEqual(result,[{
                "code":"pjpk","year":2,"name":"PJPK",
                "hasViewer":True,"expectedStatusElement":True
            }])
            self.assertEqual(popup.url,"about:blank")
            self.assertIn("Menyediakan PDF RPT",popup.locator("body").inner_text())
        finally:
            if popup:
                popup.close()
            page.close()

    def test_phone_without_popup_permission_keeps_fallback_path(self):
        page=self.browser.new_page(viewport={"width":375,"height":812})
        try:
            self.prepare(page)
            result=page.evaluate("""() => {
                window.open=()=>null;
                window.__rptMobileCalls=[];
                window.downloadCikguLajuRPT=(code,year,name,output,button,viewer)=>{
                    window.__rptMobileCalls.push({code,year,hasViewer:!!viewer});
                    return Promise.resolve(true);
                };
                document.querySelector("#rpt-download-mobile").click();
                return window.__rptMobileCalls;
            }""")
            self.assertEqual(result,[{"code":"pjpk","year":2,"hasViewer":False}])
        finally:
            page.close()

    def test_desktop_original_download_remains_available(self):
        page=self.browser.new_page(viewport={"width":1200,"height":900})
        try:
            result=self.prepare(page)
            self.assertEqual(result["linkDisplay"],"none")
            self.assertNotEqual(result["desktopButtonDisplay"],"none")
            self.assertFalse(result["desktopButtonDisabled"])
        finally:
            page.close()

    def test_unpaid_or_unavailable_pdf_has_no_direct_link(self):
        for config in ({"allowed":False,"ready":True},
                       {"allowed":True,"ready":False}):
            with self.subTest(config=config):
                page=self.browser.new_page(viewport={"width":360,"height":840})
                try:
                    result=self.prepare(page,**config)
                    self.assertTrue(result["linkHidden"])
                    self.assertIsNone(result["href"])
                    self.assertTrue(result["desktopButtonDisabled"])
                finally:
                    page.close()

if __name__=="__main__":
    unittest.main()
