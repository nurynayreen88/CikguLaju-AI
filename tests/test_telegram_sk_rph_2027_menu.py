"""Verify the bot menu uses the exact reviewed plans and existing credit gate."""

from collections import Counter
from io import BytesIO
from pathlib import Path
from threading import Lock
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from docx import Document
from flask import Flask
from pypdf import PdfReader

from curriculum_version_telegram import install as install_curriculum
from staging.matematik.penjana_2027 import DPK_ROUTE, ROUTE, register_downloads
from web.native_rph_telegram_api import create_native_rph_blueprint
from web.telegram_sk_rph_2027 import install
from web.telegram_rph_entry_choices_20261110 import install as install_entry


class TelegramSKRPH2027Tests(unittest.TestCase):
    def setUp(self):
        self.documents = []
        self.credits = 0
        self.allow_delivery = True
        self.account_allowed = True
        r = self.runtime = SimpleNamespace(
            callback=lambda cid, data: ("legacy", data),
            _continue_after_rph_time=lambda cid, st: "legacy materials",
            state={},
            _runtime_lock=Lock(),
            _processing_chats=set(),
            send=lambda cid, text, keyboard: keyboard,
            send_document=self._send_document,
            _credit_gate=lambda cid, st: self.account_allowed,
            _telegram_delivery_ok_v25279=lambda result: result is True,
            _consume_free_after_success_v25282=self._debit,
            _lesson_to_class_v2439=lambda cid: "existing class picker",
            _temporary_auto_pack_v2386=lambda cid: "existing material picker",
            CIKGULAJU_TELEGRAM_SPECIAL_RPH_MENU_ACTIVE=True,
            SUBJECTS_BY_GRADE={}, SUBJECT_LABEL={},
            subjects=lambda cid, label: [[{"text": "Sains", "callback_data": "sub_Sains"}],
                                         r._cikgulaju_dlp_subject_buttons(r.state[cid], label)],
            year=lambda cid, level: ("legacy year", level),
            quick=lambda cid: None,
        )
        self.assertTrue(install_curriculum(r.__dict__))
        self.assertTrue(install_entry(r))
        self.assertTrue(install(r))
        self.assertEqual(self.click("choose_grade"), ("legacy", "choose_grade"))
        self.assertIn("sk27:home", self.buttons(r.quick(123)))

    @staticmethod
    def buttons(menu):
        return [button["callback_data"] for row in menu for button in row]

    def click(self, command):
        return self.runtime.callback(123, command)

    def _send_document(self, cid, path, caption):
        self.documents.append((Path(path).name, Path(path).read_bytes()))
        return self.allow_delivery

    def _debit(self, cid, reason):
        self.credits += 1

    def _select(self, scope, unit, code):
        self.click("sk27:home")
        self.click(f"sk27:set:{scope}")
        self.click(f"sk27:unit:{scope}:{unit}")
        self.assertEqual(self.click(f"sk27:pick:{scope}:{unit}:{code}"), "existing class picker")
        state = self.runtime.state[123]
        state.update(rph_class="Bestari", rph_date="18/10/2027", rph_time="08:00 - 09:00",
                     rph_students="32")
        buttons = self.buttons(self.runtime._continue_after_rph_time(123, state))
        return buttons[:2]

    def test_primary_dlp_path_opens_all_year_three_to_six_download_sets(self):
        scopes = {3: ("d3", "m3"), 4: ("d4", "m4"), 5: ("d5", "m5"), 6: ("d6", "m")}
        self.runtime.state[123] = {"task": "rph"}
        self.click("cv_primary_kssr")
        for year, subject_scopes in scopes.items():
            year_button = f"year_{year}"
            for name, scope in zip(("science", "math"), subject_scopes, strict=True):
                with self.subTest(year=year, subject=name):
                    subjects = self.click(year_button)
                    self.assertEqual(self.buttons(subjects), ["sub_Sains", "cv_dlp_science", "cv_dlp_math"])
                    units = self.buttons(self.click(f"cv_dlp_{name}"))
                    self.assertIn("back_subjects", units)
                    unit = next(button for button in units if button.startswith(f"sk27:unit:{scope}:"))
                    lessons = self.buttons(self.click(unit))
                    self.assertIn(f"sk27:dlp:{scope}", lessons)
                    lesson = next(button for button in lessons if button.startswith(f"sk27:pick:{scope}:"))
                    self.assertEqual(self.click(lesson), "existing class picker")
                    state = self.runtime.state[123]
                    self.assertEqual(state["year"], f"Tahun {year}")
                    self.assertEqual(state["curriculum_version"], "dlp")
                    state.update(rph_class="Bestari", rph_date="18/10/2027",
                                 rph_time="08:00 - 09:00", rph_students="32")
                    word, pdf, back, *_ = self.buttons(self.runtime._continue_after_rph_time(123, state))
                    self.click(word)
                    self.click(pdf)
                    self.assertTrue(self.documents[-1][0].endswith(lesson.split(":")[-1] + ".pdf"))
                    self.assertEqual(len(PdfReader(BytesIO(self.documents[-1][1])).pages), 1)
                    return_to_units = f"sk27:dlp:{scope}"
                    self.assertIn(return_to_units, self.buttons(self.click(back)))
                    self.assertIn("back_subjects", self.buttons(self.click(return_to_units)))
                    self.assertIn(f"cv_dlp_{name}", self.buttons(self.click("back_subjects")))
        self.assertEqual(len(self.documents), 16)
        self.assertEqual(self.credits, 8)

    def test_primary_mathematics_opens_the_matching_year_set(self):
        self.runtime.state[123] = {"task": "rph"}
        self.click("cv_primary_kssr")
        for year in (2, 3):
            self.click(f"year_{year}")
            units = self.buttons(self.click("sub_Matematik"))
            self.assertIn("back_subjects", units)
            first = next(item for item in units if item.startswith(f"sk27:unit:dp{year}:"))
            lessons = self.buttons(self.click(first))
            self.assertIn(f"sk27:kssr:dp{year}", lessons)
            choice = next(item for item in lessons if item.startswith(f"sk27:pick:dp{year}:"))
            self.assertEqual(self.click(choice), "existing class picker")
            self.assertEqual(self.runtime.state[123]["curriculum_version"], "existing")
            self.assertTrue(self.runtime.state[123]["lesson_no"].startswith(f"SK27-DPK3-MATH-Y{year}-"))

    def test_math_render_embeds_monochrome_type_and_keeps_reflection_full_width(self):
        from zipfile import ZipFile

        lesson = "SK27-DPK3-MATH-Y2-L015"
        word, pdf = self._select("dp2", "02", lesson)
        self.click(word)
        self.click(pdf)
        with ZipFile(BytesIO(self.documents[0][1])) as package:
            fonts = {name.rsplit("/", 1)[-1] for name in package.namelist() if name.startswith("word/fonts/")}
            self.assertEqual(fonts, {"SourceSans3-Regular.odttf", "SourceSans3-Bold.odttf", "SourceSerif4-Semibold.odttf"})
        document = Document(BytesIO(self.documents[0][1]))
        self.assertEqual(document.styles["Title"].font.name, "Source Serif 4 Semibold")
        self.assertEqual(document.styles["Normal"].font.name, "Source Sans 3")
        self.assertEqual(document.paragraphs[2].style.name, "Title")
        reflection = next(row for row in document.tables[-1].rows if row.cells[0].text.startswith("Refleksi"))
        self.assertIn("murid mencapai objektif", reflection.cells[0].text)
        self.assertEqual(reflection.cells[0]._tc.grid_span, 2)
        page = PdfReader(BytesIO(self.documents[1][1])).pages[0]
        font_names = [str(font.get_object()["/BaseFont"]) for font in page["/Resources"]["/Font"].values()]
        self.assertTrue(any("SourceSerif4-Semibold" in font for font in font_names))
        self.assertTrue(any("SourceSans3-Regular" in font for font in font_names))
        for operands, operator in page.get_contents().operations:
            if operator in (b"rg", b"RG"):
                self.assertIn(tuple(operands), ((0, 0, 0), (1, 1, 1)))

    def test_every_exact_selection_can_send_word_and_pdf(self):
        keys = [key for key in self.buttons(self.click("sk27:home")) if key.startswith("sk27:set:")]
        counts = Counter()
        for scope in keys:
            units = [key for key in self.buttons(self.click(scope)) if key.startswith("sk27:unit:")]
            for unit in units:
                lessons = [key for key in self.buttons(self.click(unit)) if key.startswith("sk27:pick:")]
                for key in lessons:
                    _, _, set_id, unit_id, code = key.split(":")
                    with self.subTest(code=code):
                        word, pdf = self._select(set_id, unit_id, code)
                        self.click(word)
                        self.click(pdf)
                        self.assertEqual(self.documents[-2][0], f"CikguLaju_RPH_{code}.docx")
                        self.assertEqual(self.documents[-1][0], f"CikguLaju_RPH_{code}.pdf")
                        self.assertEqual(len(PdfReader(BytesIO(self.documents[-1][1])).pages), 1)
                        counts[set_id] += 1
        self.assertEqual(counts, {"d3": 56, "m3": 82, "d4": 69, "m4": 77, "s": 116, "m": 54, "s6": 89, "d6": 61, "m5": 69,
                                  "d5": 70, "mt4": 117, "mt5": 117, "mt6": 117,
                                  "dp2": 117, "dp3": 117})
        self.assertEqual(len(self.documents), 2656)
        self.assertEqual(self.credits, 1328)

    def test_dpk_private_route_keeps_edition_year_and_grouped_standards(self):
        app = Flask(__name__)
        register_downloads(app)
        client = app.test_client()
        token = "math-dpk-2027-test-token-for-local-app"
        headers = {"Authorization": f"Bearer {token}"}
        teacher = {"class": "Bestari", "date": "2027-10-18",
                   "students": "32", "reflection": "Semak sekali lagi."}
        with patch.dict("os.environ", {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token}):
            for year, unit_id, number, codes in ((2, 7, 111, "7.1.2, 7.2.1"), (3, 9, 117, "9.2.2")):
                query = {"year": year, "subject": "MATH"}
                units = client.get(DPK_ROUTE + "/units", query_string=query, headers=headers).json["items"]
                lesson = f"SK27-DPK3-MATH-Y{year}-L{number:03d}"
                selection = {**query, "unit": units[unit_id-1]["value"], "lesson": lesson}
                self.assertEqual(client.get(ROUTE + "/availability", query_string=selection,
                                            headers=headers).status_code, 404)
                self.assertEqual(client.get(DPK_ROUTE + "/availability", query_string=selection).status_code, 401)
                response = client.post(DPK_ROUTE + "/render", headers=headers, json={
                    "selection": selection,
                    "teacher": {**teacher, "time": "08:00-09:00" if year == 2 else "08:00-08:30"},
                    "format": "word",
                })
                self.assertEqual(response.status_code, 200, response.get_json(silent=True))
                document = Document(BytesIO(response.data))
                self.assertEqual(document.paragraphs[1].text, f"Matematik SK Tahun {year} · 2027")
                self.assertIn("DPK Edisi 3", document.tables[0].rows[5].cells[1].text)
                self.assertIn("SP " + codes, document.tables[0].rows[4].cells[1].text)
                self.assertIn("Semak sekali lagi.", document.tables[-1].rows[1].cells[1].text)

    def test_dlp_year3_api_downloads_every_exact_lesson(self):
        app = Flask(__name__)
        runtime = SimpleNamespace(create_word_file=lambda *_: None, create_pdf_file=lambda *_: None)
        app.register_blueprint(create_native_rph_blueprint(runtime))
        client = app.test_client()
        path = "/internal/rph/v1/dlp"
        token = "dlp-year-3-test-token-for-local-app"
        headers = {"Authorization": f"Bearer {token}"}
        teacher = {"class": "3 Bestari", "date": "2027-01-07", "time": "08:00–09:00",
                   "students": "29", "reflection": ""}
        with patch.dict("os.environ", {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token}):
            for slug, subject, unit_count, lesson_count in (
                ("science", "SCIENCE_DLP", 11, 56), ("mathematics", "MATH_DLP", 9, 82),
            ):
                url = f"{path}/year3-{slug}/catalogue"
                self.assertEqual(client.get(url).status_code, 401)
                response = client.get(url, headers=headers)
                self.assertEqual(response.status_code, 200)
                catalogue = response.get_json()
                self.assertEqual((catalogue["year"], catalogue["subject"]), (3, subject))
                self.assertEqual(len(catalogue["units"]), unit_count)
                self.assertEqual(sum(len(unit["lessons"]) for unit in catalogue["units"]), lesson_count)
                for unit in catalogue["units"]:
                    for lesson in unit["lessons"]:
                        with self.subTest(lesson=lesson["id"]):
                            selection = {"year": 3, "subject": subject, "unit": unit["id"],
                                         "lesson": lesson["id"]}
                            available = client.get(path + "/availability", query_string=selection, headers=headers)
                            self.assertEqual(available.status_code, 200)
                            for fmt in ("word", "pdf"):
                                file = client.post(path + "/render", headers=headers,
                                                   json={"selection": selection, "teacher": teacher, "format": fmt})
                                self.assertEqual(file.status_code, 200)
                                self.assertIn(lesson["id"], file.headers["Content-Disposition"])
                                if fmt == "word":
                                    document = Document(BytesIO(file.data))
                                    text = " ".join(cell.text for row in document.tables[0].rows for cell in row.cells)
                                    self.assertIn("3 Bestari", text)
                                    self.assertIn(lesson["label"], text)
                                else:
                                    pages = PdfReader(BytesIO(file.data)).pages
                                    self.assertEqual(len(pages), 1)
                                    self.assertIn("3 Bestari", pages[0].extract_text())
                wrong_unit = {**selection, "unit": "01"}
                self.assertEqual(client.get(path + "/availability", query_string=wrong_unit,
                                            headers=headers).status_code, 404)

    def test_dlp_year4_api_returns_the_exact_catalogues_and_files(self):
        app = Flask(__name__)
        runtime = SimpleNamespace(create_word_file=lambda *_: None, create_pdf_file=lambda *_: None)
        app.register_blueprint(create_native_rph_blueprint(runtime))
        client = app.test_client()
        path = "/internal/rph/v1/dlp"
        token = "cikgulaju-local-test-token-for-science-y4"
        headers = {"Authorization": f"Bearer {token}"}
        with patch.dict("os.environ", {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
                                      "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token}):
            self.assertEqual(client.get(path + "/year4-science/catalogue").status_code, 401)
            response = client.get(path + "/year4-science/catalogue", headers=headers)
            self.assertEqual(response.status_code, 200)
            catalogue = response.get_json()
            self.assertEqual((catalogue["year"], catalogue["subject"]), (4, "SCIENCE_DLP"))
            self.assertEqual(len(catalogue["units"]), 10)
            self.assertEqual(sum(len(unit["lessons"]) for unit in catalogue["units"]), 69)
            teacher = {"class": "4 Bestari", "date": "22/08/2027", "time": "08:00 - 09:00",
                       "students": "32", "reflection": "Check the evidence in the next lesson."}
            for unit, lesson in (("08", "DLP-SCI-Y4-L46"), ("10", "DLP-SCI-Y4-R10")):
                selection = {"year": 4, "subject": "SCIENCE_DLP", "unit": unit, "lesson": lesson}
                available = client.get(path + "/availability", query_string=selection, headers=headers)
                self.assertEqual(available.get_json(), {"available": True, "formats": ["word", "pdf"]})
                for fmt, suffix in (("word", "docx"), ("pdf", "pdf")):
                    result = client.post(path + "/render", headers=headers,
                                         json={"selection": selection, "teacher": teacher, "format": fmt})
                    self.assertEqual(result.status_code, 200)
                    self.assertIn(f"{lesson}.{suffix}", result.headers["Content-Disposition"])
                    if fmt == "word":
                        doc = Document(BytesIO(result.data))
                        self.assertIn(teacher["class"], doc.tables[0].rows[3].cells[1].text)
                        reflection = doc.tables[-1].rows[0].cells[0]
                        self.assertEqual(reflection.text.splitlines(), ["Reflection", teacher["reflection"]])
                        self.assertEqual(reflection._tc.grid_span, 2)
                    else:
                        page, = PdfReader(BytesIO(result.data)).pages
                        self.assertIn(teacher["class"], page.extract_text())
                wrong = client.get(path + "/availability", query_string={**selection, "unit": "01"},
                                   headers=headers)
                self.assertEqual(wrong.status_code, 404)
            maths = client.get(path + "/year4-mathematics/catalogue", headers=headers)
            self.assertEqual(maths.status_code, 200)
            maths_units = maths.json["units"]
            self.assertEqual((maths.json["year"], maths.json["subject"]), (4, "MATH_DLP"))
            self.assertEqual(len(maths_units), 8)
            self.assertEqual(sum(len(group["lessons"]) for group in maths_units), 77)
            maths_selection = {"year": 4, "subject": "MATH_DLP", "unit": "08", "lesson": "DLP-MAT-Y4-R08"}
            result = client.post(path + "/render", headers=headers,
                                 json={"selection": maths_selection, "teacher": teacher, "format": "word"})
            self.assertEqual(result.status_code, 200)
            self.assertIn("DLP-MAT-Y4-R08.docx", result.headers["Content-Disposition"])
            self.assertEqual(Document(BytesIO(result.data)).tables[-1].cell(0, 1).text, teacher["reflection"])
            for bad in ({**maths_selection, "unit": "01"},
                        {**maths_selection, "lesson": "DLP-SCI-Y4-R08"}):
                self.assertEqual(client.get(path + "/availability", query_string=bad, headers=headers).status_code, 404)

    def test_wrong_set_old_buttons_and_failed_delivery_cannot_charge(self):
        word, _ = self._select("s", "01", "SK27-SCI-Y5-PDP-001")
        self.allow_delivery = False
        self.click(word)
        self.assertEqual(self.credits, 0)
        self.allow_delivery = True
        self.click(word)
        self.assertEqual(self.credits, 1)

        doc = Document(BytesIO(self.documents[-1][1]))
        self.assertEqual(doc.paragraphs[2].text, "Pemerhatian kualitatif dengan deria")
        self.assertIn("Bestari", doc.tables[0].rows[3].cells[1].text)
        next_word, _ = self._select("m", "01", "DLP-MATH-Y6-L01")
        self.click(word)
        self.assertEqual(len(self.documents), 2)
        self.account_allowed = False
        self.click(next_word)
        self.assertEqual(len(self.documents), 2)
        self.assertEqual(self.credits, 1)

    def test_legacy_math_choices_open_verified_units_without_charging(self):
        cases = {
            "01": ((4, 6), 3),
            "02": ((22, 25, 27, 30, 31, 32), 31),
            "03": ((34, 37, 38), 52),
            "04": ((46, 47), 63),
            "06": ((67, 68), 84),
            "07": ((76, 78, 79, 80, 81, 82, 83, 84), 97),
        }
        for unit, (numbers, verified_lesson) in cases.items():
            for number in numbers:
                with self.subTest(unit=unit, number=number):
                    code = f"MT6-PDP-{number:03d}"
                    state = {"subject": "Matematik", "year": "Tahun 6", "pdp_sequence_code": code}
                    self.runtime.state[123] = state
                    unit_callback = f"sk27:unit:mt6:{unit}"
                    for result in (self.runtime._lesson_to_class_v2439(123),
                                   self.runtime._temporary_auto_pack_v2386(123),
                                   self.runtime._continue_after_rph_time(123, state),
                                   self.click("matsubmit2528")):
                        self.assertIn(unit_callback, self.buttons(result))
                    menu = self.buttons(self.click(unit_callback))
                    self.assertIn(f"sk27:pick:mt6:{unit}:SK27-MATH-Y6-L{verified_lesson:03d}", menu)
                    self.assertNotIn(f"sk27:pick:mt6:{unit}:{code}", menu)
        self.assertEqual(self.documents, [])
        self.assertEqual(self.credits, 0)

        self.assertEqual(self.click("sk27:pick:mt6:07:SK27-MATH-Y6-L097"), "existing class picker")
        state = self.runtime.state[123]
        state.update(rph_class="Bestari", rph_date="18/10/2027", rph_time="08:00 - 09:00",
                     rph_students="32")
        word, pdf = self.buttons(self.runtime._continue_after_rph_time(123, state))[:2]
        self.click(word)
        self.click(pdf)
        doc = Document(BytesIO(self.documents[0][1]))
        fields = {row.cells[0].text: row.cells[1].text for row in doc.tables[0].rows}
        self.assertIn("SP 7.2.1", fields["SK / SP"])
        self.assertEqual(len(PdfReader(BytesIO(self.documents[1][1])).pages), 1)
        self.assertEqual(self.credits, 1)

        for subject, year, code in (("Matematik", "Tahun 6", "MT6-PDP-085"),
                                    ("Matematik", "Tahun 6", "MT6-PDP-005"),
                                    ("Matematik", "Tahun 5", "MT6-PDP-079"),
                                    ("Sains", "Tahun 6", "MT6-PDP-079")):
            state = {"subject": subject, "year": year, "pdp_sequence_code": code}
            self.runtime.state[123] = state
            self.assertEqual(self.runtime._lesson_to_class_v2439(123), "existing class picker")
            self.assertEqual(self.runtime._temporary_auto_pack_v2386(123), "existing material picker")
            self.assertEqual(self.runtime._continue_after_rph_time(123, state), "legacy materials")
            self.assertEqual(self.click("matsubmit2528"), ("legacy", "matsubmit2528"))

    def test_year_four_preserves_grouped_standards_and_thirty_minute_plan(self):
        app = Flask(__name__)
        register_downloads(app)
        client = app.test_client()
        token = "math-sk-2027-test-token-for-local-app"
        headers = {"Authorization": f"Bearer {token}"}
        query = {"year": 4, "subject": "MATH"}
        lesson = "SK27-MATH-Y4-L005"
        with patch.dict("os.environ", {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token}):
            units = client.get(ROUTE + "/units", query_string=query, headers=headers).json["items"]
            self.assertEqual(len(units), 8)
            selection = {**query, "unit": units[0]["value"], "lesson": lesson}
            response = client.post(ROUTE + "/render", headers=headers, json={
                "selection": selection,
                "teacher": {"class": "Bestari", "date": "2027-01-18",
                            "time": "08:00-08:30", "students": "32"},
                "format": "word",
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(client.get(ROUTE + "/availability",
                                        query_string=selection | {"unit": units[1]["value"]},
                                        headers=headers).status_code, 404)
        word, _ = self._select("mt4", "01", lesson)
        self.click(word)
        for data in (response.data, self.documents[-1][1]):
            doc = Document(BytesIO(data))
            fields = {row.cells[0].text: row.cells[1].text for row in doc.tables[0].rows}
            self.assertIn("30 minit", fields["Lesson / tempoh"])
            self.assertIn("SP 1.5.1, 1.5.2", fields["SK / SP"])

    def test_private_web_render_matches_telegram_for_year_six_ratio(self):
        app = Flask(__name__)
        register_downloads(app)
        client = app.test_client()
        token = "math-sk-2027-test-token-for-local-app"
        headers = {"Authorization": f"Bearer {token}"}
        query = {"year": 6, "subject": "MATH"}
        lesson = "SK27-MATH-Y6-L097"
        with patch.dict("os.environ", {"CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
                                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN": token}):
            self.assertEqual(client.get(ROUTE + "/units", query_string=query).status_code, 401)
            units = client.get(ROUTE + "/units", query_string=query, headers=headers).json["items"]
            self.assertEqual(len(units), 8)
            selection = {**query, "unit": units[6]["value"], "lesson": lesson}
            wrong_unit = {**selection, "unit": units[0]["value"]}
            self.assertEqual(client.get(ROUTE + "/availability", query_string=wrong_unit,
                                        headers=headers).status_code, 404)
            teacher = {"class": "Bestari", "date": "2027-10-18", "time": "08:00-09:00", "students": "32"}
            response = client.post(ROUTE + "/render", headers=headers, json={
                "selection": selection, "teacher": teacher, "format": "word",
            })
            self.assertEqual(response.status_code, 200)
        word, _ = self._select("mt6", "07", lesson)
        self.click(word)
        native, telegram = (Document(BytesIO(data)) for data in
                            (response.data, self.documents[-1][1]))
        self.assertEqual(native.paragraphs[2].text, telegram.paragraphs[2].text)
        native_header = native.tables[0].rows
        telegram_header = telegram.tables[0].rows
        self.assertEqual(native_header[4].cells[1].text, telegram_header[4].cells[1].text)
        self.assertIn("SK 7.2", native_header[4].cells[1].text)
