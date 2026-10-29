#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements.txt
# Install and validate the original font set first (preserves baseline checks).
python tools/provision_pi_jawi_fonts.py
# Amiri experiment: replace only the font files at the paths already used by
# the existing Noto-based PI Jawi resolver. No app.py or DB changes.
python tools/provision_amiri_jawi.py
python - <<'PY'
from pathlib import Path
from shutil import copyfile
root = Path("fonts/jawi")
for weight in ("Regular", "Bold"):
    source = root / f"Amiri-{weight}.ttf"
    target = root / f"NotoNaskhArabic-{weight}.ttf"
    if not source.is_file() or source.stat().st_size < 10000:
        raise RuntimeError(f"Amiri missing: {source}")
    copyfile(source, target)
    print(f"PI Jawi font override: {target} <- {source}")
PY
python - <<'PY'
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, features
from fontTools.ttLib import TTFont
assert features.check("raqm"), "Amiri test: RAQM shaping is unavailable"
path = Path("fonts/jawi/NotoNaskhArabic-Regular.ttf")
font = TTFont(str(path))
try:
    names = font["name"].names
    families = [n.toUnicode() for n in names if n.nameID == 1]
    assert any("Amiri" in name for name in families), f"Amiri override not active: {families}"
finally:
    font.close()
face = ImageFont.truetype(str(path), 40, layout_engine=ImageFont.Layout.RAQM)
im = Image.new("RGB", (1200, 150), "white")
ImageDraw.Draw(im).text((1150, 35), "ڬورو دان اکتيۏيتي ڤنديديقن اسلام", font=face, direction="rtl", anchor="ra", fill="black")
assert im.getbbox() is not None
print("PI Jawi staging build: Amiri override and RAQM shaping verified")
PY
python -m py_compile app.py
