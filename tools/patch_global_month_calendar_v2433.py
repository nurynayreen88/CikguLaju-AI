#!/usr/bin/env python3
"""CikguLaju v24.33: standardise date selection on the monthly calendar.

All known PdP date-entry callbacks are routed to the existing Gregorian monthly
calendar. A date is selected once; weekday is derived automatically and the
existing next-step/time flow continues. This patch does not alter curriculum
content or SK/SP mappings.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'app.py')
s=p.read_text(encoding='utf-8')
marker='# ===== v24.33 GLOBAL MONTH CALENDAR ====='
if marker in s:
    print('already patched',p); raise SystemExit(0)
if '_pdp_calendar_month_v2429' not in s:
    raise SystemExit('monthly calendar implementation not found')

s += r'''

# ===== v24.33 GLOBAL MONTH CALENDAR =====
_callback_dispatch_v2433_base = callback

# Legacy/date-entry callbacks that should now open the same monthly calendar.
_DATE_ENTRY_CALLBACKS_V2433 = {
    'pdpdate93_back', 'pdpdate93_change', 'pdpdate93_pick',
    'quick_date', 'rph_date', 'worksheet_date', 'bbm_date',
    'choose_date', 'select_date', 'pick_date',
}

def _open_standard_calendar_v2433(cid):
    ss=state.setdefault(cid,{})
    ss.pop('_pdp_dates_v2393',None)
    return _pdp_calendar_month_v2429(cid)

def callback(cid,d):
    ds=str(d or '')
    # Do not intercept the calendar's own month navigation/date cells.
    if ds.startswith('pdpcal29_'):
        return _callback_dispatch_v2433_base(cid,d)
    low=ds.lower()
    if ds in _DATE_ENTRY_CALLBACKS_V2433 or low.endswith(('_choose_date','_select_date','_pick_date')):
        return _open_standard_calendar_v2433(cid)
    return _callback_dispatch_v2433_base(cid,d)

APP_VERSION='v24.33-GLOBAL-MONTH-CALENDAR'
# ===== END v24.33 =====
'''
p.write_text(s,encoding='utf-8')
print('patched',p)
