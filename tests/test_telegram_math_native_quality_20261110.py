"""Native Telegram Web-bridge Math quality check; no user data or quota."""
from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path
from tempfile import gettempdir
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from docx import Document
from flask import Flask
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4

from web import telegram_verified_sequence_rph_bridge as bridge

AUTH = "test-internal-secret-token-" + "a" * 40
UNIT = "u" + "a" * 24
TEACHER = {
    "class": "4 Ikhlas", "date": "2026-11-10",
    "time": "08:00 - 09:00", "students": "30",
}
PHASES = (
    ("Set Induksi", 5), ("Aktiviti 1", 12), ("Aktiviti 2", 18),
    ("Aktiviti 3", 20), ("Pengukuhan", 5), ("Penutup", 5),
)
OK_PHASES = (
    ("Set Induksi", 5), ("Aktiviti 1", 10), ("Aktiviti 2", 15),
    ("Aktiviti 3", 15), ("Pengukuhan", 10), ("Penutup", 5),
)


def real_doc_bytes(fmt, bad):
    phases = PHASES if bad else OK_PHASES
    lines = [
        "RPH MATEMATIK TAHUN 3",
        "STANDARD KANDUNGAN: 4.4 4.4 Darab wang" if bad
        else "STANDARD KANDUNGAN: 4.4 Darab wang",
        "STANDARD PEMBELAJARAN: 4.4.1 Mendarab nilai wang",
        "OBJEKTIF PEMBELAJARAN: Murid menunjukkan pengetahuan atau kemahiran berdasarkan standard"
        if bad else
        "OBJEKTIF PEMBELAJARAN: Murid menjawab 4 daripada 5 soalan darab wang.",
        "KRITERIA KEJAYAAN: 4 daripada 5 soalan dijawab tepat",
    ] + [f"{phase} ({minute} minit)" for phase, minute in phases]
    output = BytesIO()
    if fmt == "word":
        doc = Document()
        for line in lines:
            doc.add_paragraph(line)
        # Production's compact_web_word_notes expects three native tables:
        # teacher details; 3-column activities; final reflection.
        details = doc.add_table(rows=1, cols=2)
        details.cell(0, 0).text = "Kelas"
        details.cell(0, 1).text = "4 Ikhlas"
        activities = doc.add_table(rows=1, cols=3)
        activities.cell(0, 0).text = "Fasa"
        activities.cell(0, 1).text = "Aktiviti guru dan murid"
        activities.cell(0, 2).text = "Catatan"
        reflection = doc.add_table(rows=1, cols=2)
        reflection.cell(0, 0).text = "Refleksi"
        reflection.cell(0, 1).text = "PBD individu"
        doc.save(output)
    else:
        pdf = Canvas(output, pagesize=A4)
        for i, line in enumerate(lines):
            pdf.drawString(40, 790-i*23, line)
        pdf.showPage()
        pdf.save()
    return output.getvalue()


class NativeMathQualityTests(unittest.TestCase):
    def setUp(self):
        self.bad = True
        self.subject = "MATH"
        self.state = {"subject": "Matematik", "task": "rph",
                      "rph_time": "08:00 - 09:00"}
        self.runtime = SimpleNamespace(
            _sm2542_rows=lambda *_: [],
            _sm2542_unique_units=lambda *_: [],
            _commit_multi_sp=lambda *_: None,
            _local_rph_text=lambda *_: "source",
            create_word_file=lambda state, text, unique:
                self._file("word", unique),
            create_pdf_file=lambda state, text, unique:
                self._file("pdf", unique),
        )
        self.app = Flask("math-native-doc-quality")
        self.app.register_blueprint(bridge.create_native_sequence_rph_blueprint(self.runtime))
        self.client = self.app.test_client()
        self.env = patch.dict(os.environ, {
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": AUTH,
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.build = patch.object(bridge, "_build_state", side_effect=self._build)
        self.build.start()
        self.addCleanup(self.build.stop)
        self.text = patch.object(bridge, "_source_text", return_value="x"*700)
        self.text.start()
        self.addCleanup(self.text.stop)

    def _build(self, runtime, year, subject, unit, pdp, teacher):
        self.assertEqual(runtime, self.runtime)
        self.assertEqual(teacher, TEACHER)
        self.subject = subject
        return dict(self.state)

    def _file(self, fmt, unique):
        ext = ".docx" if fmt == "word" else ".pdf"
        path = Path(gettempdir()) / (unique + "_test" + ext)
        path.write_bytes(real_doc_bytes(fmt, self.bad))
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        return str(path)

    def send(self, fmt, subject="MATH"):
        return self.client.post("/internal/rph/v1/sequence/render",
            headers={"Authorization": "Bearer " + AUTH},
            json={
                "selection":{"year":3,"subject":subject,
                             "unit":UNIT,"lesson":"MT3-PDP-060"},
                "teacher":TEACHER,"format":fmt,
            })

    def test_bad_math_word_and_pdf_blocked_without_document_delivery(self):
        for fmt in ("word", "pdf"):
            with self.subTest(fmt=fmt):
                res = self.send(fmt)
                self.assertEqual(res.status_code, 503, res.get_json(silent=True))
                self.assertEqual(res.json["code"], "MATH_RPH_QUALITY_REVIEW_REQUIRED")
                self.assertNotIn(b"%PDF-", res.data)
                self.assertNotIn(b"PK\x03\x04", res.data)

    def test_good_math_word_and_pdf_delivered(self):
        self.bad = False
        for fmt in ("word", "pdf"):
            with self.subTest(fmt=fmt):
                res = self.send(fmt)
                self.assertEqual(res.status_code, 200, res.get_json(silent=True))
                self.assertEqual(res.headers["Cache-Control"], "no-store, private")
                if fmt == "word":
                    self.assertTrue(res.data.startswith(b"PK\x03\x04"))
                else:
                    self.assertTrue(res.data.startswith(b"%PDF-"))

    def test_science_unchanged(self):
        for fmt in ("word", "pdf"):
            with self.subTest(fmt=fmt):
                res = self.send(fmt, subject="SCIENCE")
                self.assertEqual(res.status_code, 200, res.get_json(silent=True))

    def test_unauthorized_private_route_still_requires_token(self):
        res = self.client.post("/internal/rph/v1/sequence/render", json={})
        self.assertEqual(res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
