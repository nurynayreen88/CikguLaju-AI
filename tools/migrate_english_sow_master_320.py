#!/usr/bin/env python3
import os, sqlite3, importlib.util, argparse, json

def load_master(patch_path=None, json_path=None):
    if json_path:
        with open(json_path,"r",encoding="utf-8") as fh:
            master=json.load(fh)
    else:
        spec=importlib.util.spec_from_file_location("eng_patch", patch_path)
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        master=getattr(mod,"_ENG12_SOW_MASTER")
    for year in ("Tahun 1","Tahun 2"):
        rows=master.get(year,[]); nums=[int(r[0]) for r in rows]
        assert len(rows)==160 and len(set(nums))==160 and set(nums)==set(range(1,161)), (year,len(rows))
        assert all(len(r)>=7 and all(str(x).strip() for x in r[:7]) for r in rows)
    return master

def migrate(db_path, patch_path=None, json_path=None):
    master=load_master(patch_path, json_path)
    con=sqlite3.connect(db_path); con.row_factory=sqlite3.Row; c=con.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sow_master_320(
      year_label TEXT NOT NULL, lesson_no INTEGER NOT NULL, skill_lesson TEXT NOT NULL,
      unit_title TEXT NOT NULL, main_content_standard TEXT NOT NULL,
      main_learning_standard TEXT NOT NULL, complementary_content_standard TEXT NOT NULL,
      complementary_learning_standard TEXT NOT NULL, source_mode TEXT NOT NULL,
      PRIMARY KEY(year_label,lesson_no))""")
    c.execute("""CREATE TABLE IF NOT EXISTS sow_master_overlay(
      year_label TEXT NOT NULL, lesson_no INTEGER NOT NULL,
      textbook_linked INTEGER NOT NULL DEFAULT 0, workbook_linked INTEGER NOT NULL DEFAULT 0,
      teacher_book_guidance INTEGER NOT NULL DEFAULT 0, audio_status TEXT,
      PRIMARY KEY(year_label,lesson_no))""")
    c.execute("DELETE FROM sow_master_320"); c.execute("DELETE FROM sow_master_overlay")
    for year, rows in master.items():
        for r in rows:
            ln,skill,unit,mcs,mls,ccs,cls=r[:7]
            linked=c.execute("""SELECT textbook_page_start,workbook_page_start,audio_status
                                FROM bot_lesson_index WHERE year_label=? AND CAST(lesson_no AS INTEGER)=?""",
                             (year,int(ln))).fetchone()
            mode="TEXTBOOK_LINKED" if linked else "SOW_ONLY"
            c.execute("INSERT INTO sow_master_320 VALUES(?,?,?,?,?,?,?,?,?)",
                      (year,int(ln),skill,unit,mcs,mls,ccs,cls,mode))
            tb=c.execute("""SELECT 1 FROM teacher_book_lesson_guidance
                            WHERE year_label=? AND CAST(lesson_no AS INTEGER)=?""",(year,int(ln))).fetchone()
            c.execute("INSERT INTO sow_master_overlay VALUES(?,?,?,?,?,?)",
                      (year,int(ln),1 if linked else 0,
                       1 if linked and linked["workbook_page_start"] is not None else 0,
                       1 if tb else 0, linked["audio_status"] if linked else None))
    for year in ("Tahun 1","Tahun 2"):
        n=c.execute("SELECT COUNT(*) FROM sow_master_320 WHERE year_label=?",(year,)).fetchone()[0]
        miss=c.execute("""SELECT COUNT(*) FROM sow_master_320 WHERE year_label=? AND
          (main_content_standard='' OR main_learning_standard='' OR complementary_content_standard='' OR complementary_learning_standard='')""",(year,)).fetchone()[0]
        assert n==160 and miss==0,(year,n,miss)
    assert c.execute("SELECT COUNT(*) FROM sow_master_320").fetchone()[0]==320
    assert c.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    assert not c.execute("PRAGMA foreign_key_check").fetchall()
    con.commit()
    counts=c.execute("""SELECT year_label,source_mode,COUNT(*) n FROM sow_master_320
                        GROUP BY year_label,source_mode ORDER BY year_label,source_mode""").fetchall()
    con.close(); return [(r["year_label"],r["source_mode"],r["n"]) for r in counts]

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("db")
    ap.add_argument("--patch",default=os.path.join(os.path.dirname(__file__),"patch_english_y1y2_bot_ready_v1.py"))
    ap.add_argument("--json",default=os.path.join(os.path.dirname(os.path.dirname(__file__)),"data","english_y1y2_sow_master_320.json"))
    a=ap.parse_args(); print(migrate(a.db,a.patch,a.json if os.path.exists(a.json) else None))
