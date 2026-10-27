"""Reproduce Jawi raster line wrapping with the actual Pillow drawing path.

Standalone: python tools/reproduce_jawi_wrap.py
Does not import app.py or access the database.
"""
from PIL import Image, ImageDraw, ImageFont, features
import pathlib

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf",
]
SAMPLE = "موريد ممباچ دان منوليس ڤنديديقن اسلام دڠن ݢورو ڤاݢي اين"
OUTPUT = pathlib.Path("jawi_wrap_diagnostic.png")


def wrap_line(draw, line, font, maxpx):
    words = line.split()
    if not words:
        return [""]
    lines, current = [], ""
    for word in words:
        candidate = word if not current else current + " " + word
        width = draw.textbbox((0, 0), candidate, font=font, direction="rtl", language="ms")
        if current and width[2] - width[0] > maxpx:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def main():
    font_path = next((p for p in FONT_CANDIDATES if pathlib.Path(p).is_file()), None)
    if not font_path:
        raise RuntimeError("No Jawi font installed")
    if not features.check("raqm"):
        raise RuntimeError("RAQM unavailable; Jawi shaping test is invalid")
    font = ImageFont.truetype(font_path, 34, layout_engine=ImageFont.Layout.RAQM)
    image = Image.new("RGB", (900, 400), "white")
    draw = ImageDraw.Draw(image)
    lines = wrap_line(draw, SAMPLE, font, 750)
    assert " ".join(lines) == SAMPLE, "Text was lost or reordered by wrapping"
    for index, line in enumerate(lines):
        draw.text((875, 25 + index * 75), line, font=font, fill="black",
                  anchor="ra", direction="rtl", language="ms")
    image.save(OUTPUT)
    print("Font:", font_path)
    print("RAQM:", features.check("raqm"))
    print("Wrapped lines:", len(lines))
    print("Output:", OUTPUT)


if __name__ == "__main__":
    main()
