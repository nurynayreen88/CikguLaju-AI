"""Public 16-subject RPH login gallery: one link, no credits or session."""
from __future__ import annotations

import ast
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOGIN = ROOT / "web_v1_static_preview" / "index.html"
GALLERY = ROOT / "web_v1_static_preview" / "Contoh_RPH_Semua_16.html"
ROUTES = ROOT / "tools" / "run_web_v1_preview.py"

EXPECTED = (
    "Bahasa Melayu", "English", "Matematik", "Sains",
    "Pendidikan Islam (Jawi)", "Bahasa Arab", "Sejarah",
    "Pendidikan Moral", "Pendidikan Jasmani", "Pendidikan Kesihatan",
    "Pendidikan Seni Visual", "Pendidikan Muzik",
    "Reka Bentuk dan Teknologi", "Mathematics DLP",
    "Science DLP", "PPKI",
)


class Sections(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pages = []

    def handle_starttag(self, tag, attrs):
        if tag != "section":
            return
        props = dict(attrs)
        if "page" in props.get("class", "").split():
            self.pages.append(props)


class PublicRphExamplesTests(unittest.TestCase):
    def test_one_public_login_link_to_sixteen_examples(self):
        login = LOGIN.read_text(encoding="utf-8")
        opening = login.split('<details class="public-rph-sample">', 1)[1].split("</details>", 1)[0]
        self.assertIn("16 contoh RPH pelbagai subjek, DLP dan PPKI", opening)
        self.assertEqual(opening.count('href="/contoh-rph-semua"'), 1)
        self.assertNotIn('href="/contoh-rph.pdf"', opening)
        self.assertIn('href="#pilihan-log-masuk"', opening)

    def test_gallery_has_sixteen_a4_samples_and_owner_approved_rtl(self):
        page = GALLERY.read_text(encoding="utf-8")
        parser = Sections()
        parser.feed(page)
        self.assertEqual(len(parser.pages), 16)
        for i, section in enumerate(parser.pages, 1):
            self.assertEqual(section.get("id"), f"rph-contoh-{i}")
            self.assertEqual(section.get("class"), "page rtl" if i in (5, 6) else "page ltr")
        self.assertIn("@page { size: A4", page)
        self.assertIn(".ltr .hero {direction:ltr !important; flex-direction:row !important;}", page)
        self.assertIn(".rtl .hero {direction:rtl !important; flex-direction:row !important;}", page)
        self.assertIn("Cetak / Simpan PDF", page)
        self.assertIn('href="/contoh-rph-semua.pdf"', page)
        self.assertIn("@media print", page)
        self.assertIn("window.print()", page)
        self.assertIn("Kembali ke log masuk", page)
        for name in EXPECTED:
            self.assertIn(name, page)
        self.assertEqual(page.count('class="teacher-row"'), 16 * 4)
        self.assertNotIn("____", page)
        self.assertNotRegex(page, r'<td class="label">\s*(?:Mata Pelajaran|Subject|مات ڤلاجرن|المادة)\s*</td>')
        for i in range(1, 17):
            section = page.split(f'<section id="rph-contoh-{i}"', 1)[1]
            if i < 16:
                section = section.split(f'<section id="rph-contoh-{i+1}"', 1)[0]
            self.assertIn('class="hero"', section)
            self.assertIn('class="teacher"', section)
            self.assertIn('class="tbl"', section)

    def test_gallery_endpoint_is_public_readonly_and_unchanged_legacy_pdf(self):
        source = ROUTES.read_text(encoding="utf-8")
        tree = ast.parse(source)
        handler = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                       and node.name == "public_all_subject_rph_gallery")
        decorators = [ast.unparse(d) for d in handler.decorator_list]
        self.assertEqual(decorators, ["app.get('/contoh-rph-semua')"])
        body = ast.get_source_segment(source, handler)
        self.assertIn('send_file(PREVIEW.with_name("Contoh_RPH_Semua_16.html")', body)
        self.assertNotIn("credits", body.lower())
        self.assertNotIn("session_ticket", body)
        self.assertNotIn("login_required", body)
        self.assertIn('@app.get("/contoh-rph.pdf")', source)
        self.assertIn('@app.get("/contoh-rph-semua.pdf")', source)
        self.assertIn('return redirect("/contoh-rph-semua", code=302)', source)


if __name__ == "__main__":
    unittest.main()
