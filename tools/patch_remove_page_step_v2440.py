#!/usr/bin/env python3
"""v24.40: make Lesson the only selectable curriculum item; pages are display metadata only."""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else 'app.py')
s=p.read_text(encoding='utf-8')
marker='# ===== v24.40 REMOVE PAGE SELECTION STEP ====='
if marker in s:
    print('already patched'); raise SystemExit(0)
s += r'''

# ===== v24.40 REMOVE PAGE SELECTION STEP =====
_callback_dispatch_v2440_base = callback

def _lesson_entry_v2440(cid):
    fn=globals().get('_show_lesson_only_v2436')
    if callable(fn): return fn(cid)
    return send(cid,'🚧 Senarai Lesson untuk pilihan ini belum tersedia.')

def callback(cid,d):
    ds=str(d or '')
    low=ds.lower()
    # Legacy textbook/page callbacks must never open a separate page menu.
    exact={
        'quick_page','choose_page','select_page','pick_page','textbook_page',
        'qsrc92_textbook','qsrc91_textbook','pdp_page','pdp_choose_page',
        'page_select','page_pick','page_choose'
    }
    prefixes=(
        'quickpage_','textbookpage_','textbook_page_','pdppage_','pdp_page_',
        'qpage_','pagepick_','page_pick_','pageselect_','page_select_'
    )
    suffixes=('_choose_page','_select_page','_pick_page','_textbook_page')
    if low in exact or low.startswith(prefixes) or low.endswith(suffixes):
        return _lesson_entry_v2440(cid)
    return _callback_dispatch_v2440_base(cid,d)

APP_VERSION='v24.40-NO-PAGE-SELECTION'
# ===== END v24.40 =====
'''
p.write_text(s,encoding='utf-8')
print('patched',p)
