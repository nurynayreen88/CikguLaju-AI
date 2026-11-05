"""Read-only, teacher-review CikguLaju PI 2027 catalog.

This is NOT a publication adapter. It does not register Telegram callbacks, import
app.py, touch credits, or modify the DB. The caller must opt into a teacher
DRAF preview and must not claim it is a final/approved RPH.
"""
from __future__ import annotations
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COUNT = {2:112,3:147,4:151,5:143,6:143}
HELD = {(2,35),(6,6),(6,14),(6,18),(6,60),(6,117)}
STATES = {"CALON_UJIAN_GURU_DRAF","SEMAKAN_KEUTAMAAN","TAHAN_SEMAKAN_KANDUNGAN"}
REQUIRED = ("sk", "sp", "objektif", "set_induksi", "aktiviti_utama", "pentaksiran", "penutup", "bahan")
VERSION = "pi-v7-partial-draft-20261105"

class UnavailableDraft(ValueError):
    """No user-facing draft is safe for this selection."""

def _int(value):
    if isinstance(value,bool):return None
    if type(value) is int:return value
    if type(value) is not str or not re.fullmatch(r'[0-9]{1,3}',value,flags=re.ASCII):return None
    return int(value)

@lru_cache(maxsize=5)
def _load(year,root):
    if year not in COUNT:return None
    root=Path(root)
    try:
        obj=json.loads((root / f'year{year}.json').read_text(encoding='utf-8'))
        if obj.get('version')!=VERSION or obj.get('ready') is not False or obj.get('year')!=year:return None
        rows=obj.get('records')
        if not isinstance(rows,list) or len(rows)!=COUNT[year]:return None
        out={}
        for i,r in enumerate(rows,1):
            if r.get('tahun')!=year or r.get('lesson')!=i or r.get('id')!=f'T{year}-L{i:03d}':return None
            state=r.get('state')
            if state not in STATES or r.get('verified_ready') is not False:return None
            held=(year,i) in HELD
            if r.get('withheld') is not held:return None
            if re.fullmatch(r'[0-9a-f]{64}',str(r.get('source_sha256',''))) is None:return None
            if held:
                if 'fields' in r or 'intro' in r:return None
            else:
                if state=='TAHAN_SEMAKAN_KANDUNGAN':return None
                fields=r.get('fields')
                if not isinstance(fields,dict) or any(not isinstance(fields.get(k),str) or not fields[k].strip() for k in REQUIRED):return None
                if 'DRAF' not in str(r.get('teacher_notice','')):return None
                # Audit fragments never become official teacher-facing instructions.
                if any('Padanan kod SP buku teks lama ada' in s or 'STATUS:' in s for s in fields.values()):return None
            out[i]=r
        return out
    except (OSError,UnicodeError,KeyError,ValueError,TypeError):
        return None


def get_lesson(year,lesson,*,root=ROOT):
    """Return an explicitly labelled DRAF; never return the six held lessons."""
    y,n=_int(year),_int(lesson)
    if y not in COUNT or n is None:return None
    records=_load(y,str(Path(root).resolve()))
    row=(records or {}).get(n)
    return dict(row) if row and not row['withheld'] else None


def counts(*,root=ROOT):
    available=0;held=0
    for year in COUNT:
        r=_load(year,str(Path(root).resolve()))
        if r is None:return None
        available+=sum(not x['withheld'] for x in r.values())
        held+=sum(x['withheld'] for x in r.values())
    return {'total':available+held,'draf':available,'held':held,'ready':0} if (available,held)==(690,6) else None


def preview_rows(state, existing, *,root=ROOT):
    """Optional rows overlay for controlled QA only; never wired automatically."""
    if not isinstance(state,dict) or not isinstance(existing,dict):return existing
    if str(state.get('subject') or '').casefold()!='pendidikan islam':return existing
    y=_int(str(state.get('year') or state.get('year_label') or '').replace('Tahun ','').replace('tahun ',''))
    n=_int(state.get('lesson_no'))
    r=get_lesson(y,n,root=root)
    if r is None:return existing
    fields=r['fields']
    selected_sp=str(state.get('sp_code') or '').strip()
    if selected_sp and selected_sp not in fields['sp']:return existing
    result=dict(existing)
    result.update({
        'MATA PELAJARAN':'Pendidikan Islam',
        'TAHUN/TINGKATAN':f'Tahun {y}',
        'TAJUK':f'CADANGAN CIKGULAJU (DRAF) — Lesson {n:03d}',
        'STANDARD KANDUNGAN':fields['sk'],
        'STANDARD PEMBELAJARAN':fields['sp'],
        'OBJEKTIF PEMBELAJARAN':fields['objektif'],
        'KRITERIA KEJAYAAN':fields['objektif'],
        'SET INDUKSI':fields['set_induksi'],
        'AKTIVITI UTAMA':fields['aktiviti_utama'],
        'PENTAKSIRAN':fields['pentaksiran'],
        'PENUTUP':fields['penutup'],
        'BAHAN BANTU MENGAJAR':fields['bahan'],
        'CATATAN SEMAKAN':r['teacher_notice'],
    })
    return result