#!/usr/bin/env python3
"""Audit English lesson labels without changing textbook page order.

Usage:
  python tools/audit_english_lesson_sequence.py CikguLaju_Curriculum_English.db
  python tools/audit_english_lesson_sequence.py CikguLaju_Curriculum_Master_v1.db

Read-only. Reports page-order lesson anomalies, duplicate lesson labels and gaps.
"""
import re, sqlite3, sys
from collections import Counter

if len(sys.argv) != 2:
    raise SystemExit("Usage: audit_english_lesson_sequence.py <db>")

path=sys.argv[1]
con=sqlite3.connect(f"file:{path}?mode=ro", uri=True)
con.row_factory=sqlite3.Row

def cols(table):
    return {r[1] for r in con.execute(f"PRAGMA table_info({table})")}

table='textbook_page_lesson_map'
c=cols(table)
if not c:
    raise SystemExit(f"Missing table: {table}")

def pick(*names):
    return next((x for x in names if x in c), None)

year=pick('year_label','year','level')
subject=pick('subject','subject_name')
page1=pick('page_start','page_from','start_page','page')
page2=pick('page_end','page_to','end_page')
lesson=pick('lesson_no','lesson_number','lesson')
unit=pick('unit_title','unit','topic','module')
idcol=pick('id')
if not all((year,page1,lesson)):
    raise SystemExit(f"Unsupported schema columns: {sorted(c)}")

fields=[x for x in (idcol,year,subject,unit,page1,page2,lesson) if x]
where=[]; args=[]
if subject:
    where.append(f"lower({subject}) in (?,?,?,?)")
    args += ['english','bahasa inggeris','english language','bi']
sql=f"SELECT {','.join(fields)} FROM {table}" + (" WHERE "+" AND ".join(where) if where else '')
rows=con.execute(sql,args).fetchall()

def nlesson(v):
    if v is None: return None
    m=re.search(r'\d+',str(v))
    return int(m.group()) if m else None

groups={}
for r in rows:
    key=(r[year], r[unit] if unit else '')
    groups.setdefault(key,[]).append(r)

issues=0
for key, rr in sorted(groups.items(), key=lambda x:str(x[0])):
    rr=sorted(rr,key=lambda r:(r[page1] if r[page1] is not None else 10**9,
                               r[page2] if page2 and r[page2] is not None else 10**9,
                               r[idcol] if idcol else 0))
    nums=[nlesson(r[lesson]) for r in rr]
    clean=[n for n in nums if n is not None]
    dup=sorted(n for n,cnt in Counter(clean).items() if cnt>1)
    desc=[]
    prev=None
    for i,n in enumerate(nums):
        if n is not None and prev is not None and n < prev:
            desc.append((i,prev,n))
        if n is not None: prev=n
    missing=[]
    if clean:
        present=set(clean)
        missing=[n for n in range(min(clean),max(clean)+1) if n not in present]
    nulls=sum(n is None for n in nums)
    if dup or desc or missing or nulls:
        issues+=1
        print(f"\n{key[0]} | {key[1] or '(no unit)'}")
        if dup: print('  duplicate:',dup)
        if desc: print('  out_of_order:',[(a,b) for _,a,b in desc])
        if missing: print('  gaps:',missing)
        if nulls: print('  missing_lesson_no:',nulls)
        print('  page_order:',[(r[page1], r[page2] if page2 else r[page1], r[lesson]) for r in rr])

print(f"\nRows audited: {len(rows)}; groups with anomalies: {issues}")
con.close()
