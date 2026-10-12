from pathlib import Path
import sqlite3
b=Path(__file__).resolve().parent; target=b/'pjpk_candidate.db'
if target.exists():
 print('Existing DB preserved:',target)
else:
 parts=[b/'pjpk_candidate.db.part1',b/'pjpk_candidate.db.part2']
 if not all(x.is_file() for x in parts): raise RuntimeError('Both DB parts required')
 tmp=b/'pjpk_candidate.db.rebuilding'
 with tmp.open('wb') as out:
  for x in parts:
   with x.open('rb') as src:
    while True:
     block=src.read(1024*1024)
     if not block:break
     out.write(block)
 with sqlite3.connect(tmp) as c:
  if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('DB integrity check failed')
 tmp.replace(target);print('Candidate DB rebuilt:',target)
