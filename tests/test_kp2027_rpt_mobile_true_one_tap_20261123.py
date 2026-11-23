"""Mobile Chromium: 6 KP2027 Year 1 RPT files download from a real local HTTP server.

No browser-route emulation of file downloads: actual HTTP Content-Disposition
responses are streamed from the SHA-pinned approved bundle. Accounts, paid
status, databases and production URLs are never accessed.
"""
from __future__ import annotations

from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import unittest
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
from web.kp2027_year1_rpt_combined import SUBJECTS, document, ready

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web_v1_static_preview"
RPT_PREFIX = "/api/rpt/2027/kp2027/tahun-1/gabungan/"
LABELS = {
    "matematik": "Matematik",
    "alam_dan_manusia": "Alam dan Manusia",
    "bahasa_melayu": "Bahasa Melayu",
}


class LocalRPTServer(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_bytes(self, body, mime, *, disposition=None, status=200):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "private, no-store")
        if disposition:
            self.send_header("Content-Disposition", disposition)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        self.server.paths.append(path)
        if path == "/":
            return self.send_bytes((WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/api/rpt/2027/catalog":
            payload = {
                "subjects": [],
                "personalization_allowed": self.server.paid,
                "kp2027_rpt_available": [
                    {"code": code, "label": LABELS[code], "year": 1,
                     "kp2027_combined": True,
                     "pdf_ready": True, "docx_ready": True,
                     "docx_download_enabled": self.server.paid,
                     "download_enabled": self.server.allowed,
                     "status": "RPT SEMAKAN PELAKSANAAN"}
                    for code in SUBJECTS
                ],
            }
            return self.send_bytes(
                json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json")
        if path.startswith(RPT_PREFIX):
            suffix = path[len(RPT_PREFIX):]
            if "." not in suffix:
                return self.send_bytes(b"Not found", "text/plain", status=404)
            code, fmt = suffix.rsplit(".", 1)
            if not self.server.allowed or (fmt == "docx" and not self.server.paid):
                return self.send_bytes(b'{"error":"Akses diperlukan"}',
                                       "application/json", status=403)
            if code not in SUBJECTS or fmt not in {"pdf", "docx"}:
                return self.send_bytes(b"Not found", "text/plain", status=404)
            payload, filename, digest = document(code, fmt)
            assert sha256(payload).hexdigest() == digest
            mime = ("application/pdf" if fmt == "pdf" else
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            return self.send_bytes(
                payload, mime,
                disposition='attachment; filename="' + filename + '"')
        if path.startswith("/assets/"):
            asset = WEB / path.rsplit("/", 1)[-1]
            if asset.is_file():
                mime = ("application/javascript" if asset.suffix == ".js" else
                        "application/json" if asset.suffix == ".json" else
                        "application/octet-stream")
                return self.send_bytes(asset.read_bytes(), mime)
        return self.send_bytes(b"Not found", "text/plain", status=404)


class KP2027OneTapMobileRPT(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert ready(), "Source-locked KP2027 RPT bundle missing"
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), LocalRPTServer)
        cls.server.allowed = True
        cls.server.paid = True
        cls.server.paths = []
        cls.host = "http://127.0.0.1:" + str(cls.server.server_address[1])
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=10)

    def _run(self, *, available, paid=True):
        self.server.allowed = available
        self.server.paid = paid
        self.server.paths.clear()
        ctx = self.browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True, has_touch=True,
            accept_downloads=True)
        page = ctx.new_page()
        pages = []
        downloads = []
        page.on("download", lambda item: downloads.append(item.suggested_filename))
        ctx.on("page", lambda p: pages.append(p))
        try:
            page.goto(self.host + "/", wait_until="domcontentloaded")
            page.evaluate("""async () => {
                document.querySelector("main.panel").hidden = true;
                document.querySelector("#workspace").hidden = false;
                document.querySelector("#view-rpt").hidden = false;
                await loadRptCatalog();
            }""")
            page.locator("#rpt-curriculum").select_option("kp2027")
            page.locator("#rpt-year").select_option("1")
            for subject in SUBJECTS:
                page.evaluate("""(code) => {
                    const select = document.getElementById("rpt-subject");
                    select.value = code;
                    select.dispatchEvent(new Event("change"));
                }""", subject)
                pdf = page.locator("#rpt-download-mobile")
                word = page.locator("#rpt-download-word")
                base = RPT_PREFIX + subject + "."
                if not available:
                    self.assertTrue(pdf.is_hidden())
                    self.assertTrue(word.is_hidden())
                    self.assertTrue(page.locator("#rpt-download").is_hidden())
                    self.assertNotIn(base + "pdf", self.server.paths)
                    continue

                self.assertTrue(pdf.is_visible())
                self.assertEqual(word.is_visible(), paid)
                self.assertTrue(page.locator("#rpt-download").is_hidden())
                self.assertEqual(pdf.get_attribute("href"), base + "pdf")
                self.assertEqual(pdf.get_attribute("download"), document(subject, "pdf")[1])
                self.assertIsNone(pdf.get_attribute("target"))
                if paid:
                    self.assertEqual(word.get_attribute("href"), base + "docx")
                    self.assertEqual(word.get_attribute("download"), document(subject, "docx")[1])
                    self.assertIsNone(word.get_attribute("target"))
                else:
                    self.assertIsNone(word.get_attribute("href"))
                    self.assertIsNone(word.get_attribute("download"))
                    self.assertIn("Rakan Pembangun", page.locator("#rpt-status").inner_text())
                    result=ctx.request.get(self.host+base+"docx")
                    self.assertEqual(result.status,403)
                for fmt, control in ([("pdf", pdf), ("docx", word)] if paid
                                     else [("pdf", pdf)]):
                    with self.subTest(subject=subject, file_format=fmt):
                        with page.expect_download(timeout=25000) as capture:
                            control.tap()
                        item = capture.value
                        payload, expected_name, digest = document(subject, fmt)
                        self.assertEqual(item.suggested_filename, expected_name)
                        self.assertEqual(sha256(Path(item.path()).read_bytes()).hexdigest(), digest)
                        self.assertEqual(page.url, self.host + "/")
                        self.assertEqual(len(ctx.pages), 1)
                        self.assertIn(base + fmt, self.server.paths)

            self.assertEqual(len(pages), 0, "No extra viewer or popup tab")
            self.assertEqual(len(downloads), (6 if paid else 3) if available else 0)
        finally:
            ctx.close()

    def test_all_six_word_pdf_downloads_are_complete_and_one_tap(self):
        self._run(available=True)

    def test_free_user_gets_pdf_not_word_and_direct_word_request_is_403(self):
        self._run(available=True, paid=False)

    def test_unavailable_status_hides_all_six_downloads(self):
        self._run(available=False)


if __name__ == "__main__":
    unittest.main()
