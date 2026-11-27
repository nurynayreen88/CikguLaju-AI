"""Real-browser responsive regression for CikguLaju Web navigation.

Runs against the production HTML; no credentials or live services required.
"""
from pathlib import Path
import unittest
from urllib.parse import parse_qs, urlsplit
from playwright.sync_api import expect, sync_playwright

WEB = Path(__file__).resolve().parents[1] / "web_v1_static_preview"
PAGE = (WEB / "index.html").as_uri()
HOST = "https://cikgulaju-guide.test"


class PhoneMenuLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_main_menu_is_compact_and_other_tabs_fit_when_expanded(self):
        for width in (320, 360, 375, 390, 430, 600, 760):
            with self.subTest(width=width):
                page=self.browser.new_page(viewport={"width":width,"height":820})
                try:
                    page.goto(PAGE,wait_until="domcontentloaded")
                    page.evaluate("""() => {
                      document.querySelector('main.panel').hidden = true;
                      document.querySelector('#workspace').hidden = false;
                    }""")
                    metrics=page.evaluate("""() => {
                      const menu=document.querySelector('.sidebar-menu');
                      const box=menu.getBoundingClientRect();
                      const tabs=[...menu.querySelectorAll('.sidebar-tab')].filter(tab=>tab.getClientRects().length);
                      return {
                        display:getComputedStyle(menu).display,
                        columns:getComputedStyle(menu).gridTemplateColumns,
                        scroll:menu.scrollWidth,
                        client:menu.clientWidth,
                        body:document.body.scrollWidth,
                        tabs:tabs.map(tab=>{
                          const b=tab.getBoundingClientRect();
                          return {label:tab.textContent.trim(),left:b.left,right:b.right,
                                  width:b.width,top:b.top,bottom:b.bottom};
                        }),
                        left:box.left,right:box.right
                      };
                    }""")
                    self.assertEqual(metrics["display"],"grid",metrics)
                    self.assertEqual(len(metrics["tabs"]),8,metrics)
                    self.assertLessEqual(metrics["scroll"],metrics["client"]+1,metrics)
                    self.assertLessEqual(metrics["body"],width+1,metrics)
                    for tab in metrics["tabs"]:
                        self.assertGreaterEqual(tab["left"],metrics["left"]-1,metrics)
                        self.assertLessEqual(tab["right"],metrics["right"]+1,metrics)
                        self.assertGreaterEqual(tab["width"],60,metrics)
                    # Users must be able to navigate without a swipe.
                    page.get_by_role("button",name="Profil & Akses",exact=True).click()
                    self.assertFalse(page.locator("#view-account").get_attribute("hidden") is not None)
                    self.assertEqual(page.locator('[data-web-view="account"]').get_attribute("aria-current"),"page")
                    page.get_by_role("button",name="Rakan Pembangun").click()
                    self.assertFalse(page.locator("#view-payment").get_attribute("hidden") is not None)
                    self.assertEqual(page.locator('[data-web-view="payment"]').get_attribute("aria-current"),"page")
                    # The new independent curriculum menu must be accessible at every width.
                    page.get_by_role("button",name="Dokumen Kurikulum",exact=True).click()
                    expect(page.locator("#curriculum-docs-heading")).to_be_focused()
                    expect(page.locator('[data-web-view="curriculum-docs"]')).to_have_attribute("aria-current","page")
                    page.locator("#curriculum-docs-type").select_option("kp2027")
                    expect(page.locator("#curriculum-kp2027-list li:visible")).to_have_count(5)
                    expect(page.locator("#curriculum-kp2027-list li:visible small").filter(has_text="PDF koleksi CikguLaju")).to_have_count(5)
                    expect(page.locator("#curriculum-kp2027-list button.curriculum-direct-download")).to_have_count(5)
                    expect(page.get_by_role("button",name="Download DK Bahasa Melayu SK Tahun 1",exact=True)).to_have_attribute("data-download-url","https://drive.usercontent.google.com/download?id=18TRqIUfNPsnyV-G_hk2BRpfExgZhyhv-&export=download&confirm=t")
                    expect(page.locator("#curriculum-kp2027-list li a")).to_have_count(0)
                    page.evaluate("""() => {
                        window.curriculumDownloadClicks=[];
                        const nativeClick=HTMLAnchorElement.prototype.click;
                        HTMLAnchorElement.prototype.click=function(){
                            if(this.href.startsWith("https://drive.usercontent.google.com/download?")){
                                window.curriculumDownloadClicks.push({url:this.href,target:this.target,download:this.hasAttribute("download")});
                            }else nativeClick.call(this);
                        };
                    }""")
                    page.get_by_role("button",name="Download DK Bahasa Melayu SK Tahun 1",exact=True).click()
                    self.assertEqual(page.evaluate("window.curriculumDownloadClicks"),[{
                        "url":"https://drive.usercontent.google.com/download?id=18TRqIUfNPsnyV-G_hk2BRpfExgZhyhv-&export=download&confirm=t",
                        "target":"","download":True}])
                    expect(page.locator("#curriculum-docs-kp2027")).not_to_contain_text("penataran",ignore_case=True)
                    expect(page.locator("#curriculum-kp2027-ppd-list")).to_have_count(0)
                    page.locator("#curriculum-docs-type").select_option("kssr")
                    expect(page.locator("#curriculum-docs-kssr-list li:visible")).to_have_count(156)
                    expect(page.locator("#curriculum-docs-kssr-list button.curriculum-direct-download")).to_have_count(137)
                    page.locator("#curriculum-docs-year").select_option("6")
                    page.locator("#curriculum-docs-subject").select_option("Matematik SJKC")
                    expect(page.locator("#curriculum-docs-kssr-list li:visible")).to_have_count(1)
                    expect(page.locator("#curriculum-docs-kssr-list li:visible .curriculum-doc-name")).to_have_text("DSKP Matematik SJKC Tahun 6")
                    expect(page.locator("#curriculum-docs-kssr-list li:visible button")).to_have_attribute("data-download-url","https://drive.usercontent.google.com/download?id=1dMLgOsc-grs4fR2WSvLNDk45Dtqh_yY_&export=download&confirm=t")
                    page.locator("#curriculum-docs-subject").select_option("Bahasa Cina SJKC")
                    expect(page.locator("#curriculum-docs-kssr-list li:visible .curriculum-doc-name")).to_have_text("DSKP Bahasa Cina SJKC Tahun 6")
                    page.locator("#curriculum-docs-year").select_option("1")
                    expect(page.locator("#curriculum-docs-kssr-list li:visible .curriculum-doc-name")).to_have_text("DSKP Bahasa Cina SJKC Tahun 1")
                    page.locator("#curriculum-docs-subject").select_option("Bahasa Cina SK")
                    page.locator("#curriculum-docs-year").select_option("3")
                    expect(page.locator("#curriculum-docs-kssr-list li:visible .curriculum-doc-name")).to_have_text("DSKP Bahasa Cina SK Tahun 3")
                    page.locator("#curriculum-docs-subject").select_option("Bahasa Tamil SK")
                    page.locator("#curriculum-docs-year").select_option("6")
                    expect(page.locator("#curriculum-docs-kssr-list li:visible a")).to_have_text("DSKP Bahasa Tamil SK Tahun 6")
                    expect(page.locator("#curriculum-docs-kssr-list li:visible small")).to_have_text("(salinan PDF sumber luar)")
                    page.locator("#curriculum-docs-year").select_option("1")
                    page.locator("#curriculum-docs-subject").select_option("Bahasa Iban")
                    expect(page.locator("#curriculum-docs-kssr-list li:visible .curriculum-doc-name")).to_have_text("DSKP Bahasa Iban Tahun 1")
                    expect(page.locator("#curriculum-docs-match-count")).to_have_text("1 pautan sumber")
                    page.locator("#curriculum-docs-type").select_option("dpk")
                    expect(page.locator("#curriculum-docs-kssr")).to_be_hidden()
                    expect(page.locator("#curriculum-docs-dpk")).to_be_visible()
                    expect(page.locator("#curriculum-docs-dpk button.curriculum-direct-download")).to_have_count(11)
                    page.locator("#curriculum-docs-type").select_option("pk")
                    expect(page.locator("#curriculum-pk-list li:visible")).to_have_count(54)
                    expect(page.locator("#curriculum-pk-list button.curriculum-direct-download")).to_have_count(12)
                    page.locator("#curriculum-pk-year").select_option("3")
                    expect(page.locator("#curriculum-pk-list li:visible")).to_have_count(6)
                    page.locator("#curriculum-pk-subject").select_option("Pengurusan Kehidupan")
                    expect(page.locator("#curriculum-pk-list li:visible")).to_have_text("DSKP Pengurusan Kehidupan Tahun 3")
                    page.locator("#curriculum-pk-year").select_option("4")
                    expect(page.locator("#curriculum-pk-list li:visible .curriculum-doc-name")).to_have_text("DSKP Pengurusan Kehidupan Tahun 4")
                    expect(page.locator("#curriculum-pk-count")).to_have_text("1 pautan sumber")
                    self.assertLessEqual(page.evaluate("document.body.scrollWidth"),width+1)
                    page.get_by_role("button",name="Rakan Pembangun").click()
                    expect(page.locator("#view-curriculum-docs")).to_be_hidden()
                    page.get_by_role("button",name="Kalendar Akademik",exact=True).click()
                    expect(page.locator("#calendar2027-heading")).to_be_focused()
                    expect(page.locator("#view-calendar")).to_be_visible()
                    expect(page.locator("#view-rpt")).to_be_hidden()
                    expect(page.locator('[data-web-view="calendar"]')).to_have_attribute("aria-current","page")
                    page.get_by_role("button",name="Rakan Pembangun").click()
                    expect(page.locator("#view-calendar")).to_be_hidden()
                    more=page.locator("#sidebar-more")
                    self.assertFalse(more.evaluate("(node)=>node.open"))
                    expect(page.get_by_role("button",name="Rekod PBD")).to_be_hidden()
                    more.locator("summary").focus()
                    page.keyboard.press("Enter")
                    self.assertTrue(more.evaluate("(node)=>node.open"))
                    self.assertLessEqual(more.evaluate("(node)=>node.scrollWidth"),width)
                    for tab in more.locator('.sidebar-tab:not([hidden])').all():
                        expect(tab).to_be_visible()
                        box=tab.bounding_box()
                        self.assertGreaterEqual(box["x"],0)
                        self.assertLessEqual(box["x"]+box["width"],width+1)
                    expect(more.get_by_text("Akan Datang",exact=True)).to_have_count(3)
                    expect(more.locator("#web-admin-tab")).to_be_hidden()
                    expect(more.locator("#web-referral-tab")).to_be_hidden()
                    more.get_by_role("button",name="Rekod PBD").click()
                    expect(page.locator("#view-pbd-heading")).to_be_focused()
                    expect(more.get_by_role("button",name="Rekod PBD")).to_have_attribute("aria-current","page")
                    page.get_by_role("button",name="Panduan",exact=True).click()
                    self.assertFalse(more.evaluate("(node)=>node.open"))
                finally:
                    page.close()

    def test_login_opens_guide_and_shortcuts_use_normal_navigation(self):
        for width in (390,1200):
            with self.subTest(width=width):
                page=self.browser.new_page(viewport={"width":width,"height":840})
                signed_in=False
                today_requests=[]

                def mock(route):
                    nonlocal signed_in
                    path=urlsplit(route.request.url).path
                    if path=="/":
                        return route.fulfill(status=200,content_type="text/html",
                                             body=(WEB/"index.html").read_bytes())
                    if path=="/api/auth/telegram/session":
                        return route.fulfill(status=200 if signed_in else 401,json={
                            "rph_access_mode":"trial","rph_trial_remaining":10})
                    if path=="/api/auth/telegram/widget":
                        signed_in=True
                        return route.fulfill(status=200,json={})
                    if path=="/api/auth/capabilities":
                        return route.fulfill(status=200,json={"telegram_widget_enabled":False})
                    if path.startswith("/assets/"):
                        asset=WEB/path.rsplit("/",1)[-1]
                        if asset.is_file():
                            return route.fulfill(status=200,path=asset)
                    if path=="/api/web/rph/hari-ini":
                        today_requests.append(path)
                    return route.fulfill(status=404,json={})

                page.route(HOST+"/**",mock)
                try:
                    page.goto(HOST+"/",wait_until="load")
                    guide=page.get_by_role("heading",name="Panduan Penggunaan")
                    expect(guide).to_be_hidden()
                    with page.expect_navigation(wait_until="load"):
                        page.evaluate("() => { void window.onCikguLajuTelegramAuth({id:123}); }")
                    expect(guide).to_be_visible()
                    nav=page.get_by_role("navigation",name="Menu utama")
                    expect(nav.get_by_role("button",name="Panduan")).to_have_attribute("aria-current","page")
                    self.assertEqual(today_requests,[])

                    for label, view, heading_id in [
                        ("Buka Profil & Akses","account","view-account-heading"),
                        ("Buka Sediakan RPH","rph","view-rph-heading"),
                        ("Buka RPT 2027","rpt","rpt2027-heading"),
                        ("Buka RPH Pantas","today","view-today-heading"),
                    ]:
                        if view=="today":
                            with page.expect_request(HOST+"/api/web/rph/hari-ini*"):
                                page.get_by_role("button",name=label).click()
                        else:
                            page.get_by_role("button",name=label).click()
                        expect(guide).to_be_hidden()
                        expect(page.locator("#"+heading_id)).to_be_focused()
                        expect(nav.locator('[data-web-view="'+view+'"]')).to_have_attribute("aria-current","page")
                        if view=="today":
                            expect(nav.get_by_role("button", name="RPH Pantas")).to_be_visible()
                            expect(nav.get_by_text("Hari Ini & Minggu Ini",exact=True)).to_be_visible()
                            expect(nav.locator('[data-web-view="today"] [aria-hidden="true"]')).to_have_text("⚡")
                        nav.get_by_role("button",name="Panduan").click()
                        expect(guide).to_be_visible()
                finally:
                    page.close()

    def test_calendar_uses_independent_free_download(self):
        import json
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from threading import Thread

        downloads=[]
        state={"ready":True}
        payload=b"%PDF-1.4\n% calendar download test\n%%EOF\n"
        filename="CikguLaju_Kalendar_2027_A2_Kemas.pdf"

        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):
                pass

            def send_body(self,status,body,content_type,attachment=None):
                self.send_response(status)
                self.send_header("Content-Type",content_type)
                self.send_header("Content-Length",str(len(body)))
                if attachment:
                    self.send_header("Content-Disposition",'attachment; filename="'+attachment+'"')
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                path=urlsplit(self.path).path
                if path=="/":
                    return self.send_body(200,(WEB/"index.html").read_bytes(),"text/html; charset=utf-8")
                if path=="/api/auth/telegram/session":
                    return self.send_body(200,json.dumps({"rph_access_mode":"trial","rph_trial_remaining":0}).encode(),"application/json")
                if path=="/api/rpt/2027/calendar/status":
                    return self.send_body(200,json.dumps(state).encode(),"application/json")
                if path=="/api/rpt/2027/calendar.pdf":
                    downloads.append(path)
                    return self.send_body(200,payload,"application/pdf",filename)
                if path.startswith("/assets/"):
                    asset=WEB/path.rsplit("/",1)[-1]
                    if asset.is_file():
                        import mimetypes
                        return self.send_body(200,asset.read_bytes(),mimetypes.guess_type(asset.name)[0] or "application/octet-stream")
                return self.send_body(404,b"{}","application/json")

        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=Thread(target=server.serve_forever,daemon=True)
        thread.start()
        origin="http://127.0.0.1:"+str(server.server_port)
        page=self.browser.new_page(viewport={"width":390,"height":820},accept_downloads=True)
        try:
            page.goto(origin+"/",wait_until="domcontentloaded")
            page.get_by_role("button",name="Kalendar Akademik",exact=True).click()
            expect(page.locator("#calendar2027-download")).to_be_visible()
            expect(page.locator("#calendar2027-status")).to_have_text("Muat turun terus tanpa menggunakan kuota RPH.")
            with page.expect_download() as info:
                page.locator("#calendar2027-download").click()
            download=info.value
            self.assertEqual(download.suggested_filename,filename)
            self.assertEqual(download.url,origin+"/api/rpt/2027/calendar.pdf")
            self.assertEqual(download.path().read_bytes(),payload)
            self.assertEqual(downloads,["/api/rpt/2027/calendar.pdf"])
            page.get_by_role("button",name="RPT 2027",exact=True).click()
            expect(page.locator("#calendar2027-download")).to_be_hidden()
            state["ready"]=False
            page.get_by_role("button",name="Kalendar Akademik",exact=True).click()
            expect(page.locator("#calendar2027-status")).to_have_text("Kalendar belum tersedia.")
            expect(page.locator("#calendar2027-download")).to_be_hidden()
        finally:
            page.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_year_one_book_references_appear_after_each_lesson_selection(self):
        page = self.browser.new_page(viewport={"width": 390, "height": 840})
        textbook = "Buku Teks Jilid 1, hlm. 1–4"
        activitybook = "Buku Aktiviti Jilid 1, hlm. 1–5"
        lesson = {"value": "PDP1", "label": "PdP 1 • Banding kuantiti melalui padanan",
                  "textbook_ref": textbook, "activitybook_ref": activitybook}
        unit = {"value": "u" + "a" * 24, "label": "Unit 1: Nombor Bulat Hingga 100"}
        options = {"subjects": [{"value": "MATH", "label": "Matematik"}],
                   "units": [unit], "pdp": [lesson]}

        def mock(route):
            request = urlsplit(route.request.url)
            if request.path == "/":
                return route.fulfill(content_type="text/html", path=WEB / "index.html")
            if request.path == "/api/auth/telegram/session":
                return route.fulfill(json={"rph_access_mode": "trial", "rph_trial_remaining": 10})
            if request.path == "/api/auth/capabilities":
                return route.fulfill(json={"telegram_widget_enabled": False})
            if request.path == "/api/options":
                kind = parse_qs(request.query).get("kind", [""])[0]
                return route.fulfill(json=options.get(kind, []))
            if request.path == "/api/web/rph/hari-ini":
                return route.fulfill(json={
                    "date": "2026-11-19", "day": "Khamis", "count": 1, "holiday_notice": "",
                    "entries": [{"year": 1, "class_name": "1 Bestari",
                                 "subject_code": "MATH", "subject": "Matematik",
                                 "start": "08:00", "end": "08:30", "can_prepare": True}],
                })
            if request.path.startswith("/assets/"):
                asset = WEB / request.path.rsplit("/", 1)[-1]
                if asset.is_file():
                    return route.fulfill(path=asset)
            return route.fulfill(status=404, json={})

        page.route("**/*", lambda route: route.abort())
        page.route(HOST + "/**", mock)
        try:
            page.goto(HOST + "/", wait_until="load")
            page.get_by_role("button", name="Buka Sediakan RPH").click()
            page.locator("#curriculum").select_option("kssr")
            page.locator("#year").select_option("1")
            page.locator("#rph-subject-search input").click()
            page.get_by_role("option", name="Matematik SK", exact=True).click()
            expect(page.locator("#unit option", has_text="Unit 1:")).to_have_count(1)
            page.locator("#unit").select_option(unit["value"])
            page.locator("#lesson").select_option("PDP1")
            expected = f"Rujukan buku: {textbook} • {activitybook}"
            expect(page.locator("#lesson-source-pages")).to_have_text(expected)
            page.locator("#lesson").select_option("")
            expect(page.locator("#lesson-source-pages")).to_be_hidden()

            page.get_by_role("navigation", name="Menu utama").get_by_role(
                "button", name="RPH Pantas").click()
            page.locator("#today-0-unit").select_option(unit["value"])
            page.locator("#today-0-lesson").select_option("PDP1")
            expect(page.locator("#today-list").get_by_text(expected, exact=True)).to_be_visible()
        finally:
            page.close()

    def test_desktop_sidebar_remains_vertical(self):
        page=self.browser.new_page(viewport={"width":1200,"height":900})
        def mock(route):
            path=urlsplit(route.request.url).path
            if path=="/":
                return route.fulfill(content_type="text/html",path=WEB/"index.html")
            if path=="/api/auth/telegram/session":
                return route.fulfill(json={"rph_access_mode":"trial","rph_trial_remaining":10})
            if path=="/api/auth/capabilities":
                return route.fulfill(json={"telegram_widget_enabled":False})
            if path=="/api/web/admin/usage":
                return route.fulfill(json={"registered_users":1})
            if path=="/api/web/admin/notifications":
                return route.fulfill(json={"items":[],"counts":{},"total":0,"more":False})
            if path.startswith("/assets/"):
                asset=WEB/path.rsplit("/",1)[-1]
                if asset.is_file():
                    return route.fulfill(path=asset)
            return route.fulfill(status=404,json={})
        page.route("**/*",lambda route:route.abort())
        page.route(HOST+"/**",mock)
        try:
            page.goto(HOST+"/",wait_until="load")
            expect(page.locator("#workspace")).to_be_visible()
            m=page.evaluate("""() => {
              const menu=document.querySelector('.sidebar-menu');
              return {display:getComputedStyle(menu).display,
                      direction:getComputedStyle(menu).flexDirection};
            }""")
            self.assertEqual(m,{"display":"flex","direction":"column"})
            self.assertFalse(page.locator("#sidebar-more").evaluate("(node)=>node.open"))
            # Use actual loaded admin JS and mocked authorized server responses.
            # The file:// fixture cannot load absolute /assets/ paths.
            page.evaluate("() => window.cikgulajuAdminInit()")
            top=page.locator("#web-admin-top")
            expect(top).to_be_visible()
            summary=top.locator(":scope > summary")
            expect(summary).to_contain_text("Pusat Admin")
            if not top.evaluate("(node)=>node.open"):
                summary.click()
            expect(page.locator("#web-admin-heading")).to_be_visible()
            expect(page.locator("#web-admin-tab")).to_be_hidden()
            summary.click()
            expect(page.locator("#web-admin-heading")).to_be_hidden()
        finally:
            page.close()


if __name__=="__main__":
    unittest.main()
