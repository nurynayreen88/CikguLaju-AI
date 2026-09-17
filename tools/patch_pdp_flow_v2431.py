#!/usr/bin/env python3
"""CikguLaju v24.31 PdP flow audit guard.

Applies the final state-transition fixes found by the full static flow audit:
- datetime.date must be imported for the monthly calendar callback;
- changing curriculum/source resets stale class/date/time execution state;
- changing class resets date/time state;
- old Tukar Tarikh callbacks open the current monthly calendar;
- date is selected once, then flow proceeds to time.
Run against app.py and py_compile afterwards.
"""
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app.py')
s=p.read_text(encoding='utf-8')
old='from datetime import datetime, timezone, timedelta\n'
new='from datetime import datetime, timezone, timedelta, date\n'
if old in s:
    s=s.replace(old,new,1)
elif new not in s:
    raise SystemExit('datetime import target not found')

marker="# ===== v24.31 PDP FLOW STATE AUDIT GUARD ====="
if marker not in s:
    s += r'''

# ===== v24.31 PDP FLOW STATE AUDIT GUARD =====
_callback_dispatch_v2431_base = callback

def _reset_pdp_execution_context_v2431(ss, keep_class=False):
    keys = ('_pdp_context_ready_v2393','rph_date','rph_day','rph_time','rph_start_time','rph_end_time','duration_minutes','_pdp_slots_v2393','_pdp_manual_start_v2393','_pdp_manual_starts_v2393','_pdp_dates_v2393','_pdp_calendar_v2429')
    for k in keys: ss.pop(k, None)
    if not keep_class:
        for k in ('rph_class','student_count','rph_students','_pdp_classes_v2393'): ss.pop(k, None)

def callback(cid, d):
    ss=state.setdefault(cid,{})
    ds=str(d or '')
    if ds.startswith(('sub_','qctx91_')) or ds in ('qsrc91_textbook','qsrc91_rpt','qsrc92_custom','quick_custom_topics'):
        _reset_pdp_execution_context_v2431(ss, keep_class=False)
    if ds.startswith('pdpclass93_') and ds!='pdpclass93_back':
        _reset_pdp_execution_context_v2431(ss, keep_class=True)
    if ds=='pdpdate93_back':
        return _pdp_calendar_month_v2429(cid)
    return _callback_dispatch_v2431_base(cid,d)

APP_VERSION='v24.31-PDP-FLOW-AUDIT-GUARD'
# ===== END v24.31 =====
'''
p.write_text(s,encoding='utf-8')
print('patched',p)
