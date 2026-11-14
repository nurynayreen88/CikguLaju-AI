"""Browser RPH trial balance UI, no real login or credit use."""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

HTML=(Path(__file__).resolve().parents[1]/"web_v1_static_preview/index.html").as_uri()


class BrowserSharedTrialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright=sync_playwright().start()
        cls.browser=cls.playwright.chromium.launch(headless=True)
    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def page(self,width=375):
        page=self.browser.new_page(viewport={"width":width,"height":840})
        page.goto(HTML,wait_until="domcontentloaded")
        page.evaluate("""() => {
          document.querySelector('main.panel').hidden=true;
          document.querySelector('#workspace').hidden=false;
          document.querySelector('#teacher-info').hidden=false;
          curriculum.value='kssr';
          selectCurriculum();
          year.value='4';
          for (const [id,value] of [['subject','ENGLISH'],['unit','Where are you from?'],
                                    ['lesson','e-4-001']]) {
             let e=document.getElementById(id);
             e.add(new Option(value,value));e.value=value;
          }
          verifiedRphKey=currentRphLessonKey();
          showRphAction();
        }""")
        return page

    def test_phone_trial_10_down_to_one_and_zero(self):
        page=self.page()
        try:
            for balance in (10,7,1):
                page.evaluate("""(n)=>applyRphAccount({
                  rph_access_mode:'trial',rph_trial_remaining:n
                })""",balance)
                self.assertIn(str(balance)+" daripada 10 janaan",page.locator("#account-access").inner_text())
                self.assertTrue(page.locator("#rph-word").is_enabled())
                self.assertTrue(page.locator("#rph-pdf").is_enabled())
                self.assertFalse(page.locator("#rph-download-actions").get_attribute("hidden") is not None)
            page.evaluate("""() => applyRphAccount({
              rph_access_mode:'exhausted',rph_trial_remaining:0
            })""")
            self.assertIn("0 daripada 10",page.locator("#account-access").inner_text())
            self.assertIn("Rakan Pembangun",page.locator("#account-access").inner_text())
            self.assertTrue(page.locator("#rph-download-actions").get_attribute("hidden") is not None)
            self.assertFalse(page.locator("#rph-word").is_enabled())
            self.assertFalse(page.locator("#rph-pdf").is_enabled())
            self.assertEqual(page.evaluate("document.documentElement.scrollWidth"),375)
        finally:page.close()

    def test_active_partner_always_unlimited_and_unknown_balance_closed(self):
        page=self.page()
        try:
            page.evaluate("""() => applyRphAccount({rph_access_mode:'paid',
              rph_trial_remaining:0,status:'Rakan Pembangun',
              access:'Tanpa had seumur hidup'})""")
            self.assertIn("Tanpa had seumur hidup",page.locator("#account-access").inner_text())
            self.assertTrue(page.locator("#rph-word").is_enabled())
            page.evaluate("""() => applyRphAccount({rph_access_mode:'unavailable',
              rph_trial_remaining:null})""")
            self.assertFalse(page.locator("#rph-word").is_enabled())
            self.assertIn("belum dapat disahkan",page.locator("#account-access").inner_text())
        finally:page.close()

    def test_copy_states_rpt_download_free_profile_print_paid_trial_shared(self):
        page=self.page(360)
        try:
            html=page.content()
            self.assertIn("10 janaan RPH percuma dikongsi antara Web dan Telegram",html)
            self.assertIn("Muat turun RPT adalah",html)
            self.assertIn("percuma untuk semua pengguna berdaftar",html)
            self.assertIn("Cetakan berprofil hanya untuk Rakan Pembangun atau langganan aktif",html)
        finally:page.close()

if __name__=="__main__":
    unittest.main()
