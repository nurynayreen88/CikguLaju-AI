#!/usr/bin/env python3
"""Patch CikguLaju primary English RPT/SOW menu semantics.

Safe, targeted source patch:
- textbook route remains page ordered;
- primary RPT/SOW fallback is ordered by numeric verified lesson_no;
- page/SP evidence with blank lesson_no is NOT exposed as an RPT/SOW lesson.

Run against app.py, then py_compile the result.
"""
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else 'app.py')
s=p.read_text(encoding='utf-8')
old_order="""                GROUP BY year_label,subject,book_title,unit_title,page_start,page_end,lesson_no,focus
                ORDER BY unit_title,page_start,lesson_no,focus\"\"\",(year_label,subject)).fetchall()"""
new_order="""                GROUP BY year_label,subject,book_title,unit_title,page_start,page_end,lesson_no,focus
                ORDER BY unit_title,
                         CASE WHEN TRIM(lesson_no) GLOB '[0-9]*' THEN CAST(lesson_no AS INTEGER) ELSE 999999 END,
                         page_start,page_end,focus\"\"\",(year_label,subject)).fetchall()"""
old_rows="""            for x in src:
                d=dict(x); d.setdefault('content_topic',''); d.setdefault('language_focus',''); d.setdefault('activity_ref','')
                d['notes']='Resolved from verified textbook_page_sp_map/SOW evidence; no lesson sequence fabricated.'
                rows.append(d)"""
new_rows="""            for x in src:
                d=dict(x); d.setdefault('content_topic',''); d.setdefault('language_focus',''); d.setdefault('activity_ref','')
                # Page/SP evidence is not automatically an RPT/SOW Lesson.
                if not str(d.get('lesson_no') or '').strip():
                    continue
                d['notes']='Resolved from verified textbook_page_sp_map/SOW evidence; no lesson sequence fabricated.'
                rows.append(d)"""
if old_order not in s: raise SystemExit('primary SOW order target not found')
if old_rows not in s: raise SystemExit('blank lesson guard target not found')
s=s.replace(old_order,new_order,1).replace(old_rows,new_rows,1)
p.write_text(s,encoding='utf-8')
print('patched',p)
