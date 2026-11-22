"""End-to-end one-tap mobile Chromium RPT profile stamping with *synthetic* login data.

Serve the REAL Web UI, PDF-lib, 2027 PDF, SHA-locked cover layout, and
browser personalization script using mocked same-origin HTTP responses.
No user account, Supabase, payments, Telegram or production network.
"""
from __future__ import annotations

import hashlib
import json
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

    def run_case(self,bad_hash=False,paid=True):
        context=self.browser.new_context(
            viewport={"width":390,"height":844},is_mobile=True,has_touch=True,
            accept_downloads=True
        )
        page=context.new_page()
        requests=[]
        downloads=[]
        def observe_download(download):
            downloads.append(download.suggested_filename)
        page.on("download",observe_download)
        context.on("page",lambda new_page:new_page.on("download",observe_download))

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
            if path=="/api/rpt/2027/catalog":
                return route.fulfill(json={"personalization_allowed":paid,"subjects":[{
                    "code":"pendidikan_islam","label":"Pendidikan Islam",
                    "years":[{"year":4,"pdf_ready":True,"download_enabled":True}]
                }]})
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
                             "Cache-Control":"no-store, private",
                             "Content-Disposition":'attachment; filename="CIKGULAJU_RPT_PENDIDIKAN_ISLAM_TAHUN_4_2027_DRAF.pdf"',
                             "X-RPT-Personalization-Allowed":"1" if paid else "0"},
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
        try:
            page.goto(HOST+"/",wait_until="domcontentloaded")
            page.evaluate("""async () => {
                document.querySelector('main.panel').hidden=true;
                document.querySelector('#workspace').hidden=false;
                document.querySelector('#view-rpt').hidden=false;
                await loadRptCatalog();
            }""")
            page.locator("#rpt-curriculum").select_option("kssr")
            page.locator("#rpt-year").select_option("4")
            subject_search=page.get_by_role("combobox",name="Subjek",exact=True)
            subject_search.tap()
            subject_search.fill("islam")
            page.get_by_role("option",name="Pendidikan Islam").tap()
            if bad_hash:
                # Never download invalid source bytes; no page or popup.
                page.locator("#rpt-download").tap()
                page.wait_for_function(
                    "() => document.querySelector('#rpt-status').textContent.includes('Checksum PDF tidak sepadan')",
                    timeout=15000
                )
                self.assertEqual(downloads,[])
            else:
                # The FIRST tap downloads the final, verified file directly.
                # There must be no second "Simpan PDF" button or popup.
                with page.expect_download(timeout=30000) as item:
                    page.locator("#rpt-download" if paid else "#rpt-download-mobile").tap()
                downloaded=item.value
                if paid:
                    page.wait_for_function(
                        "() => document.querySelector('#rpt-status').textContent.includes('PDF RPT berjaya dimuat turun')",
                        timeout=30000
                    )
                data=Path(downloaded.path()).read_bytes()
                output={
                    "bytes":len(data),
                    "header":data[:5],
                    "filename":downloaded.suggested_filename,
                    "sha":hashlib.sha256(data).hexdigest(),
                }
                self.assertGreater(output["bytes"],8000)
                self.assertEqual(output["header"],b"%PDF-")
                self.assertEqual(downloads,[output["filename"]])
                if paid:
                    self.assertNotEqual(output["sha"],entry["sha256"])
                    self.assertIn("PENDIDIKAN_ISLAM_TAHUN_4_2027_ISI_PROFIL.pdf",output["filename"])
                else:
                    self.assertEqual(output["sha"],entry["sha256"])
                    self.assertIn("PENDIDIKAN_ISLAM_TAHUN_4_2027_DRAF.pdf",output["filename"])
            self.assertEqual(len(context.pages),1)
            self.assertEqual(page.locator("#rpt-prepared-manual-link").count(),0)
            if bad_hash or not paid:
                self.assertNotIn(("GET","/api/web/teacher/profile"),requests)
                self.assertNotIn(("GET","/api/web/teacher/school-logo"),requests)
            else:
                self.assertIn(("GET","/api/web/teacher/profile"),requests)
            self.assertIn(("GET","/api/rpt/2027/all/pendidikan_islam/4.pdf"),requests)
            if not bad_hash and paid:
                self.assertIn(("GET","/assets/rpt-original-cover-layout.json"),requests)
                self.assertIn(("GET","/api/web/teacher/school-logo"),requests)
            else:
                self.assertNotIn(("GET","/assets/rpt-original-cover-layout.json"),requests)
        finally:
            context.close()

    def test_real_mobile_click_downloads_personalized_pdf_immediately(self):
        self.run_case()

    def test_invalid_source_sha_never_issues_a_personalized_pdf(self):
        self.run_case(bad_hash=True)

    def test_free_user_receives_identical_source_and_profile_is_never_read(self):
        self.run_case(paid=False)


if __name__=="__main__":
    unittest.main()
