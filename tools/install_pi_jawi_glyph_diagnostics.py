#!/usr/bin/env python3
"""Non-destructive runtime diagnostics for PI Jawi raster glyph failures.

Log codepoints only, never user text. Does not alter output or database.
"""
from pathlib import Path

app=Path(__file__).resolve().parents[1]/"app.py"
source=app.read_text(encoding="utf-8")
marker="# === PI JAWI GLYPH DIAGNOSTICS 20261029 ==="
if marker in source:
    print("PI glyph diagnostics already installed")
    raise SystemExit(0)
if "CIKGULAJU_PATCH_PI_JAWI_STRICT_20261027" not in source:
    raise RuntimeError("PI raster renderer guard missing; refusing to instrument")
patch='''
# === PI JAWI GLYPH DIAGNOSTICS 20261029 ===
_PI_JAWI_DIAG_BASE = _JawiRasterParagraph_v25213
class _JawiRasterParagraph_v25213(_PI_JAWI_DIAG_BASE):
    def wrap(self, availWidth, availHeight):
        from collections import Counter
        from pathlib import Path
        from PIL import features
        import os
        path = _pi_exact_jawi_font_v2604(
            self.text, bool(getattr(self, 'bold', False)))
        cmap = _font_cmap_v25226(path)
        missing = Counter(
            f'U+{ord(ch):04X}' for ch in self.text
            if ord(ch) not in cmap and ch not in '\\n\\r\\t')
        literal_boxes = Counter(
            f'U+{ord(ch):04X}' for ch in self.text
            if ord(ch) in (0x25A1,0x25A0,0xFFFD,0xFFFC,0x2610,0x2611))
        print('PI JAWI GLYPH DIAG',
              'font=',Path(path).name,
              'raqm=',features.check('raqm'),
              'missing=',dict(missing),
              'literal_boxes=',dict(literal_boxes),
              'symbol_patch=',globals().get('CIKGULAJU_PATCH_PI_JAWI_SYMBOL_20261029'),
              flush=True)
        return super().wrap(availWidth, availHeight)
CIKGULAJU_PATCH_PI_JAWI_DIAGNOSTICS_20261029 = True
# === END PI JAWI GLYPH DIAGNOSTICS ===
'''
app.write_text(source+"\n"+patch,encoding="utf-8")
print("PI Jawi diagnostics installed at build")
