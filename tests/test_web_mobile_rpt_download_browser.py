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
        return page.evaluate("""async ({allowed, ready}) => {
          document.querySelector('main.panel').hidden=true;
          document.querySelector('#workspace').hidden=false;
          document.querySelector('#view-rpt').hidden=false;
          const item={code:'pjpk',label:'PJPK',years:[{
            year:2,status:'DRAF',pdf_ready:ready,
            download_enabled:allowed&&ready}]};
          const realFetch=window.fetch;
          window.fetch=async (url, options)=>url==='/api/rpt/2027/catalog'
            ?new Response(JSON.stringify({allowed,subjects:[item]}))
            :realFetch(url,options);
          try { await loadRptCatalog(); } finally { window.fetch=realFetch; }
          for(const [id,value] of [['rpt-curriculum','kssr'],['rpt-year','2'],['rpt-subject','pjpk']]){
            const select=document.getElementById(id);
            select.value=value;
            select.dispatchEvent(new Event('change'));
          }
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

    def test_cascading_dropdowns_filter_curriculum_and_clear_downloads(self):
        page=self.browser.new_page(viewport={"width":360,"height":840})
        try:
            self.prepare(page)
            page.evaluate("""async () => {
                const subjects=[
                    {code:"english",label:"English (SK)",years:[
                        {year:1,coming_soon:true},{year:2,pdf_ready:true,download_enabled:true}]},
                    {code:"sejarah",label:"Sejarah",years:[
                        {year:4,pdf_ready:true,download_enabled:true}]},
                    {code:"bahasa_cina_sjkc",label:"Bahasa Cina (SJKC)",years:[
                        {year:2,pdf_ready:true,download_enabled:true,docx_ready:true,docx_url:"/api/rpt/2027/sjkc/bahasa-cina/2.docx",note:"W.P. Kuala Lumpur"},
                        {year:3,pdf_ready:true,download_enabled:false}]},
                    {code:"bahasa_melayu_sjk",label:"Bahasa Melayu (SJK)",years:[
                        {year:2,pdf_ready:true,download_enabled:true,docx_ready:true,
                         docx_url:"/api/rpt/2027/sjkc/bahasa-melayu/2.docx",note:"W.P. Kuala Lumpur"},
                        {year:3,pdf_ready:true,download_enabled:true,docx_ready:true,
                         docx_url:"/api/rpt/2027/sjkc/bahasa-melayu/3.docx",note:"W.P. Kuala Lumpur"}]},
                    {code:"science_dlp",label:"Science (DLP)",years:[
                        {year:3,pdf_ready:true,download_enabled:true,year_label:"Year 3"}]}
                ];
                const realFetch=window.fetch;
                window.fetch=async ()=>new Response(JSON.stringify({subjects,personalization_allowed:true}));
                try { await loadRptCatalog(); } finally { window.fetch=realFetch; }
            }""")
            curriculum=page.locator("#rpt-curriculum")
            year=page.locator("#rpt-year")
            subject=page.locator("#rpt-subject")
            word=page.locator("#rpt-download-word")
            pdf=page.locator("#rpt-download-mobile")
            self.assertEqual(curriculum.locator("option").all_text_contents(),
                             ["Pilih kurikulum","KSSR (SK)","KSSR (SJKC)","KP2027","DLP"])
            self.assertTrue(year.is_disabled())
            self.assertTrue(subject.is_disabled())
            curriculum.select_option("kssr")
            self.assertEqual(year.locator("option").all_text_contents(),["Pilih tahun","Tahun 2","Tahun 4"])
            year.select_option("2")
            self.assertEqual(subject.locator("option").all_text_contents(),["Pilih subjek","English (SK)"])
            subject.select_option("english")
            self.assertTrue(pdf.is_visible())
            self.assertFalse(word.is_visible())
            curriculum.select_option("sjkc")
            self.assertEqual(year.input_value(),"")
            self.assertTrue(subject.is_disabled())
            self.assertFalse(pdf.is_visible())
            year.select_option("2")
            subject.select_option("bahasa_cina_sjkc")
            self.assertTrue(word.is_visible())
            self.assertEqual(word.get_attribute("href"),"/api/rpt/2027/sjkc/bahasa-cina/2.docx")
            subject.select_option("bahasa_melayu_sjk")
            self.assertTrue(word.is_visible())
            self.assertEqual(word.get_attribute("href"),"/api/rpt/2027/sjkc/bahasa-melayu/2.docx")
            self.assertIn("W.P. Kuala Lumpur",page.locator("#rpt-status").inner_text())
            year.select_option("3")
            self.assertEqual(subject.input_value(),"")
            self.assertIsNone(word.get_attribute("href"))
            subject.select_option("bahasa_cina_sjkc")
            self.assertIn("akses berbayar",page.locator("#rpt-status").inner_text())
            self.assertFalse(pdf.is_visible())
            subject.select_option("bahasa_melayu_sjk")
            self.assertTrue(pdf.is_visible())
            self.assertEqual(word.get_attribute("href"),"/api/rpt/2027/sjkc/bahasa-melayu/3.docx")
            curriculum.select_option("kp2027")
            year.select_option("1")
            subject.select_option("english")
            self.assertEqual(page.locator("#rpt-status").inner_text(),"Dalam Penyediaan")
            self.assertFalse(pdf.is_visible())
            curriculum.select_option("dlp")
            self.assertEqual(year.locator("option").all_text_contents(),["Pilih tahun","Year 3"])
            year.select_option("3")
            subject.select_option("science_dlp")
            self.assertTrue(pdf.is_visible())
            self.assertIsNone(word.get_attribute("href"))
        finally:
            page.close()

    def test_phone_uses_safe_placeholder_link_for_personalized_rpt(self):
        for width in (320,360,375,390,430,760):
            with self.subTest(width=width):
                page=self.browser.new_page(viewport={"width":width,"height":840})
                try:
                    result=self.prepare(page)
                    self.assertEqual(result["href"],"#")
                    self.assertFalse(result["linkHidden"])
                    self.assertNotEqual(result["linkDisplay"],"none")
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
