#!/usr/bin/env python3
"""v24.38: replace the active legacy _pdp_pick_date_v2393 implementations themselves."""
from pathlib import Path
import re, sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'app.py')
s=p.read_text(encoding='utf-8')
marker='# ===== v24.38 LEGACY DATE PICKER REPLACED ====='
if marker in s:
    print('already patched'); raise SystemExit(0)
pat=re.compile(r'(?ms)^def _pdp_pick_date_v2393\(cid\):\n.*?(?=^def |^# =====)')
replacement='''def _pdp_pick_date_v2393(cid):\n    """Monthly Sunday-first calendar; replaces the historical linear 7/14-day picker."""\n    fn=globals().get('_calendar_v2437') or globals().get('_pdp_calendar_month_v2429')\n    if callable(fn):\n        return fn(cid)\n    raise RuntimeError('Monthly calendar handler is unavailable')\n\n'''
s2,n=pat.subn(replacement,s)
if n < 1:
    raise SystemExit('ERROR: active legacy date picker definition not found')
# Guard against leaving either known linear implementation active.
if re.search(r'(?s)def _pdp_pick_date_v2393\(cid\):.*?dates=\[today\+timedelta\(days=i\) for i in range\((?:7|14)\)\]',s2):
    raise SystemExit('ERROR: legacy linear date picker still active')
s2 += f'''\n\n{marker}\n# Replaced {n} historical _pdp_pick_date_v2393 definition(s).\nAPP_VERSION='v24.38-LEGACY-DATE-PICKER-REPLACED'\n# ===== END v24.38 =====\n'''
p.write_text(s2,encoding='utf-8')
print('replaced',n,'legacy date picker definition(s)')
