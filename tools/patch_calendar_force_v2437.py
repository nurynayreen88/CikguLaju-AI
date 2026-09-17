#!/usr/bin/env python3
"""v24.37: force all PdP date entry to monthly 7-column calendar."""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'app.py')
s=p.read_text(encoding='utf-8')
marker='# ===== v24.37 FORCE MONTHLY CALENDAR ====='
if marker in s:
    print('already patched'); raise SystemExit(0)
s += r'''

# ===== v24.37 FORCE MONTHLY CALENDAR =====
_callback_dispatch_v2437_base = callback

def _calendar_v2437(cid, year=None, month=None):
    ss=state.setdefault(cid,{})
    tz=timezone(timedelta(hours=8)); today=datetime.now(tz).date()
    year=int(year or today.year); month=int(month or today.month)
    first=date(year,month,1)
    nxt=date(year+1,1,1) if month==12 else date(year,month+1,1)
    ndays=(nxt-first).days
    names=['Januari','Februari','Mac','April','Mei','Jun','Julai','Ogos','September','Oktober','November','Disember']
    # Python Monday=0; calendar required Sunday first.
    offset=(first.weekday()+1)%7
    cells=[None]*offset+list(range(1,ndays+1))
    while len(cells)%7: cells.append(None)
    rows=[[{'text':x,'callback_data':'cal37_noop'} for x in ['Ah','Is','Se','Ra','Kh','Ju','Sa']]]
    for i in range(0,len(cells),7):
        rows.append([{'text':(' ' if d is None else str(d)),'callback_data':('cal37_noop' if d is None else f'cal37_pick_{year}_{month}_{d}')} for d in cells[i:i+7]])
    py,pm=(year-1,12) if month==1 else (year,month-1)
    ny,nm=(year+1,1) if month==12 else (year,month+1)
    rows.append([
        {'text':'◀️','callback_data':f'cal37_month_{py}_{pm}'},
        {'text':f'{names[month-1]} {year}','callback_data':'cal37_noop'},
        {'text':'▶️','callback_data':f'cal37_month_{ny}_{nm}'},
    ])
    ss['_calendar_v2437']=(year,month)
    send(cid,f'📅 <b>Pilih Tarikh — {names[month-1]} {year}</b>',rows)

def _calendar_pick_v2437(cid,y,m,d):
    ss=state.setdefault(cid,{})
    dt=date(int(y),int(m),int(d))
    days=['Isnin','Selasa','Rabu','Khamis','Jumaat','Sabtu','Ahad']
    ss['rph_date']=dt.isoformat(); ss['rph_day']=days[dt.weekday()]
    ss.pop('_pdp_dates_v2393',None)
    # Exactly one date selection, then time range.
    fn=globals().get('_time_hour_menu_v2435')
    if callable(fn): return fn(cid,'start')
    fn=globals().get('_pdp_time_options_v2393')
    if callable(fn): return fn(cid)

def callback(cid,d):
    ds=str(d or ''); low=ds.lower()
    if ds=='cal37_noop': return None
    if ds.startswith('cal37_month_'):
        _,_,y,m=ds.split('_',3); return _calendar_v2437(cid,y,m)
    if ds.startswith('cal37_pick_'):
        _,_,y,m,n=ds.split('_',4); return _calendar_pick_v2437(cid,y,m,n)
    # Intercept known/legacy date entry callbacks before older linear picker.
    date_entries=('pdpdate93_back','pdpdate93_change','pdpdate93_pick','quick_date','rph_date','worksheet_date','bbm_date','choose_date','select_date','pick_date')
    if low in date_entries or low.endswith(('_choose_date','_select_date','_pick_date')):
        return _calendar_v2437(cid)
    return _callback_dispatch_v2437_base(cid,d)

APP_VERSION='v24.37-FORCE-MONTHLY-CALENDAR'
# ===== END v24.37 =====
'''
p.write_text(s,encoding='utf-8')
print('patched',p)
