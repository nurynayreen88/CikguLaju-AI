"""End-to-end RAQM Jawi smoke test, independent of production DB and Telegram."""
import glob
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, features
from fontTools.ttLib import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import fitz

SAMPLE = "ڤنديديقن اسلام: موريد ممباچ دان منوليس جاوي دڠن بتول."

def find_font():
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
    ]
    candidates += glob.glob("/usr/share/fonts/**/*Arabic*.ttf", recursive=True)
    needed = {ord(c) for c in SAMPLE if 0x0600 <= ord(c) <= 0x08ff}
    for path in dict.fromkeys(candidates):
        if not Path(path).is_file():
            continue
        font = TTFont(path, lazy=True)
        try:
            cmap = set()
            for table in font["cmap"].tables:
                cmap.update(table.cmap.keys())
            if needed.issubset(cmap):
                return path
        finally:
            font.close()
    return None

class JawiRaqmSmokeTests(unittest.TestCase):
    def test_jawi_raqm_to_pdf(self):
        self.assertTrue(features.check("raqm"), "Pillow RAQM/HarfBuzz missing")
        font_path = find_font()
        self.assertIsNotNone(font_path, "No font covers sample Jawi codepoints")
        font = ImageFont.truetype(font_path, 56, layout_engine=ImageFont.Layout.RAQM)
        im = Image.new("RGB", (1400, 200), "white")
        draw = ImageDraw.Draw(im)
        draw.text((1350, 35), SAMPLE, font=font, fill="black",
                  direction="rtl", anchor="ra")
        self.assertIsNotNone(im.getbbox())
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "jawi-smoke.pdf")
            pdf = canvas.Canvas(path, pagesize=(595.28, 841.89))
            pdf.drawImage(ImageReader(im), 40, 600, width=515, height=74)
            pdf.showPage()
            pdf.save()
            doc = fitz.open(path)
            try:
                self.assertEqual(len(doc), 1)
                self.assertGreaterEqual(len(doc[0].get_images(full=True)), 1)
            finally:
                doc.close()

if __name__ == "__main__":
    unittest.main()
