#!/usr/bin/env python3
"""Provision Amiri fonts for isolated PI Jawi PDF testing.

Does not change the production font resolver or database.
"""
from pathlib import Path
from urllib.request import urlopen
from fontTools.ttLib import TTFont

DEST = Path(__file__).resolve().parents[1] / "fonts" / "jawi"
BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl/amiri/"
SAMPLE = "ڤنديديقن اسلام جاوي ڠ چ ڽ ڬ ۏ ڤ ء أ إ ا ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي"
REQUIRED = {ord(c) for c in SAMPLE if 0x0600 <= ord(c) <= 0x08FF}

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for name in ("Amiri-Regular.ttf", "Amiri-Bold.ttf"):
        path = DEST / name
        if not path.is_file() or path.stat().st_size < 10000:
            with urlopen(BASE + name, timeout=35) as response:
                data = response.read(8_000_000)
            if len(data) < 10000:
                raise RuntimeError("Amiri font download incomplete: " + name)
            temp = path.with_suffix(".tmp")
            temp.write_bytes(data)
            temp.replace(path)
        font = TTFont(str(path))
        try:
            cmap = set()
            for t in font["cmap"].tables:
                cmap.update(t.cmap.keys())
        finally:
            font.close()
        missing = REQUIRED - cmap
        if missing:
            raise RuntimeError(name + " missing Jawi glyphs: " + ", ".join("U+%04X" % c for c in sorted(missing)))
        print("Validated:", path)

if __name__ == "__main__":
    main()
