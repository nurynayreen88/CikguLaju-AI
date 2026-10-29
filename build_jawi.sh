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
python -m py_compile app.py
