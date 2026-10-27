#!/usr/bin/env python3
"""Provision Noto Naskh Arabic at build time for the PI Jawi PDF renderer.

Run AFTER pip install -r requirements.txt. Fails the build if either font
cannot be downloaded or its required Jawi codepoints are missing.
No database, application state, or user data is touched.
"""
import os
from pathlib import Path
from urllib.request import urlopen
from fontTools.ttLib import TTFont

DEST = Path(__file__).resolve().parents[1] / "fonts" / "jawi"
BASE = "https://notofonts.github.io/arabic/fonts/NotoNaskhArabic/hinted/ttf/"
# Covers Malay Jawi letters as well as common Arabic letters and marks.
SAMPLE = "ڤنديديقن اسلام جاوي ڠ چ ڽ ڬ ۏ ڤ ء أ إ ا ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي"
REQUIRED = {ord(ch) for ch in SAMPLE if 0x0600 <= ord(ch) <= 0x08FF}

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for name in ("NotoNaskhArabic-Regular.ttf", "NotoNaskhArabic-Bold.ttf"):
        target = DEST / name
        if not target.is_file() or target.stat().st_size < 10000:
            with urlopen(BASE + name, timeout=35) as response:
                payload = response.read(8_000_000)
            if len(payload) < 10000:
                raise RuntimeError("Font download incomplete: " + name)
            temp = target.with_suffix(".tmp")
            temp.write_bytes(payload)
            os.replace(temp, target)
        font = TTFont(str(target), lazy=True)
        try:
            cmap = set()
            for table in font["cmap"].tables:
                cmap.update(table.cmap.keys())
        finally:
            font.close()
        missing = REQUIRED - cmap
        if missing:
            raise RuntimeError(name + " lacks Jawi glyphs: " +
                               ", ".join("U+%04X" % cp for cp in sorted(missing)))
        print("Validated Jawi font:", target, "bytes:", target.stat().st_size)

if __name__ == "__main__":
    main()
