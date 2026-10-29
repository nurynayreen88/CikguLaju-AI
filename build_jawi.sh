#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements.txt
python tools/provision_pi_jawi_fonts.py
# Pendidikan Islam Jawi only: supply Amiri at the two existing Jawi font paths.
# Other PDF fonts, application code and database are unchanged.
python tools/provision_amiri_jawi.py
python - <<'PY'
from pathlib import Path
from shutil import copyfile
from fontTools.ttLib import TTFont
root = Path("fonts/jawi")
for weight in ("Regular", "Bold"):
    src = root / ("Amiri-" + weight + ".ttf")
    dest = root / ("NotoNaskhArabic-" + weight + ".ttf")
    if not src.is_file():
        raise RuntimeError("PI Jawi Amiri font missing: " + str(src))
    font = TTFont(str(src))
    try:
        families = [n.toUnicode() for n in font["name"].names if n.nameID == 1]
        if not any("Amiri" in name for name in families):
            raise RuntimeError("PI Jawi font is not Amiri: " + str(src))
    finally:
        font.close()
    copyfile(src, dest)
    print("PI Jawi Amiri enabled:", dest)
PY
python tools/install_pi_jawi_symbol_fallback.py
python tools/install_pi_jawi_amiri_priority.py
python -m py_compile app.py
