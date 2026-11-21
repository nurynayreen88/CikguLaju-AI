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


    def test_all_sixteen_subject_word_download_formats_preserve_every_source_part(self):
        """The actual delivery adapter must handle all gallery categories safely.

        These are source-shaped DOCX fixtures, NOT claims that every real RPH
        or PDF has passed visual review.
        """
        from pathlib import Path
        import json
        from docx.oxml import OxmlElement

        root = Path(__file__).resolve().parents[1]
        manifest = json.loads(
            (root / "web/rph_login_canonical_layout_20261121.json").read_text("utf-8")
        )
        self.assertEqual(len(manifest["subjects"]), 16)
        headings = {
            "BM": "Aktiviti 1 (15 minit): Perbincangan",
            "ENGLISH": "Activity 1 (10 minutes): Guided Practice",
            "MATH": "1. Aktiviti 1: Susun Nombor",
            "SCIENCE": "Langkah 1 – Pemerhatian",
            "PI": "اکتيۏيتي ١",
            "ARAB": "النشاط ٢: مناقشة",
            "SEJARAH": "Aktiviti 2: Garis Masa",
            "MORAL": "Aktiviti 3: Nilai Murni",
            "PJ": "Langkah 2: Latih Tubi",
            "PK": "Aktiviti 1: Pendidikan Kesihatan",
            "PSV": "Aktiviti 2: Hasil Karya",
            "MUSIC": "Aktiviti 1 – Irama",
            "RBT": "Aktiviti 3: Reka Bentuk",
            "DLP_MATH": "Activity 2: Number Line",
            "DLP_SCIENCE": "Step 3: Investigate",
            "PPKI": "Aktiviti 1: Kenal Pasti",
        }
        self.assertEqual(set(headings), {item["subject_code"] for item in manifest["subjects"]})
        for item in manifest["subjects"]:
            code = item["subject_code"]
            heading = headings[code]
            with self.subTest(subject=code):
                doc = Document()
                doc.add_paragraph(code)
                info = doc.add_table(rows=2, cols=2)
                info.cell(0, 0).text = "Standard Kandungan"
                info.cell(0, 1).text = "3.1 Standard kandungan asal"
                info.cell(1, 0).text = "Standard Pembelajaran"
                info.cell(1, 1).text = "3.1.2 Standard pembelajaran asal"
                activity = doc.add_table(rows=2, cols=3)
                activity.cell(0, 1).text = "Aktiviti Pengajaran"
                activity.cell(1, 0).text = "Aktiviti Utama"
                body = activity.cell(1, 1).paragraphs[0]
                instruction = (
                    "المعلم يشرح الموضوع." if code == "ARAB" else
                    "موريد منوليس جاوابن." if code == "PI" else
                    "Guru menerangkan dan murid menulis jawapan."
                )
                body.add_run(heading + "\n" + instruction)
                activity.cell(1, 2).text = "Pentaksiran asal"
                if item["direction"] == "rtl":
                    activity._tbl.tblPr.append(OxmlElement("w:bidiVisual"))
                    body._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
                original = BytesIO()
                doc.save(original)
                original_bytes = original.getvalue()
                first, first_words = _read(original_bytes)
                first_breaks = len(list(first.iter(W + "br")))
                with ZipFile(BytesIO(original_bytes)) as z:
                    other_parts = {
                        name: z.read(name) for name in z.namelist()
                        if name != DOC
                    }

                styled = style_word_activity_titles(original)
                result_bytes = styled.getvalue()
                self.assertNotEqual(result_bytes, original_bytes)
                updated, updated_words = _read(result_bytes)
                self.assertEqual(first_words, updated_words)
                self.assertEqual(first_breaks, len(list(updated.iter(W + "br"))))
                with ZipFile(BytesIO(result_bytes)) as z:
                    self.assertIsNone(z.testzip())
                    self.assertEqual(
                        other_parts,
                        {name: z.read(name) for name in z.namelist() if name != DOC}
                    )
                word = Document(BytesIO(result_bytes))
                self.assertEqual(len(word.tables), 2)
                self.assertEqual(word.tables[0].cell(1, 1).text,
                                 "3.1.2 Standard pembelajaran asal")
                self.assertEqual(word.tables[1].cell(1, 2).text, "Pentaksiran asal")
                self.assertEqual(word.tables[1].cell(1, 1).text,
                                 heading + "\n" + instruction)
                lines = {}
                for run in updated.iter(W + "r"):
                    value = "".join(t.text or "" for t in run.findall(W + "t"))
                    if value:
                        props = run.find(W + "rPr")
                        lines[value] = (
                            props is not None and props.find(W + "b") is not None,
                            props is not None and props.find(W + "bCs") is not None,
                        )
                self.assertEqual(lines[heading], (True, True))
                self.assertEqual(lines[instruction], (False, False))
                self.assertEqual(
                    len(list(first.iter(W + "bidiVisual"))),
                    len(list(updated.iter(W + "bidiVisual")))
                )
                self.assertIs(style_word_activity_titles(styled), styled)

    def test_multi_subject_instruction_guard_never_bolds_a_full_sentence(self):
        for example in (
            "Aktiviti 1: Guru menerangkan langkah pengajaran",
            "Langkah 2 - Murid melaksanakan tugasan",
            "Activity 2: Students draw a picture",
            "Step 3: Teacher explains the topic",
            "اکتيۏيتي ١: موريد منوليس جاوابن",
            "النشاط ٢: المعلم يشرح الموضوع",
        ):
            self.assertFalse(_is_activity_heading(example), example)


    def test_prebolded_jawi_and_arabic_word_headings_require_complex_bold(self):
        """Word may have w:b=1 but w:bCs missing/false: repair RTL only."""
        from docx.oxml.ns import qn

        for heading, empty_cs in (
            ("اکتيۏيتي ١", True),
            ("النشاط ٢: مناقشة", False),
        ):
            with self.subTest(heading=heading):
                doc = Document()
                table = doc.add_table(rows=2, cols=2)
                table.cell(0, 0).text = "Standard Pembelajaran"
                table.cell(0, 1).text = "3.1.2 Maklumat sumber asal"
                paragraph = table.cell(1, 1).paragraphs[0]
                title = paragraph.add_run(heading)
                title.bold = True  # Legacy Latin bold already exists.
                if not empty_cs:
                    title.font.cs_bold = False  # Explicitly disabled.
                paragraph.add_run("\n" + "موريد منوليس جاوابن.")
                original = BytesIO()
                doc.save(original)
                prior_root, prior_words = _read(original.getvalue())
                prior_breaks = len(list(prior_root.iter(W + "br")))

                updated = style_word_activity_titles(original)
                after_root, after_words = _read(updated.getvalue())
                self.assertEqual(after_words, prior_words)
                self.assertEqual(prior_breaks, len(list(after_root.iter(W + "br"))))
                word = Document(BytesIO(updated.getvalue()))
                self.assertEqual(
                    word.tables[0].cell(0, 1).text, "3.1.2 Maklumat sumber asal"
                )
                out_runs = word.tables[0].cell(1, 1).paragraphs[0].runs
                self.assertEqual(out_runs[0].text, heading)
                self.assertTrue(out_runs[0].bold)
                props = out_runs[0]._r.get_or_add_rPr()
                self.assertEqual(props.find(qn("w:bCs")).get(qn("w:val")), "1")
                self.assertFalse(out_runs[-1].bold)
                self.assertIs(style_word_activity_titles(updated), updated)

    def test_latin_heading_already_bold_is_not_repacked_for_missing_bcs(self):
        doc = Document()
        table = doc.add_table(rows=1, cols=2)
        para = table.cell(0, 1).paragraphs[0]
        para.add_run("Aktiviti 1: Perbincangan").bold = True
        para.add_run("\nGuru menerangkan konsep.")
        original = BytesIO()
        doc.save(original)
        self.assertIs(style_word_activity_titles(original), original)


    def test_native_tabs_and_cr_breaks_are_preserved_while_activity_titles_bold(self):
        """Word-generated tab and w:cr must not disable source-safe heading style."""
        from docx.oxml import OxmlElement

        doc = Document()
        doc.add_paragraph("RPH asal")
        table = doc.add_table(rows=3, cols=2)
        table.cell(0, 0).text = "Standard Pembelajaran"
        table.cell(0, 1).text = "2.2.1 Murid mengenal pasti bahan."
        first = table.cell(1, 1).paragraphs[0]
        first.add_run("Aktiviti 1\t\nMurid memerhati objek.")
        second = table.cell(2, 1).paragraphs[0]
        title = second.add_run("Activity 2: Matching")
        title._r.append(OxmlElement("w:cr"))
        second.add_run("Pupils record two examples.")
        original = BytesIO()
        doc.save(original)
        old_root, original_words = _read(original.getvalue())
        prior_counts = tuple(len(list(old_root.iter(W + suffix))) for suffix in ("br", "cr", "tab"))
        self.assertEqual(prior_counts, (1, 1, 1))

        styled = style_word_activity_titles(original)
        self.assertIsNot(styled, original)
        new_root, updated_words = _read(styled.getvalue())
        self.assertEqual(original_words, updated_words)
        self.assertEqual(prior_counts, tuple(
            len(list(new_root.iter(W + suffix))) for suffix in ("br", "cr", "tab"
        ))
        word = Document(BytesIO(styled.getvalue()))
        self.assertEqual(word.tables[0].cell(0, 1).text,
                         "2.2.1 Murid mengenal pasti bahan.")
        styled_runs = []
        for run in new_root.iter(W + "r"):
            value = "".join(n.text or "" for n in run.findall(W + "t"))
            if value:
                props = run.find(W + "rPr")
                styled_runs.append((value, props is not None and props.find(W + "b") is not None))
        flags = dict(styled_runs)
        self.assertTrue(flags["Aktiviti 1"])
        self.assertTrue(flags["Activity 2: Matching"])
        self.assertFalse(flags["Murid memerhati objek."])
        self.assertFalse(flags["Pupils record two examples."])
        self.assertIs(style_word_activity_titles(styled), styled)

    def test_single_line_tab_separated_teacher_instruction_not_bold(self):
        """A tab alone must not promote a full instruction to an activity title."""
        doc = Document()
        table = doc.add_table(rows=1, cols=1)
        table.cell(0, 0).paragraphs[0].add_run(
            "Aktiviti 1:\tGuru menerangkan kaedah."
        )
        original = BytesIO()
        doc.save(original)
        self.assertIs(style_word_activity_titles(original), original)


if __name__ == "__main__":
    unittest.main()
