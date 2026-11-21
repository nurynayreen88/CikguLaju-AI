"""Exact PPKI menu, API, RPH rendering and RPT entitlement."""
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

from docx import Document
from flask import Flask
from pypdf import PdfReader
from web.rph_premium_readback_20261121 import premium_rph_details

from curriculum_version_telegram import install
from rpt_2027.english.telegram_downloads import install as install_rpt
from staging.ppki.catalog import MANIPULATIVE_UNIT1, MANIPULATIVE_UNIT2, MANIPULATIVE_UNIT3, MANIPULATIVE_UNIT_LESSONS, SUBJECT, UNIT, UNIT1, UNIT3, UNIT4, UNIT5, UNIT6, YEAR3_MANIPULATIVE_UNIT_LESSONS
from web.telegram_ppki_api import create_ppki_blueprint


class PpkiTelegramTest(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.documents = []
        self.allow = False
        self.state = {42: {"task": "rph", "subject": "Sains", "lesson_no": "999"}}
        self.namespace = {
            "state": self.state, "SUBJECTS_BY_GRADE": {}, "SUBJECT_LABEL": {},
            "callback": lambda *_: None, "subjects": lambda *_: None, "year": lambda *_: None,
            "send": lambda _, message, kb=None: self.messages.append((message, kb)),
            "send_document": self._send_file, "_credit_gate": lambda *_: self.allow,
            "_access_info": lambda _: {"active": self.allow}, "_is_admin": lambda _: False,
            "_telegram_delivery_ok_v25279": lambda result: result == {"ok": True},
        }
        self.assertTrue(install(self.namespace))
        self.assertTrue(install_rpt(self.namespace))

    def _send_file(self, _, path, caption):
        file = Path(path)
        self.documents.append((file.name, file.read_bytes(), caption))
        return {"ok": True}

    def test_choice_chain_and_document_gate(self):
        callback = self.namespace["callback"]
        self.namespace["year"](42, "primary")
        for key in ("cv_primary_ppki", "cv_ppki_year2", "cv_ppki_subject",
                    "cv_ppki_component", f"cv_ppki_unit_{UNIT1}", "cv_ppki_lesson_039"):
            self.assertIn(key, [button["callback_data"] for row in self.messages[-1][1] for button in row])
            callback(42, key)
        self.assertNotIn("lesson_no", self.state[42])
        callback(42, "cv_ppki_pdf_018")
        self.assertFalse(self.documents)
        callback(42, f"cv_ppki_unit_{UNIT1}")
        callback(42, "cv_ppki_lesson_039")
        callback(42, "cv_ppki_word_039")
        self.assertFalse(self.documents)
        self.allow = True
        callback(42, "cv_ppki_word_039")
        callback(42, "cv_ppki_pdf_039")
        self.assertEqual([name.rsplit(".", 1)[1] for name, *_ in self.documents], ["docx", "pdf"])
        pdf = PdfReader(BytesIO(self.documents[-1][1]))
        self.assertEqual(len(pdf.pages), 1)
        self.assertIn("1.3.3", pdf.pages[0].extract_text())

    def test_manipulative_component_has_its_own_units(self):
        callback = self.namespace["callback"]
        self.namespace["year"](42, "primary")
        for key in ("cv_primary_ppki", "cv_ppki_year2", "cv_ppki_subject",
                    "cv_ppki_component_km", f"cv_ppki_unit_{MANIPULATIVE_UNIT1}",
                    "cv_ppki_lesson_040"):
            buttons = [item["callback_data"] for row in self.messages[-1][1] for item in row]
            self.assertIn(key, buttons)
            callback(42, key)
        self.allow = True
        callback(42, "cv_ppki_pdf_040")
        name, body, _ = self.documents[-1]
        self.assertTrue(name.endswith("_040.pdf"))
        text = PdfReader(BytesIO(body)).pages[0].extract_text()
        self.assertIn("Kami Aktif", text)
        self.assertIn("1.2.1", text)
        callback(42, f"cv_ppki_unit_{UNIT1}")
        self.assertIn("Kemahiran Manipulatif", self.messages[-1][0])
        self.assertEqual(len(self.documents), 1)

    def test_year4_unit4_telegram_selection_and_rpt(self):
        callback = self.namespace["callback"]
        self.namespace["year"](42, "primary")
        for key in ("cv_primary_ppki", "cv_ppki_year4", "cv_ppki_subject",
                    "cv_ppki_component", f"cv_ppki_unit_{UNIT4}", "cv_ppki_lesson_039"):
            self.assertIn(key, [button["callback_data"] for row in self.messages[-1][1] for button in row])
            callback(42, key)
        callback(42, "cv_ppki_word_039")
        self.assertFalse(self.documents)
        self.allow = True
        callback(42, "cv_ppki_word_039")
        callback(42, "cv_ppki_pdf_039")
        self.assertEqual([name.rsplit(".", 1)[1] for name, *_ in self.documents], ["docx", "pdf"])
        self.assertIn("4.2.3", PdfReader(BytesIO(self.documents[-1][1])).pages[0].extract_text())
        callback(42, "rpt2027_ppki_year4")
        self.assertIn("39 PdP", self.messages[-1][0])
        callback(42, "rpt2027_ppki_pdf4")
        self.assertEqual(len(PdfReader(BytesIO(self.documents[-1][1])).pages), 4)

    def test_year4_manipulative_telegram_selection_and_rpt(self):
        callback = self.namespace["callback"]
        self.namespace["year"](42, "primary")
        for key in ("cv_primary_ppki", "cv_ppki_year4", "cv_ppki_subject",
                    "cv_ppki_component_km", f"cv_ppki_unit_{MANIPULATIVE_UNIT3}", "cv_ppki_lesson_078"):
            self.assertIn(key, [button["callback_data"] for row in self.messages[-1][1] for button in row])
            callback(42, key)
        callback(42, "cv_ppki_pdf_078")
        self.assertFalse(self.documents)
        self.allow = True
        callback(42, "cv_ppki_word_078")
        callback(42, "cv_ppki_pdf_078")
        self.assertEqual([name.rsplit(".", 1)[1] for name, *_ in self.documents], ["docx", "pdf"])
        self.assertIn("3.3.4", PdfReader(BytesIO(self.documents[-1][1])).pages[0].extract_text())
        callback(42, "rpt2027_ppki_year4")
        self.assertIn("Kemahiran Manipulatif: 39 PdP", self.messages[-1][0])
        callback(42, "rpt2027_ppki_km_pdf4")
        self.assertEqual(len(PdfReader(BytesIO(self.documents[-1][1])).pages), 3)

    def test_year5_telegram_selects_unit6_and_delivers_both_formats_and_rpt(self):
        callback = self.namespace["callback"]
        self.namespace["year"](42, "primary")
        for key in ("cv_primary_ppki", "cv_ppki_year5", "cv_ppki_subject",
                    "cv_ppki_component", f"cv_ppki_unit_{UNIT6}", "cv_ppki_lesson_041"):
            self.assertIn(key, [button["callback_data"] for row in self.messages[-1][1] for button in row])
            callback(42, key)
        callback(42, "cv_ppki_pdf_041")
        self.assertFalse(self.documents)
        self.allow = True
        callback(42, "cv_ppki_word_041")
        callback(42, "cv_ppki_pdf_041")
        self.assertEqual([name.rsplit(".", 1)[1] for name, *_ in self.documents], ["docx", "pdf"])
        self.assertIn("6.2.4", PdfReader(BytesIO(self.documents[-1][1])).pages[0].extract_text())
        callback(42, "rpt2027_ppki_home")
        self.assertIn("rpt2027_ppki_year5", [button["callback_data"] for row in self.messages[-1][1] for button in row])
        callback(42, "rpt2027_ppki_year5")
        self.assertIn("41 PdP", self.messages[-1][0])
        callback(42, "rpt2027_ppki_pdf5")
        self.assertEqual(len(PdfReader(BytesIO(self.documents[-1][1])).pages), 6)

    def test_year5_manipulative_menu_and_paid_rpt(self):
        callback = self.namespace["callback"]
        self.namespace["year"](42, "primary")
        for key in ("cv_primary_ppki", "cv_ppki_year5", "cv_ppki_subject", "cv_ppki_component_km",
                    f"cv_ppki_unit_{MANIPULATIVE_UNIT2}", "cv_ppki_lesson_070"):
            self.assertIn(key, [button["callback_data"] for row in self.messages[-1][1] for button in row])
            callback(42, key)
        callback(42, "cv_ppki_pdf_070")
        callback(42, "rpt2027_ppki_km_pdf5")
        self.assertFalse(self.documents)
        self.allow = True
        callback(42, "cv_ppki_pdf_070")
        self.assertIn("Dayung Sampan", PdfReader(BytesIO(self.documents[-1][1])).pages[0].extract_text())
        callback(42, "rpt2027_ppki_year5")
        self.assertIn("Kemahiran Manipulatif: 43 PdP", self.messages[-1][0])
        callback(42, "rpt2027_ppki_km_pdf5")
        self.assertEqual(len(PdfReader(BytesIO(self.documents[-1][1])).pages), 4)

    def test_year6_telegram_choice_and_rpt(self):
        callback = self.namespace["callback"]
        self.namespace["year"](42, "primary")
        for choice in ("cv_primary_ppki", "cv_ppki_year6", "cv_ppki_subject", "cv_ppki_component",
                       f"cv_ppki_unit_{UNIT6}", "cv_ppki_lesson_035"):
            self.assertIn(choice, [button["callback_data"] for row in self.messages[-1][1] for button in row])
            callback(42, choice)
        callback(42, "cv_ppki_pdf_035")
        callback(42, "rpt2027_ppki_pdf6")
        self.assertFalse(self.documents)
        self.allow = True
        callback(42, "cv_ppki_pdf_035")
        self.assertIn("6.2.4", PdfReader(BytesIO(self.documents[-1][1])).pages[0].extract_text())
        callback(42, "rpt2027_ppki_home")
        self.assertIn("rpt2027_ppki_year6", [button["callback_data"] for row in self.messages[-1][1] for button in row])
        callback(42, "rpt2027_ppki_year6")
        self.assertIn("35 PdP", self.messages[-1][0])
        callback(42, "rpt2027_ppki_pdf6")
        self.assertEqual(len(PdfReader(BytesIO(self.documents[-1][1])).pages), 6)

    def test_year6_manipulative_menu_and_rpt(self):
        callback = self.namespace["callback"]
        self.namespace["year"](42, "primary")
        for choice in ("cv_primary_ppki", "cv_ppki_year6", "cv_ppki_subject", "cv_ppki_component_km",
                       f"cv_ppki_unit_{MANIPULATIVE_UNIT3}", "cv_ppki_lesson_069"):
            self.assertIn(choice, [button["callback_data"] for row in self.messages[-1][1] for button in row])
            callback(42, choice)
        callback(42, "cv_ppki_pdf_069")
        callback(42, "rpt2027_ppki_km_pdf6")
        self.assertFalse(self.documents)
        self.allow = True
        callback(42, "cv_ppki_pdf_069")
        self.assertIn("3.2.3", PdfReader(BytesIO(self.documents[-1][1])).pages[0].extract_text())
        callback(42, "rpt2027_ppki_year6")
        self.assertIn("Kemahiran Manipulatif: 34 PdP", self.messages[-1][0])
        callback(42, "rpt2027_ppki_km_pdf6")
        self.assertEqual(len(PdfReader(BytesIO(self.documents[-1][1])).pages), 4)

    def test_rpt_under_own_menu_and_paid_gate(self):
        callback = self.namespace["callback"]
        callback(42, "rpt2027_ppki_pdf2")
        self.assertIn("Akses Terhad", self.messages[-1][0])
        self.assertFalse(self.documents)
        self.allow = True
        for key in ("rpt2027_home", "rpt2027_ppki_home", "rpt2027_ppki_year2", "rpt2027_ppki_pdf2"):
            callback(42, key)
        rpt = PdfReader(BytesIO(self.documents[-1][1]))
        self.assertEqual(len(rpt.pages), 5)
        content = "\n".join(page.extract_text() for page in rpt.pages)
        for number in range(1, 40):
            self.assertIn(f"{number:03d}", content)
        self.assertIn("Agihan PdP Unit 2", content)
        self.assertIn("Rumah Rubina", rpt.pages[3].extract_text())
        self.assertIn("Budi Pekerti Mulia", rpt.pages[4].extract_text())
        self.assertIn("Mari Belajar", rpt.pages[0].extract_text())
        self.assertIn("UNIT_1_2_3_4_5_2027.pdf", self.documents[-1][0])
        callback(42, "rpt2027_ppki_km_pdf2")
        filename, data, _ = self.documents[-1]
        self.assertIn("KEMAHIRAN_MANIPULATIF", filename)
        rpt = PdfReader(BytesIO(data))
        self.assertEqual(len(rpt.pages), 3)
        self.assertIn("Jari Kreatif", rpt.pages[1].extract_text())
        self.assertIn("Lihat, Dengar dan Rasa", rpt.pages[2].extract_text())


class PpkiApiTest(unittest.TestCase):
    def test_year3_73_word_pdf_and_rpt_have_exact_scope(self):
        app = Flask(__name__)
        app.register_blueprint(create_ppki_blueprint())
        client = app.test_client()
        prefix = "/internal/rph/v1/ppki"
        token = "P" * 32
        headers = {"Authorization": f"Bearer {token}"}
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
                                       "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            source = client.get(prefix + "/catalog?year=3", headers=headers).get_json()
            self.assertEqual(source["year"], 3)
            self.assertEqual(source["units"], [{"value": UNIT1, "label": "Unit 1 · Sekolah, Duniaku"}])
            km = source["kemahiran_manipulatif"]
            self.assertEqual([unit["value"] for unit in km], list(YEAR3_MANIPULATIVE_UNIT_LESSONS))
            for unit in km:
                self.assertEqual([row["value"] for row in unit["lessons"]],
                                 [f"{n:03d}" for n in YEAR3_MANIPULATIVE_UNIT_LESSONS[unit["value"]]])
            self.assertEqual([row["value"] for row in source["lessons"]],
                             [f"{number:03d}" for number in range(1, 18)])
            self.assertEqual([unit["value"] for unit in source["additional_units"]], [UNIT, UNIT3, UNIT4, UNIT5])
            self.assertEqual(client.get(prefix + "/catalog?year=3&year=2", headers=headers).status_code, 400)
            teacher = {"class": "3 Bestari", "date": "2027-01-20", "time": "09:00 - 09:30",
                       "students": "8", "reflection": "Ulang dengan pilihan bergambar."}
            units = [{"value": UNIT1, "lessons": source["lessons"]}, *source["additional_units"], *km]
            expected = (range(1, 18), range(18, 36), range(36, 40), range(40, 44), range(44, 50),
                        *YEAR3_MANIPULATIVE_UNIT_LESSONS.values())
            for unit, numbers in zip(units, expected, strict=True):
                self.assertEqual([row["value"] for row in unit["lessons"]], [f"{n:03d}" for n in numbers])
                for row in unit["lessons"]:
                    selection = {"year": 3, "subject": SUBJECT, "unit": unit["value"], "lesson": row["value"]}
                    for fmt in ("word", "pdf"):
                        response = client.post(prefix + "/render", headers=headers,
                                               json={"selection": selection, "teacher": teacher, "format": fmt})
                        self.assertEqual(response.status_code, 200)
                        self.assertIn("TAHUN_3_" + row["value"], response.headers["Content-Disposition"])
                        if fmt == "word":
                            doc = Document(BytesIO(response.data))
                            text = "\n".join([p.text for p in doc.paragraphs] +
                                             [cell.text for table in doc.tables for cells in table.rows for cell in cells.cells])
                        else:
                            doc = PdfReader(BytesIO(response.data))
                            self.assertEqual(len(doc.pages), 1)
                            text = doc.pages[0].extract_text()
                        self.assertIn("Tahun 3", text)
                        self.assertIn("Ulang dengan pilihan bergambar.", text)
            bad = {**selection, "year": 2}
            self.assertEqual(client.post(prefix + "/render", headers=headers,
                                         json={"selection": bad, "teacher": teacher, "format": "pdf"}).status_code, 404)
            rpt = client.get(prefix + "/rpt.pdf?year=3", headers=headers)
            self.assertEqual(rpt.status_code, 200)
            pages = PdfReader(BytesIO(rpt.data)).pages
            self.assertEqual(len(pages), 5)
            for page, last in zip(pages, ("017", "035", "039", "043", "049"), strict=True):
                text = page.extract_text()
                self.assertIn("Tahun 3", text)
                self.assertIn(last, text)
            response = client.get(prefix + "/rpt-manipulatif.pdf?year=3", headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertIn("KEMAHIRAN_MANIPULATIF_TAHUN_3", response.headers["Content-Disposition"])
            km_rpt = PdfReader(BytesIO(response.data))
            self.assertEqual(len(km_rpt.pages), 3)
            for page, last in zip(km_rpt.pages, ("055", "061", "073"), strict=True):
                self.assertIn("Kemahiran Manipulatif", page.extract_text())
                self.assertIn(last, page.extract_text())

    def test_year4_four_pengurusan_diri_units(self):
        app = Flask(__name__)
        app.register_blueprint(create_ppki_blueprint())
        client = app.test_client()
        prefix = "/internal/rph/v1/ppki"
        token = "Y" * 32
        headers = {"Authorization": f"Bearer {token}"}
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
                                       "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            options = client.get(prefix + "/catalog?year=4", headers=headers).get_json()
            self.assertEqual(options["year"], 4)
            self.assertEqual(options["units"], [{"value": UNIT1, "label": "Unit 1 · Bertamu di Inap Desa"}])
            self.assertEqual([r["value"] for r in options["lessons"]], [f"{n:03d}" for n in range(1, 10)])
            self.assertEqual(len(options["kemahiran_manipulatif"]), 3)
            unit2, unit3, unit4 = options["additional_units"]
            self.assertEqual((unit2["value"], unit2["label"]), (UNIT, "Unit 2 · Kebersihan Diri"))
            self.assertEqual([r["value"] for r in unit2["lessons"]], [f"{n:03d}" for n in range(10, 26)])
            for source, key, label, numbers in (
                (unit3, UNIT3, "Unit 3 · Perasaanku", range(26, 34)),
                (unit4, UNIT4, "Unit 4 · Budayakan Amalan Murni", range(34, 40)),
            ):
                self.assertEqual((source["value"], source["label"]), (key, label))
                self.assertEqual([r["value"] for r in source["lessons"]], [f"{n:03d}" for n in numbers])
            self.assertEqual(client.post(prefix + "/render", headers=headers, json={
                "selection": {"year": 4, "subject": SUBJECT, "unit": UNIT1, "lesson": "010"},
                "teacher": dict.fromkeys(("class", "date", "time", "students"), ""), "format": "pdf",
            }).status_code, 404)
            for unit, lesson in [
                (source["value"], lesson)
                for source in [{"value": UNIT1, "lessons": options["lessons"]}, unit2, unit3, unit4]
                for lesson in source["lessons"]
            ]:
                selection = {"year": 4, "subject": SUBJECT, "unit": unit, "lesson": lesson["value"]}
                for fmt in ("word", "pdf"):
                    result = client.post(prefix + "/render", headers=headers,
                                         json={"selection": selection, "teacher": dict.fromkeys(("class", "date", "time", "students"), ""), "format": fmt})
                    self.assertEqual(result.status_code, 200)
                    self.assertIn("TAHUN_4_" + lesson["value"], result.headers["Content-Disposition"])
                    if fmt == "pdf":
                        doc = PdfReader(BytesIO(result.data))
                        self.assertEqual(len(doc.pages), 1)
                        self.assertIn("Tahun 4", doc.pages[0].extract_text())
                        if unit == UNIT:
                            self.assertIn("Kebersihan Diri", doc.pages[0].extract_text())
                    else:
                        word = Document(BytesIO(result.data))
                            self.assertEqual(len(word.tables), 4)
                            fields = premium_rph_details(word)
                            self.assertIn("Standard Kandungan", fields)
                            self.assertIn("Standard Pembelajaran", fields)
                            self.assertEqual(fields["Kelas"], "")
            result = client.get(prefix + "/rpt.pdf?year=4", headers=headers)
            self.assertEqual(result.status_code, 200)
            rpt = PdfReader(BytesIO(result.data))
            self.assertIn("TAHUN_4_UNIT_1_2_3_4_2027.pdf", result.headers["Content-Disposition"])
            self.assertEqual(len(rpt.pages), 4)
            for page, start, end, last_sp in zip(
                rpt.pages, (1, 10, 26, 34), (9, 25, 33, 39), ("1.3.3", "2.4.3", "3.2.4", "4.2.3"), strict=True,
            ):
                page_text = page.extract_text()
                for number in range(start, end + 1):
                    self.assertIn(f"{number:03d}", page_text)
                self.assertIn(last_sp, page_text)

    def test_year4_manipulative_all_39_word_pdf_and_rpt(self):
        app = Flask(__name__)
        app.register_blueprint(create_ppki_blueprint())
        client = app.test_client()
        prefix = "/internal/rph/v1/ppki"
        token = "P" * 32
        headers = {"Authorization": f"Bearer {token}"}
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
                                       "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            listing = client.get(prefix + "/catalog?year=4", headers=headers)
            self.assertLess(len(listing.data), 20000)
            units = listing.get_json()["kemahiran_manipulatif"]
            expected = [
                (MANIPULATIVE_UNIT1, "Lihat, Bau, Rasa dan Dengar", 40, 54, "1.5.3"),
                (MANIPULATIVE_UNIT2, "Sihat dan Cergas", 55, 66, "2.3.3"),
                (MANIPULATIVE_UNIT3, "Ringan Tangan", 67, 78, "3.3.4"),
            ]
            for unit, (key, label, start, end, _) in zip(units, expected, strict=True):
                self.assertEqual(unit["value"], key)
                self.assertIn(label, unit["label"])
                self.assertEqual([r["value"] for r in unit["lessons"]],
                                 [f"{n:03d}" for n in range(start, end + 1)])
                for row in unit["lessons"]:
                    number = row["value"]
                    choice = {"year": 4, "subject": SUBJECT, "unit": key, "lesson": number}
                    for fmt in ("word", "pdf"):
                        result = client.post(prefix + "/render", headers=headers, json={
                            "selection": choice, "teacher": dict.fromkeys(("class", "date", "time", "students"), ""),
                            "format": fmt,
                        })
                        self.assertEqual(result.status_code, 200, (key, number, fmt))
                        self.assertIn("TAHUN_4_" + number, result.headers["Content-Disposition"])
                        if fmt == "pdf":
                            pages = PdfReader(BytesIO(result.data)).pages
                            self.assertEqual(len(pages), 1, (key, number))
                            self.assertIn(label, pages[0].extract_text())
                        else:
                            word = Document(BytesIO(result.data))
                            self.assertEqual(len(word.tables), 4)
                            fields = premium_rph_details(word)
                            self.assertIn("Standard Kandungan", fields)
                            self.assertIn("Standard Pembelajaran", fields)
                            self.assertEqual(fields["Kelas"], "")
            result = client.get(prefix + "/rpt-manipulatif.pdf?year=4", headers=headers)
            self.assertEqual(result.status_code, 200)
            self.assertIn("KEMAHIRAN_MANIPULATIF_TAHUN_4", result.headers["Content-Disposition"])
            for page, (_, title, start, end, sp) in zip(PdfReader(BytesIO(result.data)).pages, expected, strict=True):
                evidence = page.extract_text()
                self.assertIn(title, evidence)
                self.assertIn(sp, evidence)
                for number in range(start, end + 1):
                    self.assertIn(f"{number:03d}", evidence)

    def test_year5_all_41_word_pdf_and_rpt(self):
        app = Flask(__name__)
        app.register_blueprint(create_ppki_blueprint())
        client = app.test_client()
        prefix = "/internal/rph/v1/ppki"
        token = "T" * 32
        headers = {"Authorization": f"Bearer {token}"}
        expected = (
            (UNIT1, "Kesusilaan Cerminan Diri", 1, 9, "1.2.5"),
            (UNIT, "Aktifkan Dirimu", 10, 13, "2.1.4"),
            (UNIT3, "Emosi Sihat, Hubungan Erat", 14, 21, "3.2.4"),
            (UNIT4, "Adab Mulia, Akhlak Terpelihara", 22, 29, "4.2.4"),
            (UNIT5, "Rumahku Selamat", 30, 33, "5.1.4"),
            (UNIT6, "Asas Pertolongan Cemas", 34, 41, "6.2.4"),
        )
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
                                       "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            got = client.get(prefix + "/catalog?year=5", headers=headers).get_json()
            self.assertEqual(got["year"], 5)
            self.assertEqual(got["units"], [{"value": UNIT1, "label": "Unit 1 · Kesusilaan Cerminan Diri"}])
            sources = [{"value": UNIT1, "label": got["units"][0]["label"], "lessons": got["lessons"]},
                       *got["additional_units"]]
            for src, (unit, title, start, last, _) in zip(sources, expected, strict=True):
                self.assertEqual(src["value"], unit)
                self.assertIn(title, src["label"])
                self.assertEqual([row["value"] for row in src["lessons"]],
                                 [f"{n:03d}" for n in range(start, last + 1)])
                for item in src["lessons"]:
                    choice = {"year": 5, "subject": SUBJECT, "unit": unit, "lesson": item["value"]}
                    for fmt in ("word", "pdf"):
                        result = client.post(prefix + "/render", headers=headers, json={
                            "selection": choice, "teacher": dict.fromkeys(("class", "date", "time", "students"), ""),
                            "format": fmt,
                        })
                        self.assertEqual(result.status_code, 200, (unit, item["value"], fmt))
                        self.assertIn("TAHUN_5_" + item["value"], result.headers["Content-Disposition"])
                        if fmt == "pdf":
                            pages = PdfReader(BytesIO(result.data)).pages
                            self.assertEqual(len(pages), 1)
                            self.assertIn(title, pages[0].extract_text())
                        else:
                            word = Document(BytesIO(result.data))
                            self.assertEqual(len(word.tables), 4)
                            fields = premium_rph_details(word)
                            self.assertIn("Standard Kandungan", fields)
                            self.assertIn("Standard Pembelajaran", fields)
                            self.assertEqual(fields["Kelas"], "")
            bad = client.post(prefix + "/render", headers=headers, json={
                "selection": {"year": 5, "subject": SUBJECT, "unit": UNIT1, "lesson": "041"},
                "teacher": {}, "format": "pdf",
            })
            self.assertEqual(bad.status_code, 404)
            result = client.get(prefix + "/rpt.pdf?year=5", headers=headers)
            self.assertEqual(result.status_code, 200)
            self.assertIn("TAHUN_5_UNIT_1_2_3_4_5_6_2027.pdf", result.headers["Content-Disposition"])
            pages = PdfReader(BytesIO(result.data)).pages
            for page, (_, label, start, end, sp) in zip(pages, expected, strict=True):
                text = page.extract_text()
                self.assertIn(label, text)
                self.assertIn(sp, text)
                for number in range(start, end + 1):
                    self.assertIn(f"{number:03d}", text)
            result = client.get(prefix + "/rpt-manipulatif.pdf?year=5", headers=headers)
            self.assertEqual(result.status_code, 200)
            self.assertIn("KEMAHIRAN_MANIPULATIF_TAHUN_5", result.headers["Content-Disposition"])
            pages = PdfReader(BytesIO(result.data)).pages
            self.assertEqual(len(pages), 4)
            for page, (first, last) in zip(pages, ((42, 53), (54, 61), (62, 74), (75, 84)), strict=True):
                rows = [line.split()[0] for line in page.extract_text().splitlines()
                        if line.split() and line.split()[0].isdigit()]
                self.assertEqual(rows, [f"{n:03d}" for n in range(first, last + 1)])

    def test_year6_all_35_pengurusan_diri_rph_and_rpt(self):
        app = Flask(__name__)
        app.register_blueprint(create_ppki_blueprint())
        client = app.test_client()
        prefix = "/internal/rph/v1/ppki"
        key = "R" * 40
        headers = {"Authorization": f"Bearer {key}"}
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": key,
                                       "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            selection_data = client.get(prefix + "/catalog?year=6", headers=headers).get_json()
            self.assertEqual(selection_data["year"], 6)
            units = [{**selection_data["units"][0], "lessons": selection_data["lessons"]},
                     *selection_data["additional_units"]]
            self.assertEqual([unit["value"] for unit in units], [UNIT1, UNIT, UNIT3, UNIT4, UNIT5, UNIT6])
            bounds = ((1, 8), (9, 15), (16, 19), (20, 23), (24, 27), (28, 35))
            teacher = {"class": "6 Bestari", "date": "2027-02-16", "time": "09:00 - 10:00", "students": "8"}
            for unit, (first, last) in zip(units, bounds, strict=True):
                self.assertEqual([r["value"] for r in unit["lessons"]], [f"{n:03d}" for n in range(first, last+1)])
                for lesson in unit["lessons"]:
                    choice = {"year": 6, "subject": SUBJECT, "unit": unit["value"], "lesson": lesson["value"]}
                    for fmt in ("word", "pdf"):
                        result = client.post(prefix + "/render", headers=headers, json={
                            "selection": choice, "teacher": teacher, "format": fmt,
                        })
                        self.assertEqual(result.status_code, 200)
                        self.assertIn("TAHUN_6_" + lesson["value"], result.headers["Content-Disposition"])
                        if fmt == "pdf":
                            pages = PdfReader(BytesIO(result.data)).pages
                            self.assertEqual(len(pages), 1)
                            text = pages[0].extract_text()
                        else:
                            doc = Document(BytesIO(result.data))
                            text = "\n".join(cell.text for table in doc.tables for row in table.rows for cell in row.cells)
                        self.assertIn("6 Bestari", text)
                        self.assertIn(unit["label"], text)
            result = client.get(prefix + "/rpt.pdf?year=6", headers=headers)
            self.assertEqual(result.status_code, 200)
            pages = PdfReader(BytesIO(result.data)).pages
            for page, (first, last) in zip(pages, bounds, strict=True):
                present = [line.split()[0] for line in page.extract_text().splitlines()
                           if line.split() and line.split()[0].isdigit()]
                self.assertEqual(present, [f"{n:03d}" for n in range(first,last+1)])
            result = client.get(prefix + "/rpt-manipulatif.pdf?year=6", headers=headers)
            self.assertEqual(result.status_code, 200)
            self.assertIn("KEMAHIRAN_MANIPULATIF_TAHUN_6", result.headers["Content-Disposition"])
            pages = PdfReader(BytesIO(result.data)).pages
            for page, (first, last) in zip(pages, ((36, 46), (47, 53), (54, 63), (64, 69)), strict=True):
                present = [line.split()[0] for line in page.extract_text().splitlines()
                           if line.split() and line.split()[0].isdigit()]
                self.assertEqual(present, [f"{n:03d}" for n in range(first, last + 1)])

    def test_year6_manipulative_all_34_documents(self):
        app = Flask(__name__)
        app.register_blueprint(create_ppki_blueprint())
        client = app.test_client()
        prefix = "/internal/rph/v1/ppki"
        key = "M" * 40
        headers = {"Authorization": f"Bearer {key}"}
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": key,
                                       "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            units = client.get(prefix + "/catalog?year=6", headers=headers).json["kemahiran_manipulatif"]
            self.assertEqual([unit["value"] for unit in units], [
                MANIPULATIVE_UNIT1, MANIPULATIVE_UNIT2, MANIPULATIVE_UNIT3,
            ])
            teacher = {"class": "6 Bestari", "date": "2027-02-16", "time": "09:00 - 10:00", "students": "8"}
            for unit, bounds in zip(units, ((36, 53), (54, 63), (64, 69)), strict=True):
                self.assertEqual([lesson["value"] for lesson in unit["lessons"]],
                                 [f"{n:03d}" for n in range(bounds[0], bounds[1] + 1)])
                for lesson in unit["lessons"]:
                    selection = {"year": 6, "subject": SUBJECT, "unit": unit["value"], "lesson": lesson["value"]}
                    for fmt in ("word", "pdf"):
                        result = client.post(prefix + "/render", headers=headers, json={
                            "selection": selection, "teacher": teacher, "format": fmt,
                        })
                        self.assertEqual(result.status_code, 200)
                        self.assertIn("TAHUN_6_" + lesson["value"], result.headers["Content-Disposition"])
                        if fmt == "pdf":
                            pages = PdfReader(BytesIO(result.data)).pages
                            self.assertEqual(len(pages), 1)
                            text = pages[0].extract_text()
                        else:
                            doc = Document(BytesIO(result.data))
                            text = "\n".join(cell.text for table in doc.tables for row in table.rows for cell in row.cells)
                        self.assertIn("6 Bestari", text)
                        self.assertIn(unit["label"], text)
                        self.assertNotIn("1.4.2", text)
            result = client.post(prefix + "/render", headers=headers, json={
                "selection": {**selection, "unit": MANIPULATIVE_UNIT2}, "teacher": teacher, "format": "pdf",
            })
            self.assertEqual(result.status_code, 404)

    def test_year5_all_43_manipulative_rph_word_and_pdf(self):
        app = Flask(__name__)
        app.register_blueprint(create_ppki_blueprint())
        client = app.test_client()
        prefix = "/internal/rph/v1/ppki"
        key = "K" * 40
        headers = {"Authorization": f"Bearer {key}"}
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": key,
                                       "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            source = client.get(prefix + "/catalog?year=5", headers=headers).get_json()
            units = source["kemahiran_manipulatif"]
            self.assertEqual([unit["value"] for unit in units], [
                MANIPULATIVE_UNIT1, MANIPULATIVE_UNIT2, MANIPULATIVE_UNIT3,
            ])
            teacher = {"class": "5 Bestari", "date": "2027-02-16", "time": "09:00 - 10:00", "students": "8"}
            for unit, numbers in zip(units, (range(42, 62), range(62, 75), range(75, 85)), strict=True):
                self.assertEqual([lesson["value"] for lesson in unit["lessons"]], [f"{n:03d}" for n in numbers])
                for lesson in unit["lessons"]:
                    selection = {"year": 5, "subject": SUBJECT, "unit": unit["value"], "lesson": lesson["value"]}
                    for fmt in ("word", "pdf"):
                        response = client.post(prefix + "/render", headers=headers, json={
                            "selection": selection, "teacher": teacher, "format": fmt,
                        })
                        self.assertEqual(response.status_code, 200)
                        self.assertIn("TAHUN_5_" + lesson["value"], response.headers["Content-Disposition"])
                        if fmt == "word":
                            doc = Document(BytesIO(response.data))
                            text = "\n".join([p.text for p in doc.paragraphs] +
                                             [cell.text for table in doc.tables for row in table.rows for cell in row.cells])
                        else:
                            doc = PdfReader(BytesIO(response.data))
                            self.assertEqual(len(doc.pages), 1)
                            text = doc.pages[0].extract_text()
                        self.assertIn(unit["label"], text)
                        self.assertIn("5 Bestari", text)
            response = client.post(prefix + "/render", headers=headers, json={
                "selection": {**selection, "unit": MANIPULATIVE_UNIT2}, "teacher": teacher, "format": "pdf",
            })
            self.assertEqual(response.status_code, 404)

    def test_all_71_word_pdf_and_protected_access(self):
        app = Flask(__name__)
        app.register_blueprint(create_ppki_blueprint())
        client = app.test_client()
        prefix = "/internal/rph/v1/ppki"
        self.assertEqual(client.get(prefix + "/catalog").status_code, 401)
        self.assertEqual(client.get(prefix + "/rpt.pdf").status_code, 401)
        token = "P" * 32
        headers = {"Authorization": f"Bearer {token}"}
        with patch.dict("os.environ", {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": token,
                                       "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1"}):
            options = client.get(prefix + "/catalog", headers=headers).get_json()
            self.assertEqual([row["value"] for row in options["lessons"]],
                             [f"{number:03d}" for number in range(1, 15)])
            teacher = {"class": "2 Bestari", "date": "2027-03-04", "time": "08:00 - 08:30",
                       "students": "7", "reflection": "Ulang dengan kad gambar."}
            selection = {"year": 2, "subject": SUBJECT, "unit": UNIT, "lesson": "001"}
            self.assertEqual([unit["value"] for unit in options["additional_units"]], [UNIT3, UNIT4, UNIT5, UNIT1])
            manipulative = options["kemahiran_manipulatif"]
            self.assertEqual([unit["value"] for unit in manipulative], list(MANIPULATIVE_UNIT_LESSONS))
            for unit in manipulative:
                self.assertEqual([row["value"] for row in unit["lessons"]],
                                 [f"{number:03d}" for number in MANIPULATIVE_UNIT_LESSONS[unit["value"]]])
            units = [{"value": UNIT, "lessons": options["lessons"]}, *options["additional_units"], *manipulative]
            for unit in units:
                selection["unit"] = unit["value"]
                for row in unit["lessons"]:
                    selection["lesson"] = row["value"]
                    for fmt in ("word", "pdf"):
                        response = client.post(prefix + "/render", headers=headers,
                                               json={"selection": selection, "teacher": teacher, "format": fmt})
                        self.assertEqual(response.status_code, 200, response.get_json(silent=True))
                        if fmt == "word":
                            doc = Document(BytesIO(response.data))
                            text = "\n".join(cell.text for table in doc.tables for cells in table.rows for cell in cells.cells)
                        else:
                            doc = PdfReader(BytesIO(response.data))
                            self.assertEqual(len(doc.pages), 1)
                            text = doc.pages[0].extract_text()
                        self.assertIn("2 Bestari", text)
                        self.assertIn("Ulang dengan kad gambar.", text)
            selection["unit"] = UNIT
            selection["lesson"] = "015"
            self.assertEqual(client.post(prefix + "/render", headers=headers,
                                         json={"selection": selection, "teacher": teacher, "format": "pdf"}).status_code, 404)
            for endpoint, pages in (("/rpt.pdf", 1), ("/rpt-current.pdf", 5), ("/rpt-manipulatif.pdf", 3)):
                response = client.get(prefix + endpoint, headers=headers)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(PdfReader(BytesIO(response.data)).pages), pages)
