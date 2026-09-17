#!/usr/bin/env python3
"""CikguLaju v24.34 manual class fallback.
Adds a manual class entry route when no linked class is available, while
preserving existing linked-class selection and the calendar -> time flow.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'app.py')
s=p.read_text(encoding='utf-8')
marker='# ===== v24.34 MANUAL CLASS FALLBACK ====='
if marker in s:
    print('already patched',p); raise SystemExit(0)

s += r'''

# ===== v24.34 MANUAL CLASS FALLBACK =====
_callback_dispatch_v2434_base = callback

def _manual_class_prompt_v2434(cid):
    ss=state.setdefault(cid,{})
    ss['_await_manual_class_v2434']=True
    send(cid,'✏️ <b>Masukkan nama kelas</b>\n\nTaip nama kelas untuk sesi ini.',[
        [{'text':'⬅️ Kembali','callback_data':'pdpclass93_back'}]
    ])

def _manual_class_button_v2434(rows):
    rows=list(rows or [])
    rows.append([{'text':'✏️ Masukkan Kelas Manual','callback_data':'pdpclass34_manual'}])
    return rows

def callback(cid,d):
    ds=str(d or '')
    if ds=='pdpclass34_manual':
        return _manual_class_prompt_v2434(cid)
    return _callback_dispatch_v2434_base(cid,d)

# Text handlers in historical app versions can call this helper before their
# normal processing. It consumes text only while manual-class entry is active.
def _consume_manual_class_text_v2434(cid,text):
    ss=state.setdefault(cid,{})
    if not ss.pop('_await_manual_class_v2434',False): return False
    name=str(text or '').strip()
    if not name:
        _manual_class_prompt_v2434(cid); return True
    ss['rph_class']=name
    ss['class_name']=name
    ss['_manual_class_v2434']=True
    # Date/time from a previous class must never leak into this session.
    for k in ('rph_date','rph_day','rph_time','rph_start_time','rph_end_time','duration_minutes','_pdp_calendar_v2429'):
        ss.pop(k,None)
    _pdp_calendar_month_v2429(cid)
    return True

APP_VERSION='v24.34-MANUAL-CLASS-FALLBACK'
# ===== END v24.34 =====
'''
p.write_text(s,encoding='utf-8')
print('patched',p)
