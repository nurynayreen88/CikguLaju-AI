#!/usr/bin/env python3
"""Make the existing PI Jawi PDF resolver use the validated project Amiri font.

The build script installs Amiri under fonts/jawi. This patch only changes the
PI Jawi raster font resolver; other subjects and databases are untouched.
"""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"app.py"
s=p.read_text(encoding="utf-8")
marker="# === PI JAWI PROJECT AMIRI PRIORITY 20261029 ==="
if marker in s:
    print("PI project Amiri priority already present")
    raise SystemExit(0)
if "CIKGULAJU_PATCH_PI_JAWI_STRICT_20261027" not in s:
    raise RuntimeError("Expected PI Jawi font guard missing")
patch = '''
# === PI JAWI PROJECT AMIRI PRIORITY 20261029 ===
_PI_JAWI_AMIRI_PREVIOUS_RESOLVER = _pi_exact_jawi_font_v2604
def _pi_exact_jawi_font_v2604(text, bold=False):
    import os
    from pathlib import Path
    candidate = Path(__file__).resolve().parent / 'fonts' / 'jawi' / (
        'Amiri-Bold.ttf' if bold else 'Amiri-Regular.ttf')
    required = {ord(ch) for ch in str(text or '') if not ch.isspace()}
    if candidate.is_file():
        cmap = _font_cmap_v25226(str(candidate))
        if required.issubset(cmap):
            return str(candidate)
        # Jawi codepoints must be complete; punctuation/Latin may be handled
        # by the existing fallback when this font does not cover them.
        print('PI AMIRI FONT COVERAGE GAP',
              [f'U+{x:04X}' for x in sorted(required-cmap)],flush=True)
    return _PI_JAWI_AMIRI_PREVIOUS_RESOLVER(text,bold)
def _pi_jawi_font_v2606(text,bold=False):
    return _pi_exact_jawi_font_v2604(text,bold)
CIKGULAJU_PATCH_PI_AMIRI_PRIORITY_20261029 = True
# === END PI JAWI PROJECT AMIRI PRIORITY ===
'''
p.write_text(s+"\n"+patch,encoding="utf-8")
print("PI Jawi project Amiri font priority installed")
