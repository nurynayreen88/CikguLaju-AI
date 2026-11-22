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
    t2 = d.add_table(rows=1, cols=2)
    t2.cell(0, 0).text = "Refleksi (Auto / Manual)"
    t2.cell(0, 1).text = "Catatan asal selepas PdP."
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
    page.insert_text((38, 686), "Refleksi (Auto / Manual)", fontsize=9)
    page.insert_text((155.6, 685), "Catatan asal selepas PdP.", fontsize=9)
    page.insert_text((38, 720), "Rujukan DK Matematik", fontsize=9)
    data = d.tobytes()
    d.close()
    return data


class TeacherFields(unittest.TestCase):
    def test_blank_fields_return_original_untouched(self):
        for fmt, doc in (("word", word_fixture()), ("pdf", pdf_fixture())):
            self.assertIs(personalize_approved_rph(doc, fmt, {}), doc)

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
        self.assertEqual(rendered.tables[1].cell(0, 1).text,
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
                "reflection_mode": "manual", "reflection": "Murid perlu bimbingan. "*20
            })


if __name__ == "__main__":
    unittest.main()
