import os
import unittest
from io import BytesIO
from unittest.mock import patch

import fitz
from flask import Flask
from PIL import Image, ImageDraw, ImageFont

from web.timetable_reader import read_timetable
from web.timetable_reader_api import bp
from web.timetable_upload import READER_PATH, UnreadableTimetable, validate_result


GRID = [
    ["HARI", "07:30 - 08:00", "08:00 - 08:30", "08:30 - 09:00", "09:00 - 09:30"],
    ["AHAD", "BM\n4 Bestari", "", "REHAT", "BI\n5 Amanah"],
    ["ISNIN", "SN\n5 Amanah", "MT\n4 Bestari", "REHAT", "PI\n4 Bestari"],
    ["SELASA", "", "PJ\n5 Amanah", "REHAT", "PSV\n4 Bestari"],
    ["RABU", "", "", "REHAT", ""],
    ["KHAMIS", "", "", "REHAT", ""],
]
CLASSES = ["4 Bestari", "5 Amanah"]
EXPECTED = [
    ("Isnin", "07:30", "08:00", "5 Amanah", "Sains"),
    ("Isnin", "08:00", "08:30", "4 Bestari", "Matematik"),
    ("Isnin", "09:00", "09:30", "4 Bestari", "Pendidikan Islam"),
    ("Selasa", "08:00", "08:30", "5 Amanah", "Pendidikan Jasmani"),
    ("Selasa", "09:00", "09:30", "4 Bestari", "Pendidikan Seni Visual"),
    ("Ahad", "07:30", "08:30", "4 Bestari", "Bahasa Melayu"),
    ("Ahad", "09:00", "09:30", "5 Amanah", "English"),
]


def grid_cells(transposed=False):
    for row, values in enumerate(GRID):
        for col, value in enumerate(values):
            if (row, col) == (1, 2):
                continue
            x, y = (row, col) if transposed else (col, row)
            w, h = (2, 1) if (row, col) == (1, 1) else (1, 1)
            if transposed:
                w, h = h, w
            yield (20 + 213*x, 40 + 95*y, 20 + 213*(x+w), 40 + 95*(y+h)), value


def image_bytes(fmt="PNG"):
    image = Image.new("RGB", (1110, 650), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("DejaVuSans.ttf", 25)
    for box, value in grid_cells():
        draw.rectangle(box, outline="black", width=3)
        x0, y0, x1, y1 = box
        if value:
            draw.multiline_text(((x0+x1)/2, (y0+y1)/2), value, anchor="mm",
                                align="center", font=font, fill="black")
    result = BytesIO()
    image.save(result, format=fmt)
    return result.getvalue()


def pdf_bytes(*, scanned=False, transposed=False, extra_page=False):
    with fitz.open() as doc:
        page = doc.new_page(width=1320 if transposed else 1110, height=650)
        if scanned:
            page.insert_image(page.rect, stream=image_bytes())
        else:
            for box, value in grid_cells(transposed):
                rect = fitz.Rect(box)
                page.draw_rect(rect, color=(0, 0, 0), width=2)
                page.insert_textbox(rect + (0, 24, 0, 0), value, fontsize=22, align=1)
        if extra_page:
            doc.new_page()
        return doc.tobytes()


def compact_jpeg():
    image = Image.new("RGB", (1030, 640), "#d5effa")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
    draw.text((80, 22), "JADUAL WAKTU", font=font, fill="black")
    rows = [
        ["Hari", "10.30\n11.00", "11.00\n11.30", "11.30\n12.00",
         "12.00\n12.30", "12.30\n1.00"],
        ["I", "KM\n1A", "KM\n1A", "R", "PD\n2B", ""],
        ["S", "", "PJPK\n1B", "E", "", "KM\n1A"],
        ["R", "PD\n2B", "", "H", "", ""],
        ["K", "", "", "A", "PD\n2B", "PD\n2B"],
        ["J", "", "", "T", "", ""],
    ]
    colors = {"KM": "#00b4ed", "PD": "#ff49a8", "PJPK": "#929292"}
    for row, values in enumerate(rows):
        for col, value in enumerate(values):
            x, y = 30 + 160 * col, 70 + 90 * row
            fill = "#ffb7d0" if not row or not col else "#fff"
            if row and col:
                fill = "#22ef40" if col == 3 else colors.get(value.split("\n")[0], fill)
            draw.rectangle((x, y, x + 160, y + 90), outline="black", fill=fill, width=3)
            draw.multiline_text((x + 80, y + 45), value, anchor="mm",
                                align="center", font=font, fill="black")
    result = BytesIO()
    image.save(result, format="JPEG")
    return result.getvalue()


class TimetableReaderTest(unittest.TestCase):
    def assert_slots(self, data):
        result = validate_result(read_timetable(data, CLASSES))
        self.assertEqual([tuple(row.values()) for row in result["entries"]], EXPECTED)
        self.assertEqual(result["uncertain"], 0)
        return result

    def test_actual_image_ocr_with_merged_periods_and_breaks(self):
        for fmt in ("PNG", "JPEG", "WEBP"):
            with self.subTest(fmt=fmt):
                self.assertEqual(self.assert_slots(image_bytes(fmt))["unreadable_pages"], 0)

    def test_actual_vector_pdf_with_days_as_columns(self):
        self.assertEqual(self.assert_slots(pdf_bytes(transposed=True))["unreadable_pages"], 0)

    def test_actual_scanned_pdf_and_partial_page_warning(self):
        self.assertEqual(self.assert_slots(pdf_bytes(scanned=True, extra_page=True))["unreadable_pages"], 1)

    def test_compact_colored_timetable_keeps_codes_and_skips_vertical_break(self):
        result = validate_result(read_timetable(compact_jpeg(), []))
        self.assertEqual([tuple(row.values()) for row in result["entries"]], [
            ("Isnin", "10:30", "11:30", "1A", "KM"),
            ("Isnin", "12:00", "12:30", "2B", "PD"),
            ("Selasa", "11:00", "11:30", "1B", "PJPK"),
            ("Selasa", "12:30", "13:00", "1A", "KM"),
            ("Rabu", "10:30", "11:00", "2B", "PD"),
            ("Khamis", "12:00", "13:00", "2B", "PD"),
        ])
        self.assertEqual(result["uncertain"], 0)

    def test_rejects_invalid_bytes_and_unreadable_document(self):
        for raw in (b"fake.pdf", b"%PDF-damaged", b"\x89PNG\r\n\x1a\nbroken"):
            with self.subTest(raw=raw), self.assertRaises(UnreadableTimetable):
                read_timetable(raw, CLASSES)

    def test_private_endpoint_authenticates_and_returns_real_slots(self):
        app = Flask(__name__)
        app.register_blueprint(bp)
        client = app.test_client()
        token = "test-server-token" * 3
        data = pdf_bytes()
        with patch.dict(os.environ, {"CIKGULAJU_AUTHORITATIVE_API_TOKEN": token}):
            self.assertEqual(client.post(READER_PATH, data=data,
                                         content_type="application/pdf").status_code, 401)
            response = client.post(READER_PATH, data=data, content_type="application/pdf",
                                   headers={"Authorization": "Bearer " + token})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["entries"]), len(EXPECTED))
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")


if __name__ == "__main__":
    unittest.main()
