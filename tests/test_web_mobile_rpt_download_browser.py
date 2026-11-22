"""Real Chromium mobile regression: RPT one click downloads, without viewer tab."""
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

    def test_sjkc_rph_stays_in_rph_and_rpt_uses_its_own_menu(self):
        page=self.browser.new_page(viewport={"width":360,"height":840},has_touch=True)
        try:
            page.goto(HTML,wait_until="domcontentloaded")
            page.evaluate("""async () => {
                document.querySelector('main.panel').hidden=true;
                document.querySelector('#workspace').hidden=false;
                const row={code:"matematik_sjkc",label:"Matematik (SJKC)",curriculum:"sjkc"};
                sjkcSubjectOptions.push({...row,value:row.code,rpt_years:[2]});
                sjktSubjectOptions.splice(0,sjktSubjectOptions.length,
                    {code:"matematik_sjkt",value:"matematik_sjkt",label:"Matematik (SJKT)",curriculum:"sjkt"});
                const realFetch=window.fetch;
                window.fetch=async (url,options)=>url==='/api/rpt/2027/catalog'
                  ?new Response(JSON.stringify({subjects:[{...row,years:[
                       {year:2,pdf_ready:true,download_enabled:true}]}]}))
                  :realFetch(url,options);
                try { await loadRptCatalog(); } finally { window.fetch=realFetch; }
                showWebView("rph");
            }""")
            page.locator("#curriculum").select_option("sjkc")
            page.locator("#year").select_option("2")
            search=page.locator("#subject-input")
            search.fill("matematik sjkc")
            search.press("Enter")
            self.assertEqual(page.locator("#subject").input_value(),"matematik_sjkc")
            self.assertIn("dalam penyediaan",page.locator("#selection-help").inner_text())
            self.assertTrue(page.locator("#rph-variant-rpt").is_hidden())
            self.assertTrue(page.locator("#view-rph").is_visible())
            self.assertTrue(page.locator("#view-rpt").is_hidden())
            page.locator("#curriculum").select_option("sjkt")
            self.assertFalse(page.locator("#year").is_hidden())
            page.locator("#year").select_option("2")
            page.locator("#subject option[value='matematik_sjkt']").wait_for(state="attached")
            search.fill("matematik sjkt")
            search.press("Enter")
            self.assertEqual(page.locator("#subject").input_value(),"matematik_sjkt")
            self.assertIn("dalam penyediaan",page.locator("#selection-help").inner_text())
            self.assertTrue(page.locator("#view-rpt").is_hidden())
            page.locator('[data-web-view="rpt"]').click()
            self.assertTrue(page.locator("#view-rpt").is_visible())
            page.locator("#rpt-curriculum").select_option("sjkc")
            page.locator("#rpt-year").select_option("2")
            rpt_search=page.locator("#rpt-subject-input")
            rpt_search.fill("matematik sjkc")
            rpt_search.press("Enter")
            self.assertEqual(page.locator("#rpt-subject").input_value(),"matematik_sjkc")
        finally:
            page.close()

    def test_released_sjkc_year_two_opens_rph_units(self):
        page = self.browser.new_page(viewport={"width": 360, "height": 840}, has_touch=True)
        try:
            page.goto(HTML, wait_until="domcontentloaded")
            page.evaluate("""() => {
                document.querySelector('main.panel').hidden = true;
                document.querySelector('#workspace').hidden = false;
                if (!sjkcSubjectOptions.some(row => row.value === 'matematik_sjkc')) {
                    sjkcSubjectOptions.push({value:'matematik_sjkc',label:'Matematik (SJKC)'});
                }
                const previousFetch = window.fetch;
                window.fetch = (url, options) => {
                    const params = new URL(url, 'https://local.example').searchParams;
                    if (params.get('kind') === 'subjects' && params.get('year') === '2'
                        && params.get('curriculum') === 'sjkc') {
                        return Promise.resolve(new Response(JSON.stringify([
                            {value:'MATH_SJKC',label:'Matematik SJKC'}
                        ])));
                    }
                    if (params.get('kind') === 'units' && params.get('subject') === 'MATH_SJKC') {
                        return Promise.resolve(new Response(JSON.stringify([
                            {value:'1',label:'Unit 1 · 1 000 以内的整数'}
                        ])));
                    }
                    return previousFetch(url, options);
                };
                showWebView('rph');
            }""")
            page.locator("#curriculum").select_option("sjkc")
            page.locator("#year").select_option("2")
            page.locator("#subject option[value='MATH_SJKC']").wait_for(state="attached")
            subject_search = page.locator("#subject-input")
            subject_search.fill("matematik sjkc")
            subject_search.press("Enter")
            self.assertEqual(page.locator("#subject").input_value(), "MATH_SJKC")
            page.locator("#unit option[value='1']").wait_for(state="attached")
            self.assertTrue(page.locator("#view-rph").is_visible())
            self.assertTrue(page.locator("#view-rpt").is_hidden())
            self.assertTrue(page.locator("#rph-variant-rpt").is_hidden())
        finally:
            page.close()

    def test_cascading_dropdowns_filter_curriculum_and_clear_downloads(self):
        page=self.browser.new_page(viewport={"width":360,"height":840},has_touch=True)
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
                         docx_url:"/api/rpt/2027/sjkc/bahasa-melayu/3.docx",note:"W.P. Kuala Lumpur"},
                        {year:4,pdf_ready:true,download_enabled:true,docx_ready:true,
                         docx_url:"/api/rpt/2027/sjkc/bahasa-melayu/4.docx",note:"W.P. Kuala Lumpur"},
                        {year:5,pdf_ready:true,download_enabled:true,docx_ready:true,
                         docx_url:"/api/rpt/2027/sjkc/bahasa-melayu/5.docx",note:"W.P. Kuala Lumpur"},
                        {year:6,pdf_ready:true,download_enabled:true,docx_ready:true,
                         docx_url:"/api/rpt/2027/sjkc/bahasa-melayu/6.docx",note:"W.P. Kuala Lumpur"}]},
                    {code:"sains_sjkc",label:"Sains (SJKC)",years:[
                        {year:6,pdf_ready:true,download_enabled:true,docx_ready:true,
                         docx_url:"/api/rpt/2027/sjkc/sains/6.docx"}]},
                    {code:"matematik_sjkc",label:"Matematik (SJKC)",years:[
                        {year:2,pdf_ready:true,download_enabled:true,docx_ready:true,
                         docx_url:"/api/rpt/2027/sjkc/matematik/2.docx"},
                        {year:3,pdf_ready:true,download_enabled:true,docx_ready:true,
                         docx_url:"/api/rpt/2027/sjkc/matematik/3.docx",note:"Tarikh Kumpulan A dan B dalam satu RPT."}]},
                    {code:"science_dlp",label:"Science (DLP)",years:[
                        {year:3,pdf_ready:true,download_enabled:true,year_label:"Year 3"}]},
                    {code:"mathematics_dlp",label:"Mathematics (DLP)",years:[
                        {year:1,pdf_ready:false,download_enabled:false,coming_soon:true},
                        {year:3,pdf_ready:true,download_enabled:true,year_label:"Year 3"}]}
                ];
                const realFetch=window.fetch;
                window.fetch=async ()=>new Response(JSON.stringify({subjects:subjects.reverse(),personalization_allowed:true}));
                try { await loadRptCatalog(); } finally { window.fetch=realFetch; }
            }""")
            curriculum=page.locator("#rpt-curriculum")
            year=page.locator("#rpt-year")
            subject=page.locator("#rpt-subject")
            subject_search=page.get_by_role("combobox",name="Subjek",exact=True)
            subject_options=page.locator("#rpt-subject-list").get_by_role("option")

            def choose_subject(label):
                subject_search.tap()
                subject_search.fill(label)
                subject_options.filter(has_text=label).tap()
            word=page.locator("#rpt-download-word")
            pdf=page.locator("#rpt-download")
            self.assertEqual(curriculum.locator("option").all_text_contents(),
                             ["Pilih kurikulum","KSSR (SK)","KSSR (SJKC)","KP2027"])
            self.assertTrue(year.is_disabled())
            self.assertTrue(subject_search.is_disabled())
            curriculum.select_option("kssr")
            self.assertEqual(year.locator("option").all_text_contents(),["Pilih tahun","Tahun 2","Year 3","Tahun 4"])
            year.select_option("2")
            self.assertEqual(subject.locator("option").all_text_contents(),["Pilih atau cari subjek","English (SK)"])
            choose_subject("English (SK)")
            self.assertTrue(pdf.is_visible())
            self.assertFalse(word.is_visible())
            curriculum.select_option("sjkc")
            self.assertEqual(year.input_value(),"")
            self.assertTrue(subject_search.is_disabled())
            self.assertFalse(pdf.is_visible())
            year.select_option("2")
            subject_search.tap()
            self.assertEqual(subject_options.all_text_contents(),
                             ["Bahasa Cina (SJKC)","Bahasa Melayu (SJK)","Matematik (SJKC)"])
            subject_search.fill("melayu")
            self.assertEqual(subject_options.all_text_contents(),["Bahasa Melayu (SJK)"])
            subject_search.fill("tiada padanan")
            self.assertTrue(page.locator("#view-rpt").get_by_text("Tiada subjek sepadan.").is_visible())
            subject_search.fill("cInA")
            subject_search.press("ArrowDown")
            subject_search.press("Enter")
            self.assertEqual(subject_search.input_value(),"Bahasa Cina (SJKC)")
            self.assertTrue(word.is_visible())
            self.assertEqual(word.get_attribute("href"),"/api/rpt/2027/sjkc/bahasa-cina/2.docx")
            choose_subject("Bahasa Melayu (SJK)")
            self.assertTrue(word.is_visible())
            self.assertEqual(word.get_attribute("href"),"/api/rpt/2027/sjkc/bahasa-melayu/2.docx")
            self.assertIn("W.P. Kuala Lumpur",page.locator("#rpt-status").inner_text())
            choose_subject("Matematik (SJKC)")
            self.assertTrue(word.is_visible())
            self.assertEqual(word.get_attribute("href"),"/api/rpt/2027/sjkc/matematik/2.docx")
            year.select_option("3")
            self.assertEqual(subject.input_value(),"")
            self.assertEqual(subject_search.input_value(),"")
            self.assertIsNone(word.get_attribute("href"))
            choose_subject("Bahasa Cina (SJKC)")
            self.assertIn("akses berbayar",page.locator("#rpt-status").inner_text())
            self.assertFalse(pdf.is_visible())
            choose_subject("Bahasa Melayu (SJK)")
            self.assertTrue(pdf.is_visible())
            self.assertEqual(word.get_attribute("href"),"/api/rpt/2027/sjkc/bahasa-melayu/3.docx")
            choose_subject("Matematik (SJKC)")
            self.assertTrue(pdf.is_visible())
            self.assertTrue(word.is_visible())
            self.assertEqual(word.get_attribute("href"),"/api/rpt/2027/sjkc/matematik/3.docx")
            self.assertIn("Kumpulan A dan B",page.locator("#rpt-status").inner_text())
            year.select_option("4")
            choose_subject("Bahasa Melayu (SJK)")
            self.assertTrue(pdf.is_visible())
            self.assertEqual(word.get_attribute("href"),"/api/rpt/2027/sjkc/bahasa-melayu/4.docx")
            year.select_option("5")
            choose_subject("Bahasa Melayu (SJK)")
            self.assertTrue(pdf.is_visible())
            self.assertEqual(word.get_attribute("href"),"/api/rpt/2027/sjkc/bahasa-melayu/5.docx")
            year.select_option("6")
            choose_subject("Bahasa Melayu (SJK)")
            self.assertTrue(pdf.is_visible())
            self.assertEqual(word.get_attribute("href"),"/api/rpt/2027/sjkc/bahasa-melayu/6.docx")
            choose_subject("Sains (SJKC)")
            self.assertTrue(word.is_visible())
            self.assertEqual(word.get_attribute("href"),"/api/rpt/2027/sjkc/sains/6.docx")
            curriculum.select_option("kp2027")
            year.select_option("1")
            self.assertEqual(subject.locator("option").all_text_contents(),
                             ["Pilih atau cari subjek","English (SK) — Dalam Penyediaan"])
            choose_subject("English (SK)")
            self.assertEqual(page.locator("#rpt-status").inner_text(),"Dalam Penyediaan")
            self.assertFalse(pdf.is_visible())
            curriculum.select_option("kssr")
            year.select_option("3")
            for label in ("Science (DLP)", "Mathematics (DLP)"):
                choose_subject(label)
                self.assertTrue(pdf.is_visible())
                self.assertIsNone(word.get_attribute("href"))
        finally:
            page.close()

    def test_phone_shows_the_direct_download_button_not_a_second_step_link(self):
        for width in (320,360,375,390,430,760):
            with self.subTest(width=width):
                page=self.browser.new_page(viewport={"width":width,"height":840})
                try:
                    result=self.prepare(page)
                    self.assertEqual(result["href"],"#")
                    self.assertEqual(result["linkDisplay"],"none")
                    self.assertNotEqual(result["desktopButtonDisplay"],"none")
                    self.assertIsNone(result["linkTarget"])
                    self.assertFalse(result["desktopButtonDisabled"])
                    self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"),width+1)
                finally:
                    page.close()

    def test_phone_click_starts_direct_pdf_download_once_without_popup(self):
        page=self.browser.new_page(viewport={"width":390,"height":844})
        popups=[]
        try:
            self.prepare(page)
            page.on("popup",lambda popup:popups.append(popup))
            page.evaluate("""() => {
                window.__rptMobileCalls=[];
                window.downloadCikguLajuRPT=(code,year,name,output,button,viewer,mobile)=>{
                    window.__rptMobileCalls.push({
                        code,year,name,hasViewer:!!viewer,mobileRequest:!!mobile,
                        expectedStatusElement:output?.id==="rpt-status"
                    });
                    return Promise.resolve(true);
                };
            }""")
            page.locator("#rpt-download").click()
            result=page.evaluate("window.__rptMobileCalls")
            self.assertEqual(result,[{
                "code":"pjpk","year":2,"name":"PJPK",
                "hasViewer":False,"mobileRequest":False,
                "expectedStatusElement":True
            }])
            self.assertEqual(popups,[])
        finally:
            for popup in popups:popup.close()
            page.close()

    def test_phone_does_not_depend_on_popup_permission(self):
        page=self.browser.new_page(viewport={"width":375,"height":812})
        try:
            self.prepare(page)
            result=page.evaluate("""() => {
                window.open=()=>{throw Error("Popup must not be opened")};
                window.__rptMobileCalls=[];
                window.downloadCikguLajuRPT=(code,year,name,output,button,viewer)=>{
                    window.__rptMobileCalls.push({code,year,hasViewer:!!viewer});
                    return Promise.resolve(true);
                };
                document.querySelector("#rpt-download").click();
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
