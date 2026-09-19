#!/usr/bin/env python3
"""Read-only QA for CikguLaju English Year1-2 BOT_READY DB."""
import sqlite3,sys
if len(sys.argv)!=2: raise SystemExit("Usage: audit_english_bot_ready.py <db>")
con=sqlite3.connect(f"file:{sys.argv[1]}?mode=ro",uri=True)
print("integrity:",con.execute("PRAGMA integrity_check").fetchone()[0])
print("fk_issues:",len(con.execute("PRAGMA foreign_key_check").fetchall()))
for y in ("Tahun 1","Tahun 2"):
    n=con.execute("SELECT COUNT(*) FROM bot_lesson_index WHERE year_label=?",(y,)).fetchone()[0]
    bad=con.execute("""SELECT COUNT(*) FROM bot_lesson_index
                       WHERE year_label=? AND ready_for_bot<>1""",(y,)).fetchone()[0]
    wb=con.execute("""SELECT workbook_status,COUNT(*) FROM bot_lesson_index
                      WHERE year_label=? GROUP BY workbook_status ORDER BY workbook_status""",(y,)).fetchall()
    au=con.execute("""SELECT audio_status,COUNT(*) FROM bot_lesson_index
                      WHERE year_label=? GROUP BY audio_status ORDER BY audio_status""",(y,)).fetchall()
    ms=con.execute("""SELECT COUNT(*) FROM (
       SELECT b.lesson_no,COUNT(s.id)c FROM bot_lesson_index b
       LEFT JOIN bot_lesson_standards s ON s.year_label=b.year_label AND s.lesson_no=b.lesson_no
       WHERE b.year_label=? GROUP BY b.lesson_no HAVING c<>2)""",(y,)).fetchone()[0]
    print(y,{"lessons":n,"not_ready":bad,"workbook":wb,"audio":au,"missing_standard_sets":ms})
con.close()
