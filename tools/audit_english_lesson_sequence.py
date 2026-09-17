#!/usr/bin/env python3
"""Read-only audit for English textbook/SOW mappings.

Rule: textbook navigation follows pages; RPT/SOW navigation follows official lesson numbers.
A lower textbook page in a later SOW lesson is not automatically an error.
"""
import re, sqlite3, sys
from collections import defaultdict
if len(sys.argv)!=2: raise SystemExit('Usage: audit_english_lesson_sequence.py <db>')
con=sqlite3.connect(f'file:{sys.argv[1]}?mode=ro',uri=True); con.row_factory=sqlite3.Row
T='textbook_page_lesson_map'
cols={r[1] for r in con.execute(f'PRAGMA table_info({T})')}
need={'year_label','subject','unit_title','page_start','page_end','lesson_no'}
if not need.issubset(cols): raise SystemExit(f'Missing columns: {sorted(need-cols)}')
def lk(v):
 s=str(v or '').strip(); n=[int(x) for x in re.findall(r'\d+',s)]
 return (n[0] if n else 10**9,n[1] if len(n)>1 else (n[0] if n else 10**9),s.casefold())
rows=[dict(r) for r in con.execute(f"SELECT * FROM {T} WHERE lower(subject) IN ('english','bahasa inggeris','english language','bi') AND verified=1")]
g=defaultdict(list)
for r in rows:g[(r['year_label'],r['unit_title'])].append(r)
print('=== TEXTBOOK VIEW (page order) ===')
for k,rr in sorted(g.items()):
 rr=sorted(rr,key=lambda r:(r['page_start'] if r['page_start'] is not None else 10**9,r['page_end'] if r['page_end'] is not None else 10**9,r.get('id',0)))
 print(k[0],'|',k[1],'|',[(r['page_start'],r['page_end'],r['lesson_no']) for r in rr])
print('\n=== RPT/SOW VIEW (lesson order) ===')
for k,rr in sorted(g.items()):
 rr=sorted(rr,key=lambda r:(lk(r['lesson_no']),r['page_start'] if r['page_start'] is not None else 10**9,r.get('id',0)))
 print(k[0],'|',k[1],'|',[(r['lesson_no'],r['page_start'],r['page_end']) for r in rr])
print('\n=== REVIEW FLAGS ===')
flags=0
for k,rr in sorted(g.items()):
 ident=defaultdict(list)
 for r in rr: ident[(str(r['lesson_no']).strip(),str(r.get('focus') or '').strip().casefold(),r['page_start'],r['page_end'])].append(r)
 exact=[(x,v) for x,v in ident.items() if len(v)>1]; blanks=[r for r in rr if not str(r['lesson_no'] or '').strip()]
 if exact or blanks:
  flags+=1; print(k[0],'|',k[1])
  if exact: print(' exact_duplicate_mapping:',[(x,len(v)) for x,v in exact])
  if blanks: print(' blank_lesson_no:',len(blanks))
print(f'\nVerified rows audited: {len(rows)}; groups needing review: {flags}')
print('NOTE: page reversals across SOW lessons are intentionally not flagged.')
con.close()
