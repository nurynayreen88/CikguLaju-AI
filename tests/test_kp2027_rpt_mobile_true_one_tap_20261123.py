"""Mobile Chromium: all 6 approved KP2027 Year 1 combined RPT files download on one tap.

Offline, synthetic catalog and same-origin HTTP responses. Uses actual SHA-checked
RPT PDF/Word source bytes; never needs accounts, Supabase or production login.
"""
from __future__ import annotations

import hashlib
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from web.kp2027_year1_rpt_combined import SUBJECTS, document, ready

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web_v1_static_preview"
HOST = "https://kp2027-direct-download.test"
RPT_PREFIX = "/api/rpt/2027/kp2027/tahun-1/gabungan/"
LABELS = {
    "matematik": "Matematik",
    "alam_dan_manusia": "Alam dan Manusia",
    "bahasa_melayu": "Bahasa Melayu",
}


class KP2027OneTapMobileRPT(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert ready(), "Source-locked KP2027 RPT bundle missing"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def _run(self, *, available=True):
        ctx = self.browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True, has_touch=True,
            accept_downloads=True,
        )
        page = ctx.new_page()
        paths = []
        pages = []
        downloads = []
        page.on("download", lambda download: downloads.append(download.suggested_filename))
        ctx.on("page", lambda p: pages.append(p))

        def mock(route):
            path = urlsplit(route.request.url).path
            paths.append(path)
            if path == "/":
                return route.fulfill(
                    status=200, content_type="text/html",
                    body=(WEB / "index.html").read_bytes())
            if path == "/api/rpt/2027/catalog":
                return route.fulfill(json={
                    "subjects": [],
                    "personalization_allowed": False,
                    "kp2027_rpt_available": [
                        {
                            "code": code, "label": LABELS[code], "year": 1,
                            "kp2027_combined": True,
                            "pdf_ready": True, "docx_ready": True,
                            "download_enabled": available,
                            "status": "RPT SEMAKAN PELAKSANAAN",
                        } for code in SUBJECTS
                    ],
                })
            if path.startswith(RPT_PREFIX):
                selected = path[len(RPT_PREFIX):]
                if "." not in selected:
                    return route.fulfill(status=404, body="Unsupported path")
                code, fmt = selected.rsplit(".", 1)
                if not available or code not in SUBJECTS or fmt not in {"pdf", "docx"}:
                    return route.fulfill(status=403, content_type="application/json",
                                         body='{"error":"Akses diperlukan"}')
                payload, name, digest = document(code, fmt)
                assert hashlib.sha256(payload).hexdigest() == digest
                mime = ("application/pdf" if fmt == "pdf" else
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                return route.fulfill(
                    status=200,
                    headers={
                        "Content-Type": mime,
                        "Content-Disposition": 'attachment; filename="' + name + '"',
                        "Cache-Control": "private, no-store",
                        "X-RPT-Source-SHA256": digest,
                    },
                    body=payload)
            if path.startswith("/assets/"):
                asset = WEB / path.rsplit("/", 1)[-1]
                if asset.is_file():
                    mime = ("application/javascript" if asset.suffix == ".js" else
                            "application/json" if asset.suffix == ".json" else
                            "application/octet-stream")
                    return route.fulfill(status=200, content_type=mime,
                                         body=asset.read_bytes())
            return route.fulfill(status=404, body="No fixture")

        page.route(HOST + "/**", mock)
        try:
            page.goto(HOST + "/", wait_until="domcontentloaded")
            page.evaluate("""async () => {
                document.querySelector("main.panel").hidden = true;
                document.querySelector("#workspace").hidden = false;
                document.querySelector("#view-rpt").hidden = false;
                await loadRptCatalog();
            }""")
            page.locator("#rpt-curriculum").select_option("kp2027")
            page.locator("#rpt-year").select_option("1")

            for subject in SUBJECTS:
                with self.subTest(subject=subject, available=available):
                    page.evaluate("""(subject) => {
                        const select=document.getElementById("rpt-subject");
                        select.value=subject;
                        select.dispatchEvent(new Event("change"));
                    }""", subject)
                    pdf = page.locator("#rpt-download-mobile")
                    word = page.locator("#rpt-download-word")
                    base = RPT_PREFIX + subject + "."
                    if not available:
                        self.assertTrue(pdf.is_hidden())
                        self.assertTrue(word.is_hidden())
                        self.assertTrue(page.locator("#rpt-download").is_hidden())
                        self.assertNotIn(base + "pdf", paths)
                        continue

                    self.assertTrue(pdf.is_visible())
                    self.assertTrue(word.is_visible())
                    self.assertTrue(page.locator("#rpt-download").is_hidden())
                    self.assertEqual(pdf.get_attribute("href"), base + "pdf")
                    self.assertEqual(word.get_attribute("href"), base + "docx")
                    self.assertEqual(pdf.get_attribute("download"), "")
                    self.assertEqual(word.get_attribute("download"), "")
                    self.assertIsNone(pdf.get_attribute("target"))
                    self.assertIsNone(word.get_attribute("target"))

                    for fmt, control in (("pdf", pdf), ("docx", word)):
                        with self.subTest(subject=subject, file_format=fmt):
                            with page.expect_download(timeout=20000) as captured:
                                control.tap()
                            download = captured.value
                            payload, expected_name, digest = document(subject, fmt)
                            self.assertEqual(download.suggested_filename, expected_name)
                            self.assertEqual(hashlib.sha256(Path(download.path()).read_bytes()).hexdigest(), digest)
                            self.assertEqual(page.url, HOST + "/")
                            self.assertEqual(len(ctx.pages), 1, "Unexpected extra tab/viewer")
                            self.assertIn(base + fmt, paths)
            self.assertEqual(len(pages), 0, "A popup must never be created")
            self.assertEqual(len(downloads), 6 if available else 0)
        finally:
            ctx.close()

    def test_six_word_pdf_files_download_without_viewer_or_popup(self):
        self._run(available=True)

    def test_unavailable_catalog_never_exposes_any_download(self):
        self._run(available=False)


if __name__ == "__main__":
    unittest.main()
