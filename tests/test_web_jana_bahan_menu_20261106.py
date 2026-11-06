"""RPH Web uses one Jana Bahan action and original Telegram-native RPH routes."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf-8")


class JanaBahanWebTests(unittest.TestCase):
    def test_existing_title_and_selection_are_preserved(self):
        self.assertIn('<h2 id="view-rph-heading">Sediakan RPH</h2>',HTML)
        for field in ("year", "subject", "unit", "lesson", "teacher-class",
                      "teacher-date", "teacher-time-start", "teacher-time-end"):
            self.assertIn('id="'+field+'"',HTML)

    def test_materials_appear_after_button(self):
        self.assertIn('id="show-materials" type="button" hidden disabled>Jana Bahan',HTML)
        self.assertIn('id="materials-panel" hidden',HTML)
        for label in ("RPH PDF", "RPH Word", "Buku Teks", "Audio", "Buku Aktiviti"):
            self.assertIn(label,HTML)
        self.assertIn('document.getElementById("show-materials").addEventListener',HTML)

    def test_rph_downloads_use_existing_native_generator(self):
        self.assertIn('onDownload:()=>generateRphFile("pdf")',HTML)
        self.assertIn('onDownload:()=>generateRphFile("word")',HTML)
        self.assertIn('"/api/web/rph/pdf?"',HTML)
        self.assertIn('"/api/web/rph/word?"',HTML)
        self.assertIn('X-RPH-Generator',HTML)
        self.assertIn('telegram-native',HTML)

    def test_unverified_telegram_assets_remain_disabled(self):
        self.assertIn('Sumber fail tambahan Telegram belum membenarkan muat turun',HTML)
        self.assertIn('action.disabled=!ready',HTML)
        self.assertIn('data.download_enabled===true',HTML)
        self.assertIn('item.download_enabled!==true',HTML)
        self.assertIn('tiada',HTML.lower())
        self.assertNotIn('#show-materials,#materials-panel{display:none!important}',HTML)

    def test_do_not_enable_fake_bundle(self):
        self.assertIn('id="download-all" type="button" hidden disabled',HTML)


if __name__=="__main__":
    unittest.main()
