"""Phone browser tests: native class dropdown, start/end time and pupil count."""
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

HTML=(Path(__file__).resolve().parents[1]/"web_v1_static_preview/index.html").as_uri()


class RphFieldsBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright=sync_playwright().start()
        cls.browser=cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.playwright.stop()

    def _page(self,width):
        page=self.browser.new_page(viewport={"width":width,"height":840})
        page.goto(HTML,wait_until="domcontentloaded")
        page.evaluate("""() => {
          document.querySelector('main.panel').hidden=true;
          document.querySelector('#workspace').hidden=false;
          document.querySelector('#teacher-info').hidden=false;
          document.querySelector('#year').value='4';
          for (const [id,value] of [['subject','ENGLISH'],['unit','Unit 1'],['lesson','L001']]) {
            const element=document.getElementById(id);
            element.add(new Option(value,value));
            element.value=value;
          }
          verifiedRphKey=currentRphLessonKey();
          showRphAction();
        }""")
        return page

    def test_dropdown_and_metadata_fields_fit_phone_screen(self):
        for width in (320,360,375,390,430,760):
            with self.subTest(width=width):
                page=self._page(width)
                try:
                    self.assertEqual(page.locator("#teacher-class").evaluate("(e)=>e.tagName"),"SELECT")
                    self.assertTrue(page.get_by_label("Waktu Mula").is_visible())
                    self.assertTrue(page.get_by_label("Waktu Tamat").is_visible())
                    self.assertTrue(page.get_by_label("Bilangan Murid").is_visible())
                    right=page.locator("#teacher-info").evaluate("""e=>({
                        width:e.getBoundingClientRect().width,
                        all:[...e.querySelectorAll('select,input')].map(x=>({
                            id:x.id,right:x.getBoundingClientRect().right,
                            left:x.getBoundingClientRect().left
                        }))
                    })""")
                    self.assertTrue(all(x["right"]<=width+1 for x in right["all"]),right)
                    self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"),width+1)
                finally:
                    page.close()

    def test_class_selection_manual_fallback_and_rph_query(self):
        page=self._page(360)
        try:
            page.get_by_label("Pilih Kelas").select_option("__other__")
            self.assertTrue(page.get_by_label("Nama Kelas Lain").is_visible())
            page.get_by_label("Nama Kelas Lain").fill("4 Bestari")
            page.get_by_label("Tarikh PdP").fill("2027-03-08")
            page.get_by_label("Waktu Mula").fill("07:30")
            page.get_by_label("Waktu Tamat").fill("08:30")
            page.get_by_label("Bilangan Murid").fill("32")
            result=page.evaluate("""()=>{
               const q=currentRphParams();
               return q?Object.fromEntries(q.entries()):null;
            }""")
            self.assertIsNotNone(result)
            self.assertEqual(result["teacher_class"],"4 Bestari")
            self.assertEqual(result["teacher_start"],"07:30")
            self.assertEqual(result["teacher_end"],"08:30")
            self.assertEqual(result["teacher_students"],"32")
            self.assertEqual(result["teacher_date"],"2027-03-08")
            self.assertFalse(page.locator("#rph-download-actions").get_attribute("hidden") is not None)
            page.get_by_label("Waktu Tamat").fill("07:00")
            self.assertIsNone(page.evaluate("currentRphParams()"))
            self.assertTrue(page.locator("#rph-download-actions").get_attribute("hidden") is not None)
            page.get_by_label("Waktu Tamat").fill("08:30")
            page.get_by_label("Bilangan Murid").fill("201")
            self.assertIsNone(page.evaluate("currentRphParams()"))
        finally:
            page.close()


if __name__=="__main__":
    unittest.main()
