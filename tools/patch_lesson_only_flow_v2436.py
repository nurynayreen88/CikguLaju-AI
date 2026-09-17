#!/usr/bin/env python3
"""v24.36: simplify curriculum flow to Lesson selection; page is metadata only."""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'app.py')
s=p.read_text(encoding='utf-8')
marker='# ===== v24.36 LESSON ONLY FLOW ====='
if marker in s:
    print('already patched'); raise SystemExit(0)
s += r'''

# ===== v24.36 LESSON ONLY FLOW =====
_callback_dispatch_v2436_base = callback

def _lesson_only_rows_v2436(items):
    """Build lesson buttons. page_start/page_end are display metadata, never a selection step."""
    rows=[]
    for i,item in enumerate(items or []):
        if isinstance(item,dict):
            lesson=str(item.get('lesson_no') or item.get('lesson') or item.get('lesson_label') or '').strip()
            ps=item.get('page_start'); pe=item.get('page_end')
        else:
            lesson=str(item).strip(); ps=pe=None
        if not lesson: continue
        label=f'📚 Lesson {lesson}' if not lesson.lower().startswith('lesson') else f'📚 {lesson}'
        if ps not in (None,''):
            page=str(ps) if pe in (None,'',ps) else f'{ps}–{pe}'
            label += f' · m/s {page}'
        rows.append([{'text':label[:60],'callback_data':f'lesson36_{i}'}])
    return rows

def _show_lesson_only_v2436(cid, items=None):
    ss=state.setdefault(cid,{})
    if items is not None: ss['_lesson_items_v2436']=list(items)
    items=ss.get('_lesson_items_v2436') or ss.get('_lesson_items') or ss.get('lesson_items') or []
    rows=_lesson_only_rows_v2436(items)
    if not rows:
        return send(cid,'🚧 Senarai Lesson untuk pilihan ini belum tersedia.')
    send(cid,'📚 <b>Pilih Lesson</b>\n\nMuka surat dipaparkan sebagai rujukan sahaja. Tidak perlu pilih muka surat.',rows)

def _apply_lesson_v2436(cid, idx):
    ss=state.setdefault(cid,{})
    items=ss.get('_lesson_items_v2436') or ss.get('_lesson_items') or ss.get('lesson_items') or []
    try: item=items[int(idx)]
    except Exception: return _show_lesson_only_v2436(cid)
    if isinstance(item,dict):
        lesson=str(item.get('lesson_no') or item.get('lesson') or item.get('lesson_label') or '').strip()
        ss['lesson_no']=lesson; ss['lesson']=lesson
        for k in ('page_start','page_end','sk_code','sp_code','sk','sp'):
            if item.get(k) not in (None,''): ss[k]=item.get(k)
    else:
        ss['lesson_no']=str(item); ss['lesson']=str(item)
    # Lesson already determines page/SK/SP. Continue to class selection.
    nxt=globals().get('_pdp_class_options_v2393') or globals().get('_quick_class_options_v2393') or globals().get('show_classes')
    if callable(nxt): return nxt(cid)
    return None

def callback(cid,d):
    ds=str(d or '')
    if ds.startswith('lesson36_'):
        return _apply_lesson_v2436(cid,ds.split('_',1)[1])
    # Any explicit textbook page-selection entry is redirected to Lesson selection.
    low=ds.lower()
    if low in ('quick_page','choose_page','select_page','pick_page','textbook_page','qsrc92_textbook') or low.endswith(('_choose_page','_select_page','_pick_page')):
        return _show_lesson_only_v2436(cid)
    return _callback_dispatch_v2436_base(cid,d)

APP_VERSION='v24.36-LESSON-ONLY-FLOW'
# ===== END v24.36 =====
'''
p.write_text(s,encoding='utf-8')
print('patched',p)
