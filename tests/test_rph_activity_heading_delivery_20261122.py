"""Protect academic RPH content while bolding existing activity headings."""
from __future__ import annotations

from io import BytesIO
import unittest
from zipfile import ZipFile

from docx import Document
from lxml import etree

from web.rph_activity_heading_delivery import (
    DOC, W, _is_activity_heading, style_word_activity_titles,
)


def _sample():
    doc = Document()
    doc.add_paragraph("RANCANGAN PENGAJARAN HARIAN")
    table = doc.add_table(rows=3, cols=2)
    table.cell(0, 0).text = "Standard Kandungan"
    table.cell(0, 1).text = "4.1 Memahami persekitaran"
    table.cell(1, 0).text = "Aktiviti Utama"
    para = table.cell(1, 1).paragraphs[0]
    para.add_run("Aktiviti 1")
    para.add_run(
        "\nMurid mengenal pasti bentuk."
        "\nAktiviti 2: Perbincangan"
        "\nGuru membuat rumusan."
    )
    table.cell(2, 1).text = "Aktiviti 3: Guru menerangkan langkah amali."
    out = BytesIO()
    doc.save(out)
    return out


def _read(data):
    with ZipFile(BytesIO(data)) as package:
        assert package.testzip() is None
        root = etree.fromstring(package.read(DOC))
    return root, tuple(node.text for node in root.iter(W + "t"))


class ActivityTitleWordRegression(unittest.TestCase):
    def test_existing_headings_bold_without_rewriting_source(self):
        original = _sample()
        prior, prior_words = _read(original.getvalue())
        styled = style_word_activity_titles(original)
        new, new_words = _read(styled.getvalue())
        self.assertEqual(prior_words, new_words)
        self.assertNotEqual(original.getvalue(), styled.getvalue())
        self.assertEqual(len(list(prior.iter(W + "br"))), len(list(new.iter(W + "br"))))
        found = {}
        for run in new.iter(W + "r"):
            props = run.find(W + "rPr")
            bold = props is not None and props.find(W + "b") is not None
            for word in run.iter(W + "t"):
                found[word.text] = bold
        self.assertTrue(found["Aktiviti 1"])
        self.assertTrue(found["Aktiviti 2: Perbincangan"])
        self.assertFalse(found["Murid mengenal pasti bentuk."])
        self.assertFalse(found["Guru membuat rumusan."])
        self.assertFalse(found["Aktiviti 3: Guru menerangkan langkah amali."])
        self.assertEqual(
            Document(BytesIO(styled.getvalue())).tables[0].cell(0, 1).text,
            "4.1 Memahami persekitaran",
        )

    def test_idempotence_and_unknown_data_unchanged(self):
        original = _sample()
        styled = style_word_activity_titles(original)
        self.assertIs(style_word_activity_titles(styled), styled)
        unknown = BytesIO(b"invalid")
        self.assertIs(style_word_activity_titles(unknown), unknown)

    def test_optional_ooxml_dependency_absence_keeps_original_word(self):
        from unittest.mock import patch
        from web import rph_activity_heading_delivery as formatter
        original = _sample()
        with patch.object(formatter, "etree", None):
            self.assertIs(formatter.style_word_activity_titles(original), original)

    def test_instructions_are_not_misidentified_as_titles(self):
        for text in (
            "Aktiviti 1: Guru menunjukkan kad.",
            "Aktiviti 2: Murid menyenaraikan jawapan.",
            "Activity 3: Students draw the diagram.",
        ):
            self.assertFalse(_is_activity_heading(text), text)
        for text in ("Aktiviti 1", "Aktiviti 2: Perbincangan", "Activity 3"):
            self.assertTrue(_is_activity_heading(text), text)


    def test_actual_word_path_styles_jawi_and_arabic_headings_safely(self):
        doc = Document()
        doc.add_paragraph("RPH asal tidak diubah")
        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "SK"
        table.cell(0, 1).text = "2.1.1 Standard asal"
        paragraph = table.cell(1, 1).paragraphs[0]
        paragraph.add_run(
            "اکتيۏيتي ١\nموريد منوليس جاوابن."
            "\nالنشاط ٢: مناقشة\nالمعلم يشرح الموضوع."
        )
        original = BytesIO()
        doc.save(original)
        _, original_words = _read(original.getvalue())
        styled = style_word_activity_titles(original)
        updated, updated_words = _read(styled.getvalue())
        self.assertEqual(original_words, updated_words)
        found = {}
        for run in updated.iter(W + "r"):
            props = run.find(W + "rPr")
            bold = props is not None and props.find(W + "b") is not None
            for word in run.iter(W + "t"):
                found[word.text] = bold
        self.assertTrue(found["اکتيۏيتي ١"])
        self.assertTrue(found["النشاط ٢: مناقشة"])
        self.assertFalse(found["موريد منوليس جاوابن."])
        self.assertFalse(found["المعلم يشرح الموضوع."])
        self.assertEqual(
            Document(BytesIO(styled.getvalue())).tables[0].cell(0, 1).text,
            "2.1.1 Standard asal",
        )

    def test_jawi_arabic_instructions_not_mistaken_for_headings(self):
        for value in (
            "اکتيۏيتي ١: موريد منوليس جاوابن",
            "النشاط ٢: المعلم يشرح الموضوع",
        ):
            self.assertFalse(_is_activity_heading(value), value)
        for value in ("اکتيۏيتي ١", "النشاط ٢: مناقشة"):
            self.assertTrue(_is_activity_heading(value), value)


if __name__ == "__main__":
    unittest.main()
