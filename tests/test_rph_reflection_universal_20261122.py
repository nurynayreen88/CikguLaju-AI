"""Universal KSSR/KP2027 reflection policy regression: keep original curriculum intact."""
from io import BytesIO
import unittest
from docx import Document
import fitz

from web.rph_reflection_universal import (
    candidates, criterion_from_layout, personalize_layout,
    personalize_verified_document,
)

CRITERION="Murid membandingkan dua objek menggunakan deria secara selamat."
ENGLISH_CRITERION="Pupils read aloud five sentences with correct pronunciation."


def word_fixture(criterion=CRITERION, reflection="Catatan refleksi asal."):
    d=Document()
    header=d.add_table(rows=1,cols=2)
    header.cell(0,0).text="Kelas"
    header.cell(0,1).text="3 Amanah"
    table=d.add_table(rows=2,cols=2)
    table.cell(0,0).text="Kriteria Kejayaan"
    table.cell(0,1).text=criterion
    table.cell(1,0).text="Aktiviti Utama"
    table.cell(1,1).text="Aktiviti 1 – Uji deria menggunakan dua objek selamat."
    footer=d.add_table(rows=2,cols=2)
    footer.cell(0,0).text="Pemulihan / Pengayaan"
    footer.cell(0,1).text="Bimbingan guru."
    footer.cell(1,0).text="Refleksi"
    footer.cell(1,1).text=reflection
    b=BytesIO();d.save(b);return b.getvalue()


def pdf_fixture(criterion=CRITERION, reflection_label="Refleksi"):
    doc=fitz.open()
    page=doc.new_page(width=595,height=842)
    # Draw a real fixed-grid RPH: 2-column criterion and reflection cells.
    for y in (120,160,225,310,410,510,620,710,785):
        page.draw_line((35,y),(560,y),color=(0,0,0),width=.6)
    for x in (35,170,560):
        page.draw_line((x,120),(x,785),color=(0,0,0),width=.6)
    page.insert_text((45,180),"Kriteria Kejayaan",fontsize=10)
    page.insert_text((180,180),criterion,fontsize=9)
    page.insert_text((45,258),"Aktiviti Utama",fontsize=10)
    page.insert_text((180,258),"Murid membezakan dua objek dengan selamat.",fontsize=9)
    page.insert_text((45,729),reflection_label,fontsize=10)
    page.insert_text((180,729),"Catatan refleksi asal.",fontsize=9)
    data=doc.tobytes();doc.close();return data


class TestUniversalReflection(unittest.TestCase):
    def test_two_blank_counts_and_subject_specific_action(self):
        for criterion,term in (
            ("Murid membandingkan dua objek melalui deria.", "deria"),
            ("Murid membilang nombor satu hingga sembilan.", "pembilang"),
            ("Murid menjelaskan situasi sentuhan tidak selamat.", "simulasi"),
            ("Murid mentafsir piktograf data harian.", "piktograf"),
        ):
            with self.subTest(criterion=criterion):
                text=candidates(criterion,"SCIENCE")[0]
                self.assertEqual(text.count("____"),2)
                self.assertIn(term,text)
                self.assertNotIn("25 orang",text)
                self.assertIn(criterion.removeprefix("Murid ").lower(),text.lower())

    def test_english_reflection_keeps_language_and_blanks(self):
        text=candidates(ENGLISH_CRITERION,"ENGLISH")[0]
        self.assertIn("____ pupils",text)
        self.assertEqual(text.count("____"),2)
        self.assertIn(ENGLISH_CRITERION,text)
        self.assertIn("guided reading",text)

    def test_verified_kssr_layout_automatic_and_manual(self):
        layout={
            "style":"telegram-native-rph-v1",
            "header":[{"label":"Kriteria Kejayaan","value":CRITERION}],
            "footer":[{"label":"Pemulihan / Pengayaan","value":"Bimbingan"},
                      {"label":"Refleksi","value":"Ayat placeholder asal."}],
        }
        self.assertEqual(criterion_from_layout(layout),CRITERION.rstrip("."))
        self.assertTrue(personalize_layout(layout,{"students":"30"},"SCIENCE"))
        result=layout["footer"][1]["value"]
        self.assertEqual(result.count("____"),2)
        self.assertIn("deria",result)
        self.assertNotIn("30 orang",result)
        layout["footer"][1]["value"]="Refleksi auto"
        self.assertTrue(personalize_layout(layout,{"reflection":"Catatan cikgu sendiri."},"SCIENCE"))
        self.assertEqual(layout["footer"][1]["value"],"Catatan cikgu sendiri.")

    def test_actual_kssr_telegram_layout_uses_shared_policy(self):
        from web.telegram_rph_parity import build_layout
        source={
            "subject":"MORAL","year":2,"unit":"Jiran Baik","lesson":1,
            "teacher":{"class":"2 Amanah","date":"","time":"","students":"30"},
            "fields":[
                {"label":"Kriteria Kejayaan","value":CRITERION},
                {"label":"Aktiviti 1","value":"Murid membandingkan dua objek selamat."},
            ],
        }
        layout=build_layout(source,{"MORAL":"Pendidikan Moral"})
        self.assertEqual(layout["style"],"telegram-native-rph-v1")
        self.assertEqual(layout["footer"][1]["value"].count("____"),2)
        self.assertIn("deria",layout["footer"][1]["value"])
        self.assertNotIn("30 orang",layout["footer"][1]["value"])
        source["teacher"]["reflection"]="Refleksi guru sebenar."
        manual=build_layout(source,{"MORAL":"Pendidikan Moral"})
        self.assertEqual(manual["footer"][1]["value"],"Refleksi guru sebenar.")

    def test_verified_word_document_changes_only_reflection_cell(self):
        source=word_fixture()
        result=personalize_verified_document(BytesIO(source),"word",
            {"subject":"SCIENCE","source":"telegram-native-pdp-sequence","teacher":{"students":"30"}})
        self.assertNotEqual(result.getvalue(),source)
        a,b=Document(BytesIO(source)),Document(result)
        self.assertEqual(a.tables[1].cell(0,1).text,b.tables[1].cell(0,1).text)
        self.assertEqual(a.tables[1].cell(1,1).text,b.tables[1].cell(1,1).text)
        self.assertEqual(a.tables[2].cell(0,1).text,b.tables[2].cell(0,1).text)
        text=b.tables[2].cell(1,1).text
        self.assertEqual(text.count("____"),2)
        self.assertIn("deria",text)
        self.assertNotIn("30 orang",text)

    def test_verified_kssr_word_preserves_font_label_and_compacts_empty_height(self):
        from docx.shared import Pt
        from docx.enum.table import WD_ROW_HEIGHT_RULE
        doc = Document(BytesIO(word_fixture()))
        row = doc.tables[2].rows[1]
        row.cells[0].paragraphs[0].runs[0].text = "Refleksi (Auto / Manual)"
        body_run = row.cells[1].paragraphs[0].runs[0]
        body_run.font.name = "Liberation Serif"
        body_run.font.size = Pt(9)
        row.height = Pt(110)
        row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY
        original = BytesIO()
        doc.save(original)
        result = personalize_verified_document(BytesIO(original.getvalue()), "word", {
            "subject": "SCIENCE", "source": "telegram-native-pdp-sequence", "teacher": {}
        })
        output = Document(result)
        out_row = output.tables[2].rows[1]
        self.assertEqual(out_row.cells[0].text, "Refleksi")
        self.assertIn("deria", out_row.cells[1].text)
        self.assertNotIn("Auto / Manual", out_row.cells[0].text)
        self.assertEqual(out_row.cells[1].paragraphs[0].runs[0].font.name, "Liberation Serif")
        self.assertAlmostEqual(out_row.cells[1].paragraphs[0].runs[0].font.size.pt, 9)
        self.assertEqual(out_row.height_rule, WD_ROW_HEIGHT_RULE.AUTO)
        self.assertIsNone(out_row.height)
        self.assertEqual(output.tables[1].cell(1, 1).text,
                         doc.tables[1].cell(1, 1).text)

    def test_verified_layout_does_not_print_auto_manual_control_label(self):
        layout = {
            "style": "telegram-native-rph-v1",
            "header": [{"label": "Kriteria Kejayaan", "value": CRITERION}],
            "footer": [{"label": "Pemulihan / Pengayaan", "value": "Asal"},
                       {"label": "Refleksi (Auto / Manual)", "value": "Asal"}],
        }
        self.assertTrue(personalize_layout(layout, {"reflection": "Catatan cikgu."}, "SCIENCE"))
        self.assertEqual(layout["footer"][1]["label"], "Refleksi")
        self.assertEqual(layout["footer"][1]["value"], "Catatan cikgu.")

    def test_verified_pdf_document_changes_only_reflection_row(self):
        source=pdf_fixture()
        output=personalize_verified_document(BytesIO(source),"pdf",
            {"subject":"SCIENCE","source":"telegram-native-pdp-sequence","teacher":{}})
        self.assertNotEqual(output.getvalue(),source)
        doc=fitz.open(stream=output.getvalue(),filetype="pdf")
        self.assertEqual(doc.page_count,1)
        text=" ".join(doc[0].get_text().split())
        self.assertEqual(text.count("____"),2)
        self.assertIn("belum menguasai",text)
        self.assertIn("Aktiviti Utama",text)
        self.assertIn(CRITERION,text)
        self.assertNotIn("Catatan refleksi asal",text)
        doc.close()

    def test_verified_kssr_pdf_does_not_print_auto_manual_suffix(self):
        source = pdf_fixture(reflection_label="Refleksi (Auto / Manual)")
        result = personalize_verified_document(BytesIO(source), "pdf", {
            "subject": "SCIENCE", "source": "telegram-native-pdp-sequence", "teacher": {}
        })
        with fitz.open(stream=result.getvalue(), filetype="pdf") as document:
            page = document[0]
            text = page.get_text()
            self.assertIn("Refleksi", text)
            self.assertNotIn("(Auto / Manual)", text)
            self.assertIn("Kriteria Kejayaan", text)
            self.assertIn("Aktiviti Utama", text)
            self.assertEqual(text.count("____"), 2)

    def test_manual_and_historical_pi_v2_untouched(self):
        source=word_fixture()
        for selection in (
            {"subject":"SCIENCE","source":"telegram-native-pdp-sequence",
             "teacher":{"reflection":"25 murid mencapai objektif"}},
            {"subject":"PI","source":"pi-696-private-bundle","teacher":{}},
        ):
            self.assertIs(
                personalize_verified_document(BytesIO(source),"word",selection).getvalue()==source,True)

    def test_unknown_word_pdf_source_and_missing_criterion_untouched(self):
        word=word_fixture(criterion="—")
        doc=fitz.open();doc.new_page()
        pdf=doc.tobytes();doc.close()
        for fmt,source in (("word",word),("pdf",pdf)):
            self.assertEqual(
                personalize_verified_document(BytesIO(source),fmt,
                  {"subject":"BM","source":"telegram-native-bm-pdp","teacher":{}}).getvalue(),source)


if __name__=="__main__":
    unittest.main()
