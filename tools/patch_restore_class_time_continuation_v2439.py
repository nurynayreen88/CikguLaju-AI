#!/usr/bin/env python3
"""v24.39: restore Lesson -> class -> calendar -> time -> existing pack continuation."""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'app.py')
s=p.read_text(encoding='utf-8')
marker='# ===== v24.39 CLASS + TIME CONTINUATION REPAIR ====='
if marker in s:
    print('already patched'); raise SystemExit(0)
s += r'''

# ===== v24.39 CLASS + TIME CONTINUATION REPAIR =====
_callback_dispatch_v2439_base = callback

# Preserve the working monthly calendar but restore the class gate before it.
def _lesson_to_class_v2439(cid):
    ss=state.setdefault(cid,{})
    # A new Lesson must not inherit execution context from a previous run.
    for k in ('rph_class','class_name','student_count','rph_students','rph_date','rph_day','rph_time','rph_start_time','rph_end_time','duration_minutes','_pdp_context_ready_v2393'):
        ss.pop(k,None)
    fn=globals().get('_pdp_pick_class_v2393') or globals().get('_pdp_choose_class_v2393')
    if callable(fn): return fn(cid)
    return send(cid,'⚠️ Pilihan kelas tidak tersedia.')

# Override the active Lesson application so class selection is mandatory.
_apply_lesson_v2436_base_v2439 = globals().get('_apply_lesson_v2436')
def _apply_lesson_v2436(cid, idx):
    ss=state.setdefault(cid,{})
    items=ss.get('_lesson_items_v2436') or ss.get('_lesson_items') or ss.get('lesson_items') or []
    try: item=items[int(idx)]
    except Exception:
        fn=globals().get('_show_lesson_only_v2436')
        return fn(cid) if callable(fn) else None
    if isinstance(item,dict):
        lesson=str(item.get('lesson_no') or item.get('lesson') or item.get('lesson_label') or '').strip()
        ss['lesson_no']=lesson; ss['lesson']=lesson
        for k in ('page_start','page_end','sk_code','sp_code','sk','sp'):
            if item.get(k) not in (None,''): ss[k]=item.get(k)
    else:
        ss['lesson_no']=str(item); ss['lesson']=str(item)
    return _lesson_to_class_v2439(cid)

# Add manual class entry to the actual active class menu without removing linked classes.
_pdp_pick_class_v2393_base_v2439 = globals().get('_pdp_pick_class_v2393')
def _pdp_pick_class_v2393(cid):
    ss=state.setdefault(cid,{})
    rows=[]
    finder=globals().get('_profile_class_records_for_context_v2394')
    if callable(finder):
        try: rows=finder(cid,ss.get('year',''),ss.get('subject','')) or []
        except Exception: rows=[]
    if not rows:
        finder=globals().get('_profile_class_records_for_year_v2393')
        if callable(finder):
            try: rows=finder(cid,ss.get('year','')) or []
            except Exception: rows=[]
    ss['_pdp_classes_v2393']=rows
    kb=[]
    for i,r in enumerate(rows):
        name=str(r.get('name') or '').strip()
        if name: kb.append([{'text':'🏫 '+name,'callback_data':f'pdpclass93_{i}'}])
    kb.append([{'text':'✏️ Masukkan Kelas Manual','callback_data':'pdpclass34_manual'}])
    msg='🏫 <b>Pilih Kelas</b>' if rows else '🏫 <b>Tiada kelas dipautkan</b>\n\nMasukkan kelas secara manual untuk sesi ini.'
    return send(cid,msg,kb)

# Once end time is valid, mark the PDP context complete and continue through
# the pre-v23.93 pack function. This is the continuation used by the historical
# timetable/manual-time flow and avoids the v24.35 return-None dead end.
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
    ss['_pdp_context_ready_v2393']=True
    send(cid,f"✅ Masa: <b>{ss['rph_time']}</b> ({end-start} minit)")
    fn=globals().get('_auto_pack_v2393_base')
    if callable(fn): return fn(cid)
    fn=globals().get('_auto_pack_v2393') or globals().get('_temporary_auto_pack_v2386')
    if callable(fn): return fn(cid)
    return send(cid,'✅ Maklumat kelas, tarikh dan masa telah lengkap.',[[{'text':'🏠 Menu Utama','callback_data':'home'}]])

def callback(cid,d):
    ds=str(d or '')
    # Ensure linked-class buttons always enter the monthly calendar.
    if ds.startswith('pdpclass93_') and ds!='pdpclass93_back':
        ss=state.setdefault(cid,{})
        try: r=(ss.get('_pdp_classes_v2393') or [])[int(ds.rsplit('_',1)[1])]
        except Exception: return _pdp_pick_class_v2393(cid)
        ss['rph_class']=r.get('name'); ss['class_name']=r.get('name')
        if r.get('students') not in (None,''):
            ss['student_count']=r.get('students'); ss['rph_students']=r.get('students')
        fn=globals().get('_calendar_v2437') or globals().get('_pdp_calendar_month_v2429')
        return fn(cid) if callable(fn) else None
    return _callback_dispatch_v2439_base(cid,d)

APP_VERSION='v24.39-CLASS-TIME-CONTINUATION'
# ===== END v24.39 =====
'''
p.write_text(s,encoding='utf-8')
print('patched',p)
