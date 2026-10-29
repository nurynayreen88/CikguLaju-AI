#!/usr/bin/env python3
"""Append a narrowly scoped PI raster glyph fallback at build time.

Fail closed if the expected renderer anchor is missing; never change source
RPH/DB, non-PI flow, or other PDF/Word paths.
"""
from pathlib import Path

app = Path(__file__).resolve().parents[1] / "app.py"
source = app.read_text(encoding="utf-8")
anchor = "CIKGULAJU_PATCH_PI_JAWI_STRICT_20261027"
marker = "# === PI JAWI RASTER SYMBOL FALLBACK 20261029 ==="
if marker in source:
    print("PI Jawi symbol fallback already installed")
    raise SystemExit(0)
if anchor not in source or "class _JawiRasterParagraph_v25213(" not in source:
    raise RuntimeError("PI Jawi renderer anchor not found; refusing to patch")
patch = '''
# === PI JAWI RASTER SYMBOL FALLBACK 20261029 ===
from pi_jawi_symbol_fallback import sanitize_raster_text as _pi_symbol_sanitize
_PI_JAWI_SYMBOL_BASE = _JawiRasterParagraph_v25213
class _JawiRasterParagraph_v25213(_PI_JAWI_SYMBOL_BASE):
    def __init__(self, text, style):
        super().__init__(text, style)
        path = _pi_exact_jawi_font_v2604(
            self.text, bool(getattr(self, 'bold', False)))
        self.text, replaced = _pi_symbol_sanitize(
            self.text, path, _font_cmap_v25226)
        if replaced:
            print('PI JAWI NONARABIC SYMBOL FALLBACK',
                  [f'U+{cp:04X}' for cp in replaced], flush=True)
CIKGULAJU_PATCH_PI_JAWI_SYMBOL_20261029 = 'RENDER_ONLY_NONARABIC_FALLBACK'
# === END PI JAWI RASTER SYMBOL FALLBACK ===
'''
app.write_text(source + "\n" + patch, encoding="utf-8")
print("PI Jawi render-only fallback installed into build artifact")
