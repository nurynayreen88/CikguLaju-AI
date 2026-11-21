"""Fix verified Jawi complex-script bold; protect source text and private ZIP routing."""
import io
import os
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from docx import Document
from docx.oxml.ns import qn

from web import pi_696_private_bundle as pi
from web.pi_696_jawi_pdf_fix import with_jawi_bold


def example_word():
    doc = Document()
    hero = doc.add_table(rows=1, cols=2)
    hero.cell(0, 0).text = "رنچڠن ڤڠاجرن هارين"
    details = doc.add_table(rows=4, cols=2)
    details.cell(0, 0).text = "ستاندرد کاندوڠن"
    details.cell(0, 1).text = "4.1 Merumus"
    activities = doc.add_table(rows=6, cols=2)
    activities.cell(1, 0).text = "اکتيۏيتي اوتام"
    cell = activities.cell(1, 1)
    cell.text = ""
    for text in ("اکتيۏيتي 1", "2. ݢورو menerangkan maklumat.",
                 "اکتيۏيتي 2", "3. موريد melaksanakan tugasan."):
        p = cell.add_paragraph()
        run = p.add_run(text)
        run.font.name = "Amiri"
        run.bold = text.startswith("اکتيۏيتي")
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


class TestJawiBoldPDFAddon(unittest.TestCase):
    def test_pdf_archive_is_pinned_and_private(self):
        s = pi.ARCHIVES["v2-bold-pdf"]
        self.assertEqual(s["bytes"], 26641162)
        self.assertEqual(s["sha256"], "4387c6808a286fb6855bdb5f48e43a4436ef7264e0b9e916c7067a99f217937d")
        self.assertEqual(s["object"], "rph-premium/pi-2027/v2/696-jawi-bold-pdf-addon.zip")

    def test_bold_jawi_does_not_change_any_source_text(self):
        original = example_word()
        old = Document(io.BytesIO(original))
        revised, count = with_jawi_bold(original)
        new = Document(io.BytesIO(revised))
        self.assertEqual(count, 2)
        self.assertEqual([[c.text for row in table.rows for c in row.cells]
                          for table in old.tables],
                         [[c.text for row in table.rows for c in row.cells]
                          for table in new.tables])
        ps = new.tables[2].cell(1, 1).paragraphs
        matched = [p for p in ps if p.text.startswith("اکتيۏيتي")]
        self.assertEqual(len(matched), 2)
        for p in matched:
            for run in p.runs:
                self.assertTrue(run.bold)
                self.assertIsNotNone(run._r.get_or_add_rPr().find(qn("w:bCs")))
        for p in ps:
            if p.text.startswith(("2.", "3.")):
                self.assertFalse(any(run._r.get_or_add_rPr().find(qn("w:bCs")) is not None
                                     for run in p.runs))

    def test_pdf_fetches_only_addon_in_v2(self):
        with io.BytesIO() as out:
            with ZipFile(out, "w") as z:
                z.writestr("Pendidikan_Islam/Tahun_5/PDF/CIKGULAJU_RPH_PI_T5_PDP019.pdf",
                           b"%PDF-" + b"0" * 2000)
            with ZipFile(io.BytesIO(out.getvalue())) as fake, \
                 patch.dict(os.environ, {pi.V2_FLAG: "1"}), \
                 patch.object(pi, "_settings", return_value=("https://example.test", "secret")), \
                 patch.object(pi, "_verified_zip", return_value=fake) as read:
                result = pi._file(5, 19, "pdf", {})
                self.assertTrue(result.startswith(b"%PDF-"))
                read.assert_called_once_with("https://example.test", "secret", "v2-bold-pdf")

    def test_word_in_v2_also_has_complex_script_bold(self):
        base = example_word()
        with patch.dict(os.environ, {pi.V2_FLAG: "1"}), \
             patch.object(pi, "_file", return_value=base):
            result = pi.request_private_document(5, 19, "word", {}, {})
        changed = Document(result)
        self.assertEqual(changed.tables[1].cell(0, 1).text, "4.1 Merumus")
        self.assertTrue(any(run._r.get_or_add_rPr().find(qn("w:bCs")) is not None
                            for run in changed.tables[2].cell(1, 1).paragraphs[1].runs))


if __name__ == "__main__":
    unittest.main()
