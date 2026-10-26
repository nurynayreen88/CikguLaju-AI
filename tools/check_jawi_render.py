"""Non-destructive Jawi rendering diagnostic. Run: python tools/check_jawi_render.py --out /tmp/jawi-check
Requires Pillow and fonttools. Does not import app.py or touch the database.
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, features
from fontTools.ttLib import TTFont

SAMPLES = [
    "ڤنديديقن اسلام",
    "چارا منوليس جاوي",
    "ڠ ڽ ڤ چ ݢ",
    "موريد ممباچ دان منوليس",
]
FONT_PATHS = [
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
]
def cmap(path):
    font = TTFont(str(path), lazy=True)
    try:
        return set().union(*(set(t.cmap) for t in font["cmap"].tables))
    finally:
        font.close()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="/tmp/jawi-check")
    p.add_argument("--font", action="append", help="Additional font file path")
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    chars = {ord(c) for sample in SAMPLES for c in sample if 0x600 <= ord(c) <= 0x8ff}
    results = {"raqm_available": bool(features.check("raqm")), "fonts": []}
    for index, path in enumerate([*FONT_PATHS, *(args.font or [])]):
        fp = Path(path)
        if not fp.is_file():
            results["fonts"].append({"path": path, "status": "missing"})
            continue
        missing = sorted(chars - cmap(fp))
        item = {"path": path, "missing_codepoints": [f"U+{c:04X}" for c in missing]}
        if not results["raqm_available"]:
            item["status"] = "blocked_no_raqm"
        elif missing:
            item["status"] = "blocked_missing_glyphs"
        else:
            font = ImageFont.truetype(str(fp), 42, layout_engine=ImageFont.Layout.RAQM)
            img = Image.new("RGB", (1300, 380), "white")
            draw = ImageDraw.Draw(img)
            for i, sample in enumerate(SAMPLES):
                draw.text((1250, 20 + i * 85), sample, font=font, fill="black", anchor="ra", direction="rtl", language="ms")
            output = out / f"jawi_font_{index}.png"
            img.save(output)
            item.update(status="rendered_requires_visual_review", image=str(output))
        results["fonts"].append(item)
    (out / "report.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if not results["raqm_available"] or not any(x.get("status") == "rendered_requires_visual_review" for x in results["fonts"]):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
