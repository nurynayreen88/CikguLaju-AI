#!/usr/bin/env python3
"""Pre-deploy non-destructive checks for PI mixed Jawi/Latin PDF rendering."""
from pathlib import Path
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont, features
import sys

ROOT = Path(__file__).resolve().parents[1]
TEXT = [
    "ڤنديديقن اسلام: Guru / Aktiviti 1",
    "ڬورو: SK 3.1 / SP 3.1.4",
    "موريد: 10/20 - (Refleksi)",
    "بهن بنتو مڠاجر: Buku / PDF",
]
REQUIRED = {ord(c) for s in TEXT for c in s if not c.isspace()}
if not features.check("raqm"):
    raise SystemExit("FAIL: Pillow RAQM missing")
for weight in ("Regular", "Bold"):
    path = ROOT / "fonts" / "jawi" / ("Amiri-" + weight + ".ttf")
    if not path.exists():
        raise SystemExit("FAIL: Amiri font missing: " + str(path))
    font = TTFont(str(path))
    try:
        cmap = set().union(*(set(t.cmap) for t in font["cmap"].tables))
    finally:
        font.close()
    missing = sorted(REQUIRED - cmap)
    if missing:
        raise SystemExit("FAIL: missing glyphs " + str([hex(x) for x in missing]))
    pil_font = ImageFont.truetype(str(path), 42, layout_engine=ImageFont.Layout.RAQM)
    img = Image.new("RGB", (1300, 340), "white")
    draw = ImageDraw.Draw(img)
    for i, s in enumerate(TEXT):
        draw.text((1250, 10 + 75*i), s, font=pil_font, fill="black",
                  anchor="ra", direction="rtl", language="ms")
    target = ROOT / ("pi_mixed_jawi_" + weight.lower() + ".png")
    img.save(target)
    print("PASS:", weight, "glyphs and RAQM; sample:", target)
print("PASS: mixed Jawi/Latin/:/ glyph coverage")
