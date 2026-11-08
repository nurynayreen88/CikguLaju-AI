"""End-to-end mobile Chromium RPT profile stamping with *synthetic* login data.

Serve the REAL Web UI, PDF-lib, 2027 PDF, SHA-locked cover layout, and
browser personalization script using mocked same-origin HTTP responses.
No user account, Supabase, payments, Telegram or production network.
"""
from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PDF_ROOT=ROOT/"rpt_2027/web_2027_pdfs"
WEB=ROOT/"web_v1_static_preview"
HOST="https://cikgulaju-rpt-browser.test"
PAIR="pendidikan_islam:4"
manifest=json.loads((PDF_ROOT/"manifest.json").read_text("utf-8"))
entry=manifest["files"][PAIR]
ORIGINAL=(PDF_ROOT/entry["path"]).read_bytes()
LAYOUT=(PDF_ROOT/"original_cover_layout_verified.json").read_bytes()
assert hashlib.sha256(ORIGINAL).hexdigest()==entry["sha256"]


class RealMobilePersonalizedDownload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright=sync_playwright().start()
        cls.browser=cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def run_case(self,bad_hash=False):
        context=self.browser.new_context(
            viewport={"width":390,"height":844},is_mobile=True,has_touch=True
        )
        page=context.new_page()
        requests=[]

        def mock(route):
            url=route.request.url
            path=urlsplit(url).path
            requests.append((route.request.method,path))
            if path=="/":
                return route.fulfill(status=200,content_type="text/html",
                                     body=(WEB/"index.html").read_text("utf-8"))
            if path=="/assets/pdf-lib.min.js":
                return route.fulfill(status=200,content_type="application/javascript",
                                     body=(WEB/"pdf-lib.min.js").read_bytes())
            if path=="/assets/rpt-personalize.js":
                return route.fulfill(status=200,content_type="application/javascript",
                                     body=(WEB/"rpt-personalize.js").read_text("utf-8"))
            if path=="/assets/rpt-original-cover-layout.json":
                return route.fulfill(status=200,content_type="application/json",body=LAYOUT)
            if path=="/api/web/teacher/profile":
                return route.fulfill(status=200,content_type="application/json",
                    body=json.dumps({"profile":{
                        "school_name":"Sekolah Kebangsaan Laju",
                        "display_name":"Cikgu Ujian"
                    }},ensure_ascii=False))
            if path=="/api/web/teacher/school-logo":
                return route.fulfill(status=404,content_type="application/json",
                    body='{"error":"Logo sekolah belum dimuat naik"}')
            if path=="/api/rpt/2027/all/pendidikan_islam/4.pdf":
                return route.fulfill(status=200,content_type="application/pdf",
                    headers={"X-RPT-Source-SHA256":"0"*64 if bad_hash else entry["sha256"],
                             "Cache-Control":"no-store, private"},
                    body=ORIGINAL)
            # Unrelated preview/analytics assets are not used in this test.
            if path.startswith("/assets/") and path.endswith(".js"):
                local=WEB/path.rsplit("/",1)[-1]
                if local.is_file():
                    return route.fulfill(status=200,content_type="application/javascript",
                                         body=local.read_bytes())
                return route.fulfill(status=200,content_type="application/javascript",body="")
            return route.fulfill(status=404,content_type="text/plain",body="not used")

        page.route(HOST+"/**",mock)
        popup=None
        try:
            page.goto(HOST+"/",wait_until="domcontentloaded")
            page.evaluate("""() => {
                document.querySelector('main.panel').hidden=true;
                document.querySelector('#workspace').hidden=false;
                document.querySelector('#view-rpt').hidden=false;
                rptCatalog={allowed:true,subjects:[{
                    code:'pendidikan_islam',label:'Pendidikan Islam',
                    years:[{year:4,status:'DRAF',pdf_ready:true,download_enabled:true}]
                }]};
                const s=document.querySelector('#rpt-subject');
                s.replaceChildren(new Option('Pilih Subjek',''),
                                  new Option('Pendidikan Islam','pendidikan_islam'));
                s.value='pendidikan_islam';
                const y=document.querySelector('#rpt-year');
                y.replaceChildren(new Option('Tahun 4','4'));
                y.value='4';
                refreshRptDownload();
            }""")
            with page.expect_popup(timeout=10000) as next_page:
                page.locator("#rpt-download-mobile").tap()
            popup=next_page.value
            if bad_hash:
                page.wait_for_function(
                    "() => document.querySelector('#rpt-status').textContent.includes('Checksum PDF tidak sepadan')",
                    timeout=15000
                )
                self.assertTrue(popup.is_closed())
            else:
                page.wait_for_function(
                    "() => document.querySelector('#rpt-status').textContent.includes('PDF RPT dibuka di tab baharu')",
                    timeout=30000
                )
                popup.wait_for_url(re.compile(r"^blob:"),timeout=12000)
                self.assertTrue(popup.url.startswith("blob:"),popup.url)
                self.assertFalse(popup.is_closed())
            self.assertIn(("GET","/api/web/teacher/profile"),requests)
            self.assertIn(("GET","/api/rpt/2027/all/pendidikan_islam/4.pdf"),requests)
            self.assertIn(("GET","/assets/rpt-original-cover-layout.json"),requests)
            self.assertIn(("GET","/api/web/teacher/school-logo"),requests)
        finally:
            if popup and not popup.is_closed():
                popup.close()
            context.close()

    def test_real_mobile_click_opens_personalized_pdf_viewer(self):
        self.run_case()

    def test_invalid_source_sha_never_issues_a_personalized_pdf(self):
        self.run_case(bad_hash=True)


if __name__=="__main__":
    unittest.main()
