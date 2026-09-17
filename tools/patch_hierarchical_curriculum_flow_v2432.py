#!/usr/bin/env python3
"""CikguLaju v24.32 hierarchical curriculum navigation patch.

Rule: curriculum hierarchy is traversed one level at a time. Never combine
Theme/Unit/Topic/Subtopic in one choice. Source choice appears only after the
last available hierarchy level. Manual SK/SP remains under Pilihan Sendiri.
"""
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app.py')
s=p.read_text(encoding='utf-8')
marker='# ===== v24.32 HIERARCHICAL CURRICULUM FLOW ====='
if marker in s:
    print('already patched', p); raise SystemExit(0)

s += r'''

# ===== v24.32 HIERARCHICAL CURRICULUM FLOW =====
_callback_dispatch_v2432_base = callback

_HIERARCHY_KEYS_V2432 = (
    ('theme','tema'),
    ('unit','unit'),
    ('topic','topik','tajuk'),
    ('subtopic','subtopik','sub_topic'),
)

def _hierarchy_values_v2432(ss, level):
    """Read only hierarchy values already supplied by the curriculum layer.
    No curriculum labels are fabricated here.
    """
    pools = ss.get('_curriculum_hierarchy') or ss.get('curriculum_hierarchy') or {}
    if not isinstance(pools, dict): return []
    aliases=_HIERARCHY_KEYS_V2432[level]
    for k in aliases:
        vals=pools.get(k)
        if isinstance(vals,(list,tuple)):
            out=[]
            for v in vals:
                if isinstance(v,dict):
                    label=str(v.get('label') or v.get('name') or v.get('title') or '').strip()
                    value=str(v.get('value') or v.get('id') or label).strip()
                else:
                    label=value=str(v).strip()
                if label: out.append((label,value))
            return out
    return []

def _next_hierarchy_level_v2432(ss, after=-1):
    for i in range(after+1,len(_HIERARCHY_KEYS_V2432)):
        if _hierarchy_values_v2432(ss,i): return i
    return None

def _show_hierarchy_level_v2432(cid, level):
    ss=state.setdefault(cid,{})
    vals=_hierarchy_values_v2432(ss,level)
    if not vals:
        nxt=_next_hierarchy_level_v2432(ss,level)
        if nxt is not None: return _show_hierarchy_level_v2432(cid,nxt)
        return _quick_source_choice_v2391(cid)
    names=('Tema','Unit','Topik/Tajuk','Subtopik')
    kb=[]
    ss['_hierarchy_choices_v2432']={str(i):v for i,(_,v) in enumerate(vals)}
    for i,(label,_) in enumerate(vals):
        kb.append([{'text':label,'callback_data':f'hier32_{level}_{i}'}])
    send(cid,f'📚 <b>Pilih {names[level]}</b>',kb)

def _start_hierarchy_v2432(cid):
    ss=state.setdefault(cid,{})
    first=_next_hierarchy_level_v2432(ss,-1)
    if first is None: return _quick_source_choice_v2391(cid)
    return _show_hierarchy_level_v2432(cid,first)

def callback(cid,d):
    ss=state.setdefault(cid,{})
    ds=str(d or '')
    if ds.startswith('hier32_'):
        try:
            _,lev,idx=ds.split('_',2); lev=int(lev)
            value=ss.get('_hierarchy_choices_v2432',{}).get(idx)
            if value is None: return _show_hierarchy_level_v2432(cid,lev)
            canonical=('theme','unit','topic','subtopic')[lev]
            ss[canonical]=value
            # Child levels must be re-resolved by the curriculum layer; clear stale execution state.
            for k in ('rph_date','rph_day','rph_time','rph_start_time','rph_end_time','duration_minutes'):
                ss.pop(k,None)
            nxt=_next_hierarchy_level_v2432(ss,lev)
            if nxt is not None: return _show_hierarchy_level_v2432(cid,nxt)
            return _quick_source_choice_v2391(cid)
        except Exception:
            return _start_hierarchy_v2432(cid)
    return _callback_dispatch_v2432_base(cid,d)

APP_VERSION='v24.32-HIERARCHICAL-CURRICULUM-FLOW'
# ===== END v24.32 =====
'''
p.write_text(s,encoding='utf-8')
print('patched',p)
