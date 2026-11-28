"""RPT2027: five table headings translated to subject language.

Arabic/Jawi pages remain physically RTL; English and all other subjects LTR.
Source cover is intentionally the SAME Malay profile template for all 56 PDFs.
"""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
import fitz

from rpt_2027.common.format_2026_layout_preview import (
    build_preview, LOCALIZED_TABLE_HEADINGS, DEFAULT_TABLE_HEADINGS,
)


def item(n):
    return {
        "id": f"{n:03d}", "week": "M02",
        "a_start": "2027-01-10", "a_end": "2027-01-14",
        "b_start": "2027-01-11", "b_end": "2027-01-15",
        "unit": "Bidang: القرءان",
        "topic": "درس القراءة العربية",
        "sk": "1.1", "sp": "1.1.1",
        "note": "Rujukan buku teks (DRAF).",
    }


def is_arabic(text):
    return any("\u0600" <= c <= "\u08ff" or "\ufb50" <= c <= "\ufeff" for c in text)


def actual_header_spans(page):
    """Read only the yellow first header row, not body words or page title."""
    return [s for b in page.get_text("dict")["blocks"]
            for l in b.get("lines", [])
            for s in l["spans"]
            if 46 <= s["bbox"][1] < 86 and
            s["bbox"][3] < 90 and s["text"].strip()]


class TableDirectionAndLanguageRegression(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def pdf(self, subject):
        dest = self.path/(subject + ".pdf")
        build_preview(subject, 4, [item(1), item(2)], dest, max_span_rows=2)
        doc = fitz.open(dest)
        self.assertEqual(doc.page_count, 2)
        for label in ("LOGO SEKOLAH", "NAMA SEKOLAH", "NAMA GURU"):
            self.assertIn(label, doc[0].get_text("text"))
        return doc

    def test_expected_native_headings_declared(self):
        self.assertEqual(set(LOCALIZED_TABLE_HEADINGS),
                         {"pendidikan_islam", "bahasa_arab", "english"})
        self.assertEqual(len(DEFAULT_TABLE_HEADINGS), 5)
        self.assertTrue(all(all(is_arabic(x) for x in values)
                            for key, values in LOCALIZED_TABLE_HEADINGS.items()
                            if key != "english"))
        self.assertTrue(all(all(c.isascii() for c in x)
                            for x in LOCALIZED_TABLE_HEADINGS["english"]))
        self.assertIn("ستندرد", LOCALIZED_TABLE_HEADINGS["pendidikan_islam"][2])
        self.assertIn("المحتوى", LOCALIZED_TABLE_HEADINGS["bahasa_arab"][2])
        self.assertEqual(LOCALIZED_TABLE_HEADINGS["english"][2],
                         "CONTENT STANDARD")

    def test_jawi_arabic_five_rtl_native_script_headers(self):
        # Physical original left-edge table columns in RTL are note|SP|SK|
        # unit|week. Numeric positions are source-layout-specific and stable.
        band_edges = [29, 193, 403, 528, 708, 813]
        for subject in ("pendidikan_islam", "bahasa_arab"):
            with self.subTest(subject=subject), self.pdf(subject) as pdf:
                page = pdf[1]
                headings = actual_header_spans(page)
                text = "\n".join(x["text"] for x in headings)
                self.assertNotIn("MINGGU / TARIKH", text)
                self.assertNotIn("CATATAN / BAHAN", text)
                # Every one of the five physical header cells must contain
                # Arabic/Jawi glyphs rather than Latin Malay headings.
                for x0,x1 in zip(band_edges,band_edges[1:]):
                    band = [s for s in headings if x0<=s["bbox"][0]<x1]
                    self.assertTrue(band,(subject,x0,text))
                    self.assertTrue(any(is_arabic(s["text"]) for s in band),
                                    (subject,x0,band))
                self.assertIn("PdP 001",page.get_text())
                self.assertIn("PdP 002",page.get_text())
                self.assertEqual(page.get_text().count("M02"),1)
                self.assertIn("1.1.1",page.get_text())

    def test_english_five_english_ltr_headers(self):
        with self.pdf("english") as pdf:
            page = pdf[1]
            spans = actual_header_spans(page)
            text = "\n".join(s["text"] for s in spans)
            for head in LOCALIZED_TABLE_HEADINGS["english"]:
                self.assertIn(head,text)
            self.assertNotIn("MINGGU / TARIKH",text)
            self.assertNotIn("CATATAN / BAHAN",text)
            self.assertFalse(any(is_arabic(s["text"]) for s in spans))
            locations = [next(s["bbox"][0] for s in spans if s["text"]==x)
                         for x in LOCALIZED_TABLE_HEADINGS["english"]]
            self.assertEqual(locations,sorted(locations))

    def test_other_subjects_keep_malay_ltr_header(self):
        with self.pdf("matematik") as pdf:
            spans = actual_header_spans(pdf[1])
            self.assertEqual({s["text"] for s in spans},set(DEFAULT_TABLE_HEADINGS))
            locations = [next(s["bbox"][0] for s in spans if s["text"]==x)
                         for x in DEFAULT_TABLE_HEADINGS]
            self.assertEqual(locations,sorted(locations))


if __name__ == "__main__":
    unittest.main()
