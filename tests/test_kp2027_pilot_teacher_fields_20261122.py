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
    def test_printed_label_is_only_refleksi_in_word_and_pdf(self):
        from docx import Document
        import fitz
        for fmt, source in (("word", word_fixture()), ("pdf", pdf_fixture())):
            for payload in (
                {"reflection_mode": "auto"},
                {"reflection_mode": "manual", "reflection": "Catatan guru tanpa perubahan."},
            ):
                with self.subTest(fmt=fmt, mode=payload["reflection_mode"]):
                    result = personalize_approved_rph(source, fmt, payload)
                    if fmt == "word":
                        document = Document(BytesIO(result))
                        self.assertEqual(document.tables[1].cell(1, 0).text, "Refleksi")
                        self.assertIn("sekurang-kurangnya dua objek",
                                      document.tables[1].cell(0, 1).text)
                    else:
                        with fitz.open(stream=result, filetype="pdf") as document:
                            text = document[0].get_text()
                            self.assertIn("Refleksi", text)
                            self.assertNotIn("(Auto / Manual)", text)
                            self.assertIn("Rujukan DK Matematik", text)
                    self.assertNotEqual(result, source)

    def test_word_reflection_label_preserves_original_typography(self):
        from docx import Document
        from docx.shared import Pt
        document = Document(BytesIO(word_fixture()))
        original_run = document.tables[1].cell(1, 0).paragraphs[0].runs[0]
        original_run.font.name = "Liberation Serif"
        original_run.font.size = Pt(9)
        original_run.bold = True
        buffer = BytesIO()
        document.save(buffer)
        output = personalize_approved_rph(buffer.getvalue(), "word", {})
        label = Document(BytesIO(output)).tables[1].cell(1, 0)
        self.assertEqual(label.text, "Refleksi")
        self.assertEqual(label.paragraphs[0].runs[0].font.name, "Liberation Serif")
        self.assertAlmostEqual(label.paragraphs[0].runs[0].font.size.pt, 9)
        self.assertTrue(label.paragraphs[0].runs[0].bold)

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
                self.assertIn("belum menguasai", " ".join(text.split()))
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

    def test_manual_reflection_fits_in_expanded_box_without_clipping(self):
        import fitz
        reflection=("Murid memerlukan bimbingan susulan berstruktur dan pemantauan khusus.\n" * 6).strip()
        rendered=personalize_approved_rph(pdf_fixture(), "pdf", {
            "reflection_mode": "manual", "reflection": reflection
        })
        with fitz.open(stream=rendered,filetype="pdf") as doc:
            self.assertEqual(doc.page_count,1)
            self.assertEqual(doc[0].get_text().count("Murid memerlukan bimbingan"),6)
            self.assertNotIn("Catatan asal selepas PdP.",doc[0].get_text())


    def test_alam_pdf_reflection_uses_full_cell_without_overlap_and_correct_action(self):
        from web.kp2027_pilot_teacher_fields import _pdf_success_criterion, _reflection_candidates
        import fitz
        criterion = ("Murid menamakan dan menunjukkan sekurang-kurangnya "
                     "lima bahagian tubuh dengan tepat.")
        d = fitz.open()
        page = d.new_page(width=595.3, height=841.9)
        page.insert_text((170, 43), "RANCANGAN PENGAJARAN HARIAN", fontsize=12)
        page.insert_text((215, 64), "KP2027 • TAHUN 1 • PdP 002 (RPT A/B)", fontsize=9)
        for y, label in ((108, "Kelas:"), (121, "Tarikh:"),
                         (134, "Masa:"), (147, "Bil. Murid:")):
            page.insert_text((393.7, y), label, fontsize=8)
        page.insert_text((38, 211), "Objektif Pembelajaran", fontsize=9)
        page.insert_text((156, 211), "Pada akhir PdP, murid berjaya menyebut dengan", fontsize=9)
        page.insert_text((156, 223), "tepat.", fontsize=9)
        page.insert_text((38, 239), "Kriteria Kejayaan", fontsize=9)
        page.insert_text((156, 239), criterion, fontsize=9)
        page.insert_text((38, 256), "EMK / Nilai", fontsize=9)
        page.insert_text((38, 551), "Pengayaan", fontsize=9)
        page.draw_line((37, 564), (558, 564), color=(.7, .7, .7), width=.5)
        page.draw_line((37, 646), (558, 646), color=(.7, .7, .7), width=.5)
        page.insert_text((38, 609), "Refleksi (Auto / Manual)", fontsize=9)
        # Old text begins ABOVE its vertically centered label: old redaction
        # at label.y0-1 left the first line and caused overlapping fonts.
        page.insert_text((159, 599), "CATATAN ASAL YANG MESTI DIPADAM", fontsize=8)
        page.insert_text((159, 612), "BARIS ASAL KEDUA", fontsize=8)
        page.insert_text((38, 660), "Rujukan: DK Alam dan Manusia", fontsize=8)
        page.insert_text((170, 824), "CIKGULAJU • KP2027 TAHUN 1 • Footer lama", fontsize=8)
        self.assertEqual(_pdf_success_criterion(page), criterion.rstrip("."))
        self.assertIn("anggota tubuh", _reflection_candidates(criterion)[0])
        self.assertNotIn("gambar makanan", _reflection_candidates(criterion)[0])
        source=d.tobytes(); d.close()
        out=personalize_approved_rph(source,"pdf",{"reflection_mode":"auto","teacher_students":"35"})
        with fitz.open(stream=out,filetype="pdf") as result:
            self.assertEqual(result.page_count, 1)
            page=result[0]
            text=page.get_text()
            self.assertEqual(text.count("____"),2)
            self.assertIn("anggota tubuh",text)
            self.assertNotIn("CATATAN ASAL",text)
            self.assertNotIn("BARIS ASAL KEDUA",text)
            self.assertNotIn("gambar makanan",text)
            self.assertNotIn("KP2027 • TAHUN 1",text)
            self.assertNotIn("KP2027 TAHUN 1",text)
            spans=[span for block in page.get_text("dict")["blocks"]
                   for line in block.get("lines",())
                   for span in line["spans"]
                   if span["bbox"][0]>=155 and 564<span["bbox"][1]<646]
            self.assertGreaterEqual(len(spans),2)
            self.assertEqual(len({round(x["size"],1) for x in spans}),1)
            self.assertTrue(all(x["bbox"][3]<=646 for x in spans))

    def test_alam_word_reflection_preserves_font_and_removes_redundant_lines(self):
        from docx import Document
        from docx.shared import Pt
        d=Document(BytesIO(word_fixture()))
        d.add_paragraph("KP2027 • TAHUN 1 • PdP 002 (RPT A/B)")
        d.sections[0].footer.paragraphs[0].text="CIKGULAJU • KP2027 TAHUN 1 • Footer lama"
        old=d.tables[1].cell(1,1).paragraphs[0].runs[0]
        old.font.name="Liberation Serif"
        old.font.size=Pt(8)
        tmp=BytesIO();d.save(tmp)
        output=personalize_approved_rph(tmp.getvalue(),"word",{"reflection_mode":"auto"})
        result=Document(BytesIO(output))
        self.assertNotIn("KP2027 • TAHUN 1"," ".join(p.text for p in result.paragraphs))
        self.assertNotIn("KP2027 TAHUN 1",result.sections[0].footer.paragraphs[0].text)
        runs=result.tables[1].cell(1,1).paragraphs[0].runs
        self.assertTrue(runs)
        self.assertEqual(runs[0].font.name,"Liberation Serif")
        self.assertAlmostEqual(runs[0].font.size.pt,8.0)
        self.assertEqual(result.tables[1].cell(1,1).text.count("____"),2)

    def test_rpt_buttons_download_directly_without_second_mobile_save_step(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        page=(root/"web_v1_static_preview/index.html").read_text(encoding="utf-8")
        script=(root/"web_v1_static_preview/rpt-personalize.js").read_text(encoding="utf-8")
        self.assertIn("#rpt-download-mobile:not([hidden]){display:inline-flex!important}",page)
        self.assertNotIn('window.open("about:blank","_blank")',page)
        self.assertIn('rptDownload.addEventListener("click"',page)
        self.assertIn('function rptDirectPdfUrl(entry)',page)
        self.assertIn('if(rptKP2027Choice(entry))return rptKP2027Url(entry,"pdf")',page)
        self.assertIn('rptMobileLink.href=directUrl;',page)
        self.assertIn('rptMobileLink.setAttribute("download","");',page)
        self.assertIn('rptWordLink.setAttribute("download","");',page)
        self.assertIn('if(rptDirectPdfUrl(item))return;',page)
        self.assertNotIn('async function downloadKP2027Rpt(selection)',page)
        self.assertNotIn('target="_blank" id="rpt-download',page)
        self.assertIn('result.delivery="direct-download"',script)
        self.assertNotIn('phone-tab-link',script)
        self.assertNotIn('rpt-prepared-manual-link',script)


if __name__ == "__main__":
    unittest.main()
