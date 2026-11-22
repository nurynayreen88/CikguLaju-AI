"""KP2027 Word/PDF personalisation: original RPH content remains untouched."""
from io import BytesIO
import unittest

from web.kp2027_pilot_teacher_fields import (
    TeacherFieldError, parse_teacher_fields, personalize_approved_rph,
)


def word_fixture():
    from docx import Document
    d = Document()
    t = d.add_table(rows=1, cols=2)
    t.cell(0, 0).text = "MATEMATIK Tahun 1 - Lesson 001"
    c = t.cell(0, 1)
    c.text = "Maklumat PdP"
    for label in ("Kelas:", "Tarikh:", "Masa:", "Bil. Murid:"):
        c.add_paragraph(label)
    t2 = d.add_table(rows=2, cols=2)
    t2.cell(0, 0).text = "Kriteria Kejayaan"
    t2.cell(0, 1).text = ("Murid membandingkan sekurang-kurangnya dua objek "
                          "berdasarkan ciri yang diperhati atau disentuh secara selamat.")
    t2.cell(1, 0).text = "Refleksi (Auto / Manual)"
    t2.cell(1, 1).text = "Catatan asal selepas PdP."
    d.add_paragraph("Aktiviti 1: Mengenal pasti nombor.")
    b = BytesIO()
    d.save(b)
    return b.getvalue()


def pdf_fixture():
    import fitz
    d = fitz.open()
    page = d.new_page(width=595.3, height=841.9)
    page.insert_text((38, 92), "MATEMATIK Tahun 1 Lesson 001", fontsize=12)
    for y, label in ((105, "Kelas:"), (118, "Tarikh:"), (131, "Masa:"), (144, "Bil. Murid:")):
        page.insert_text((393.7, y), label, fontsize=9)
    page.insert_text((38, 200), "Kriteria Kejayaan", fontsize=9)
    page.insert_text((155.6, 200), "Murid membandingkan sekurang-kurangnya dua objek", fontsize=9)
    page.insert_text((155.6, 211), "berdasarkan ciri yang diperhati atau disentuh secara selamat.", fontsize=9)
    page.insert_text((38, 240), "EMK / Nilai", fontsize=9)
    page.insert_text((38, 686), "Refleksi (Auto / Manual)", fontsize=9)
    page.insert_text((155.6, 685), "Catatan asal selepas PdP.", fontsize=9)
    page.insert_text((155.6, 698), "Pilih refleksi automatik.", fontsize=9)
    page.insert_text((38, 720), "Rujukan DK Matematik", fontsize=9)
    page.insert_text((155.6, 825), "CIKGULAJU - Rujukan: Dokumen Kurikulum KPM", fontsize=9)
    data = d.tobytes()
    d.close()
    return data


class TeacherFields(unittest.TestCase):
    def test_auto_reflection_is_not_placeholder_even_when_teacher_fields_blank(self):
        from docx import Document
        import fitz
        for fmt, original in (("word", word_fixture()), ("pdf", pdf_fixture())):
            with self.subTest(fmt=fmt):
                rendered = personalize_approved_rph(original, fmt, {
                    "teacher_students": "30",
                    "reflection_mode": "auto"
                })
                self.assertNotEqual(rendered, original)
                if fmt == "word":
                    text = Document(BytesIO(rendered)).tables[1].cell(1, 1).text
                else:
                    d = fitz.open(stream=rendered, filetype="pdf")
                    self.assertEqual(d.page_count, 1)
                    text = d[0].get_text()
                    d.close()
                self.assertIn("sekurang-kurangnya dua objek", text)
                self.assertEqual(text.count("____"), 2)
                self.assertIn("orang", text)
                self.assertIn("belum menguasai", text)
                self.assertIn("latihan", text.lower())
                self.assertNotIn("30 orang", text)
                self.assertNotIn("Catatan asal selepas PdP.", text)
                self.assertNotIn("25 murid", text)

    def test_actions_follow_success_criterion_topic(self):
        from web.kp2027_pilot_teacher_fields import _reflection_candidates
        for criterion, expected in (
            ("Murid membandingkan dua objek berdasarkan deria secara selamat.", "membandingkan dua objek"),
            ("Murid membilang serta menyebut dan menulis nombor satu hingga sembilan.", "pembilang"),
            ("Murid menilai situasi sentuhan tidak selamat dan meminta bantuan.", "simulasi"),
            ("Murid membaca piktograf dan mengenal pasti data yang betul.", "piktograf"),
        ):
            with self.subTest(criterion=criterion):
                for reflection in _reflection_candidates(criterion):
                    self.assertEqual(reflection.count("____"), 2)
                    self.assertIn("belum menguasai", reflection)
                    self.assertIn(criterion.removeprefix("Murid "), reflection)
                self.assertIn(expected, _reflection_candidates(criterion)[0])

    def test_manual_reflection_overrides_criterion_based_auto_text(self):
        for fmt, original in (("word", word_fixture()), ("pdf", pdf_fixture())):
            with self.subTest(fmt=fmt):
                rendered = personalize_approved_rph(original, fmt, {
                    "reflection_mode": "manual",
                    "reflection": "17 murid mencapai objektif. 3 murid perlu bimbingan."
                })
                if fmt == "word":
                    from docx import Document
                    text = Document(BytesIO(rendered)).tables[1].cell(1, 1).text
                else:
                    import fitz
                    d = fitz.open(stream=rendered, filetype="pdf")
                    text = d[0].get_text()
                    d.close()
                self.assertIn("17 murid mencapai objektif", text)
                self.assertNotIn("PdP dilaksanakan mengikut perancangan", text)

    def test_auto_reflection_requires_real_success_criteria(self):
        from docx import Document
        d = Document(BytesIO(word_fixture()))
        d.tables[1].cell(0, 0).text = "Bukan Kriteria Kejayaan"
        a = BytesIO(); d.save(a)
        with self.assertRaises(TeacherFieldError):
            personalize_approved_rph(a.getvalue(), "word", {})
        import fitz
        doc = fitz.open(stream=pdf_fixture(), filetype="pdf")
        page = doc[0]
        for rect in page.search_for("Kriteria Kejayaan"):
            page.add_redact_annot(rect, fill=(1, 1, 1), cross_out=False)
        page.apply_redactions()
        invalid = doc.tobytes()
        doc.close()
        with self.assertRaises(TeacherFieldError):
            personalize_approved_rph(invalid, "pdf", {})

    def test_validation_prevents_bad_date_time_students_and_reflection(self):
        for data in (
            {"teacher_date": "2027-02-30"},
            {"teacher_date": "2027/01/02"},
            {"teacher_start": "08:00"},
            {"teacher_start": "09:00", "teacher_end": "08:00"},
            {"teacher_students": "201"},
            {"teacher_class": "X"*41},
            {"reflection_mode": "manual"},
            {"reflection_mode": "auto", "reflection": "not permitted"},
            {"unknown": "value"},
            {"teacher_class": 8},
        ):
            with self.subTest(data=data), self.assertRaises(TeacherFieldError):
                parse_teacher_fields(data)

    def test_fills_word_original_header_and_manual_reflection(self):
        from docx import Document
        original = word_fixture()
        doc = personalize_approved_rph(original, "word", {
            "teacher_class": "1 Bestari", "teacher_date": "2027-04-21",
            "teacher_start": "07:30", "teacher_end": "08:30",
            "teacher_students": "28", "reflection_mode": "manual",
            "reflection": "25 murid mencapai objektif. 3 dibimbing."
        })
        self.assertNotEqual(original, doc)
        rendered = Document(BytesIO(doc))
        header = rendered.tables[0].cell(0, 1).text
        for item in ("Kelas: 1 Bestari", "Tarikh: 21/04/2027",
                     "Masa: 07:30 - 08:30", "Bil. Murid: 28"):
            self.assertIn(item, header)
        self.assertEqual(rendered.tables[1].cell(1, 1).text,
                         "25 murid mencapai objektif. 3 dibimbing.")
        self.assertIn("Aktiviti 1: Mengenal pasti nombor.",
                      "\n".join(p.text for p in rendered.paragraphs))

    def test_fills_pdf_one_page_without_overwriting_main_content(self):
        import fitz
        original = pdf_fixture()
        doc = personalize_approved_rph(original, "pdf", {
            "teacher_class": "1 Bestari", "teacher_date": "2027-04-21",
            "teacher_start": "07:30", "teacher_end": "08:30",
            "teacher_students": "28", "reflection_mode": "manual",
            "reflection": "25 murid mencapai objektif."
        })
        rendered = fitz.open(stream=doc, filetype="pdf")
        self.assertEqual(rendered.page_count, 1)
        fulltext = rendered[0].get_text()
        for item in ("1 Bestari", "21/04/2027", "07:30 - 08:30",
                     "28", "25 murid mencapai objektif.", "MATEMATIK Tahun 1"):
            self.assertIn(item, fulltext)
        self.assertNotIn("Catatan asal selepas PdP.", fulltext)
        self.assertIn("Rujukan DK Matematik", fulltext)
        rendered.close()

    def test_does_not_stamp_wrong_pdf_layout(self):
        import fitz
        d = fitz.open(); d.new_page()
        invalid = d.tobytes();d.close()
        with self.assertRaises(TeacherFieldError):
            personalize_approved_rph(invalid, "pdf", {"teacher_class": "1 Bestari"})

    def test_manual_reflection_longer_than_one_page_box_fails_before_download(self):
        with self.assertRaises(TeacherFieldError):
            personalize_approved_rph(pdf_fixture(), "pdf", {
                "reflection_mode": "manual", "reflection": ("Murid memerlukan bimbingan susulan berstruktur dan pemantauan khusus.\n" * 6).strip()
            })


if __name__ == "__main__":
    unittest.main()
