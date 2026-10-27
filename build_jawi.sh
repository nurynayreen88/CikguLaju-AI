#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements.txt
python tools/provision_pi_jawi_fonts.py
python -m py_compile app.py
