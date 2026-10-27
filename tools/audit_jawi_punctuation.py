"""Audit Jawi punctuation glyph coverage without modifying source text or app state.

Usage: python tools/audit_jawi_punctuation.py /path/to/jawi-font.ttf [/path/to/fallback.ttf]
Requires fonttools. Exit 0 only if every sample character is covered by at least one font.
This is a coverage check, not a substitute for RTL/RAQM PDF visual verification.
"""
import argparse
import json
from pathlib import Path
from fontTools.ttLib import TTFont

SAMPLES = (
    "ڤنديديقن اسلام – جاوي",
    "اکتيۏيتي 1 – ممباچ",
    "موريد ممباچ دان منوليس",
    "ڠ ڽ ڤ چ ݢ",
    "Jawi / Rumi - 2026: (1) & 2",
)

def coverage(path):
    font = TTFont(str(path), lazy=True)
    try:
        return set().union(*(set(t.cmap.keys()) for t in font["cmap"].tables))
    finally:
        font.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fonts", nargs="+", type=Path)
    args = parser.parse_args()
    font_maps = []
    for path in args.fonts:
        if not path.is_file():
            parser.error(f"Font not found: {path}")
        font_maps.append((str(path), coverage(path)))
    chars = sorted({ord(c) for s in SAMPLES for c in s if not c.isspace()})
    report = {
        "fonts": [p for p, _ in font_maps],
        "missing": [
            {"character": chr(cp), "codepoint": f"U+{cp:04X}"}
            for cp in chars if not any(cp in cmap for _, cmap in font_maps)
        ],
        "fallback_needed": [
            {"character": chr(cp), "codepoint": f"U+{cp:04X}",
             "font": next((p for p, cmap in font_maps[1:] if cp in cmap), None)}
            for cp in chars if cp not in font_maps[0][1]
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(1 if report["missing"] else 0)

if __name__ == "__main__":
    main()
