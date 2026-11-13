"""Actual Chromium click / download UI contract, simulated API, zero live users.

No real Telegram, payment, Supabase request or new draft source. A browser
loads the same Web RPH page shipped to teachers and clicks real Word/PDF
controls with synthetic Year4 Sains selection and same-origin mock API.
"""
from __future__ import annotations

from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"web_v1_static_preview/index.html").as_uri()
UNIT="u"+"a"*24
PDP="SCI-Y4-PDP-001"


class ScienceBrowserDownloadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw=sync_playwright().start()
        cls.browser=cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.page=self.browser.new_page(
            viewport={"width":375,"height":812},accept_downloads=True)
        self.page.goto(HTML,wait_until="domcontentloaded")
        self.page.set_default_timeout(8000)
        self.page.evaluate("""({unit,pdp})=>{
          document.querySelector('main.panel').hidden=true;
          document.querySelector('#workspace').hidden=false;
          showWebView('rph'); // Mimic authenticated teacher opening sidebar RPH
          document.querySelector('#teacher-info').hidden=false;
          for(const [id,value] of [
             ['year','4'],['subject','SCIENCE'],['unit',unit],['lesson',pdp]
          ]) {
            const node=document.getElementById(id);
            node.add(new Option(value,value));
            node.value=value;
          }
          const date=document.getElementById('teacher-date');
          if(date)date.value='2026-11-08';
          verifiedRphKey=currentRphLessonKey();
          verifiedRphFormats=['word','pdf'];
          applyRphAccount({rph_access_mode:'trial',rph_trial_remaining:10});
          showRphAction();
          // Real teacher flow: select Lesson, then press "Jana Bahan".
          // Direct legacy #rph-word/pdf buttons are intentionally hidden.
          const materials=document.getElementById('show-materials');
          materials.hidden=false;
          materials.disabled=false;
          window.__sainsRequests=[];
          window.fetch=async (url,options)=>{
            const target=String(url);
            if(target.includes('/api/web/rph/extra-materials?')){
              return new Response(JSON.stringify({items:[]}),
                {status:200,headers:{'content-type':'application/json'}});
            }
            if(target.includes('/api/web/rph/word?')||
               target.includes('/api/web/rph/pdf?')){
              const isPdf=target.includes('/pdf?');
              window.__sainsRequests.push(target);
              const remaining=10-window.__sainsRequests.length;
              const bytes=new Uint8Array(2200);
              bytes[0]=isPdf?37:80;bytes[1]=isPdf?80:75;
              const headers={
                'content-type':isPdf?'application/pdf':
                   'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'X-RPH-Generator':'telegram-native',
                'X-RPH-Access-Mode':'trial',
                'X-RPH-Trial-Remaining':String(remaining)
              };
              return new Response(bytes,{status:200,headers});
            }
            return new Response(JSON.stringify({error:'unexpected request'}),
              {status:503,headers:{'content-type':'application/json'}});
          };
        }""",{"unit":UNIT,"pdp":PDP})
        self.assertTrue(self.page.locator("#show-materials").is_visible())


    def tearDown(self):
        self.page.close()

    def test_real_word_and_pdf_click_decrements_shared_balance_once_each(self):
        self.page.locator("#show-materials").click()
        self.assertTrue(self.page.locator("#materials-panel").is_visible())
        self.assertEqual(self.page.locator("#materials-list li").count(),2)
        self.assertTrue(self.page.locator("#rph-download-actions").is_hidden())
        for fmt,balance in (("word",9),("pdf",8)):
            with self.subTest(fmt=fmt):
                with self.page.expect_download() as downloaded:
                    label="RPH Word" if fmt=="word" else "RPH PDF"
                    self.page.locator("#materials-list li").filter(
                        has_text=label).locator("button").click()
                result=downloaded.value
                self.assertTrue(result.suggested_filename.endswith(
                    ".docx" if fmt=="word" else ".pdf"))
                self.assertIn("SCI-Y4-PDP-001",result.suggested_filename)
                self.page.wait_for_function(
                    "(b)=>document.querySelector('#rph-download-status')"
                    ".textContent.includes('Baki percuma: '+b+' daripada 10')",
                    arg=balance)
                self.assertIn(f"{balance} daripada 10 janaan",
                              self.page.locator("#account-access").inner_text())
        requests=self.page.evaluate("window.__sainsRequests")
        self.assertEqual(len(requests),2)
        self.assertTrue(all("subject=SCIENCE" in q and "SCI-Y4-PDP-001" in q
                            and "teacher_date=2026-11-08" in q for q in requests))
        self.assertEqual(self.page.evaluate("document.documentElement.scrollWidth"),375)

    def test_access_zero_hides_science_download_and_never_calls_backend(self):
        self.page.evaluate("""()=>{
            applyRphAccount({rph_access_mode:'exhausted',rph_trial_remaining:0});
            showRphAction();
        }""")
        self.page.locator("#show-materials").click()
        self.assertTrue(self.page.locator("#materials-panel").is_visible())
        self.assertEqual(self.page.locator("#materials-list li").count(),2)
        for row in self.page.locator("#materials-list li").all():
            self.assertIn("Akses diperlukan",row.inner_text())
            self.assertFalse(row.locator("button").is_enabled())
        self.assertIn("0 daripada 10 janaan",
                      self.page.locator("#account-access").inner_text())
        self.assertEqual(self.page.evaluate("window.__sainsRequests.length"),0)

    def test_native_telegram_503_keeps_selection_and_trial_balance(self):
        self.page.evaluate("""()=>{
          window.__sainsRequests=[];
          window.fetch=async (url)=>{
            const target=String(url);
            if(target.includes('/api/web/rph/extra-materials?')){
              return new Response(JSON.stringify({items:[]}),
                {status:200,headers:{'content-type':'application/json'}});
            }
            window.__sainsRequests.push(target);
            return new Response(
              JSON.stringify({error:'Penjana RPH Telegram belum dapat dihubungi.',
                              code:'TELEGRAM_RPH_GENERATOR_UNAVAILABLE'}),
              {status:503,headers:{'content-type':'application/json'}});
          };
        }""")
        self.page.locator("#show-materials").click()
        self.page.locator("#materials-list li").filter(
            has_text="RPH Word").locator("button").click()
        self.page.wait_for_function("""() =>
          document.querySelector('#rph-download-status')
             .textContent.includes('Penjana RPH Telegram belum dapat dihubungi')
        """)
        self.assertEqual(self.page.locator("#lesson").input_value(),PDP)
        self.assertIn("10 daripada 10 janaan",
                      self.page.locator("#account-access").inner_text())
        self.assertEqual(self.page.evaluate("window.__sainsRequests.length"),1)

    def test_textbook_opens_source_without_using_rph_credit(self):
        url = "https://fliphtml5.com/itzsi/xpxe/BUKU_TEKS_SAINS_TAHUN_4/"
        self.page.evaluate("""(url)=>{
          const original=window.fetch;
          window.fetch=async (target,options)=>{
            if(!String(target).includes('/api/web/rph/extra-materials?'))return original(target,options);
            return new Response(JSON.stringify({items:[{
              type:'textbook',title:'Buku Teks Sains Tahun 4 • m/s 2–4',url
            }]}),{status:200,headers:{'content-type':'application/json'}});
          };
        }""", url)
        self.page.locator("#show-materials").click()
        book = self.page.locator("#materials-list li").filter(has_text="m/s 2–4")
        link = book.get_by_role("link", name="Buka Buku Teks")
        self.assertEqual(link.get_attribute("href"), url)
        self.assertEqual(link.get_attribute("target"), "_blank")
        self.assertIn("10 daripada 10 janaan", self.page.locator("#account-access").inner_text())
        self.assertEqual(self.page.evaluate("window.__sainsRequests.length"), 0)


if __name__=="__main__":
    unittest.main()
