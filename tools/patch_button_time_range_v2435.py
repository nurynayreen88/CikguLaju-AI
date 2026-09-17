#!/usr/bin/env python3
"""v24.35: button-based start/end hour+minute selector."""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'app.py')
s=p.read_text(encoding='utf-8')
marker='# ===== v24.35 BUTTON TIME RANGE SELECTOR ====='
if marker in s:
    print('already patched'); raise SystemExit(0)
s += r'''

# ===== v24.35 BUTTON TIME RANGE SELECTOR =====
_callback_dispatch_v2435_base = callback

def _time_hour_menu_v2435(cid, which='start'):
    ss=state.setdefault(cid,{})
    ss['_time_range_stage_v2435']=which
    rows=[]
    hours=list(range(6,24))
    for i in range(0,len(hours),3):
        rows.append([{'text':f'{h:02d}','callback_data':f'tr35_h_{which}_{h:02d}'} for h in hours[i:i+3]])
    send(cid,('🕐 <b>Pilih jam mula</b>' if which=='start' else '🕐 <b>Pilih jam akhir</b>'),rows)

def _time_minute_menu_v2435(cid, which, hour):
    ss=state.setdefault(cid,{})
    ss[f'_time_{which}_hour_v2435']=int(hour)
    mins=list(range(0,60,5)); rows=[]
    for i in range(0,len(mins),4):
        rows.append([{'text':f'{m:02d}','callback_data':f'tr35_m_{which}_{m:02d}'} for m in mins[i:i+4]])
    send(cid,('⏱️ <b>Pilih minit mula</b>' if which=='start' else '⏱️ <b>Pilih minit akhir</b>'),rows)

def _finish_time_range_v2435(cid):
    ss=state.setdefault(cid,{})
    sh=int(ss.get('_time_start_hour_v2435',0)); sm=int(ss.get('_time_start_min_v2435',0))
    eh=int(ss.get('_time_end_hour_v2435',0)); em=int(ss.get('_time_end_min_v2435',0))
    start=sh*60+sm; end=eh*60+em
    if end<=start:
        send(cid,'⚠️ Masa akhir mesti selepas masa mula. Sila pilih masa akhir semula.')
        return _time_hour_menu_v2435(cid,'end')
    ss['rph_start_time']=f'{sh:02d}:{sm:02d}'
    ss['rph_end_time']=f'{eh:02d}:{em:02d}'
    ss['rph_time']=f'{sh:02d}:{sm:02d} - {eh:02d}:{em:02d}'
    ss['duration_minutes']=end-start
    # Continue through the historical dispatcher/flow after emitting a compact confirmation.
    send(cid,f"✅ Masa: <b>{ss['rph_time']}</b> ({end-start} minit)")
    nxt=globals().get('_pdp_after_time_v2393') or globals().get('_pdp_next_after_time_v2393')
    if callable(nxt): return nxt(cid)
    return None

def callback(cid,d):
    ds=str(d or '')
    if ds in ('pdpmanualtime35','pdp_time_manual','time_manual','manual_time'):
        return _time_hour_menu_v2435(cid,'start')
    if ds.startswith('tr35_h_'):
        _,_,which,h=ds.split('_',3); return _time_minute_menu_v2435(cid,which,h)
    if ds.startswith('tr35_m_'):
        _,_,which,m=ds.split('_',3); ss=state.setdefault(cid,{})
        ss[f'_time_{which}_min_v2435']=int(m)
        if which=='start': return _time_hour_menu_v2435(cid,'end')
        return _finish_time_range_v2435(cid)
    return _callback_dispatch_v2435_base(cid,d)

APP_VERSION='v24.35-BUTTON-TIME-RANGE'
# ===== END v24.35 =====
'''
p.write_text(s,encoding='utf-8')
print('patched',p)
