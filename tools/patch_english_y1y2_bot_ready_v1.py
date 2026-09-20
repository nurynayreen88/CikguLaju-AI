#!/usr/bin/env python3
"""Patch English Year 1-2 BOT_READY lesson-first flow into app.py safely.

Non-destructive and idempotent:
- preserves existing app.py;
- activates only for Bahasa Inggeris / English Year 1-2;
- uses verified BOT_READY DB tables;
- user selects Lesson once; SK/SP auto;
- unresolved audio never guessed.
"""
from pathlib import Path
import sys

p=Path(sys.argv[1] if len(sys.argv)>1 else "app.py")
s=p.read_text(encoding="utf-8")
MARK="# ===== ENGLISH Y1Y2 BOT READY V1 ====="
if MARK in s:
    print("English Y1Y2 BOT_READY block already present; continuing priority-route check")

block=r'''
# ===== ENGLISH Y1Y2 BOT READY V1 =====
def _eng12_year_label(ss):
    raw=str(ss.get("year") or ss.get("grade") or ss.get("level") or "").strip().lower()
    if raw in ("tahun 1","1","year 1","year1","y1"): return "Tahun 1"
    if raw in ("tahun 2","2","year 2","year2","y2"): return "Tahun 2"
    return ""

def _eng12_is_english_subject_callback(ds):
    x=str(ds or "").strip().lower().replace("%20"," ")
    return ("bahasa inggeris" in x or "english" in x) and (x.startswith("sub_") or x.startswith("subject_") or x.startswith("subjek_") or x in ("bahasa inggeris","english"))

def _eng12_db_path():
    import os
    candidates=[
        os.environ.get("CIKGULAJU_ENGLISH_Y1Y2_DB_PATH","").strip(),
        os.path.join(os.path.dirname(__file__),"CikguLaju_English_Primary_Year1_Year2_BOT_READY_v1.db"),
    ]
    for x in candidates:
        if x and os.path.exists(x):
            return x
    return ""

_ENG12_SOW_MASTER={"Tahun 1":[[1,"Speaking 1","Friends","2.1","2.1.4","2.3","2.3.1"],[2,"Listening 1","Friends","1.2","1.2.4","4.1","4.1.2"],[3,"Reading 1","Friends","3.1","3.1.1","3.1","3.1.2"],[4,"Writing 1","Friends","4.1","4.1.2","3.1","3.1.1"],[5,"Language Arts 1","Friends","5.1","5.1.1","5.1","5.1.2"],[6,"Listening 2","Friends","1.2","1.2.2","2.1","2.1.1"],[7,"Writing 2","Friends","4.1","4.1.2","2.1","2.1.1"],[8,"Reading 2","Friends","3.1","3.1.1","4.1","4.1.2"],[9,"Speaking 2","Friends","2.1","2.1.5","3.1","3.1.3"],[10,"Language Arts 2","Friends","5.1","5.1.1","5.1","5.1.2"],[11,"Listening 3","Friends","1.2","1.2.5","4.2","4.2.1"],[12,"Speaking 3","Friends","2.3","2.3.1","4.3","4.3.1"],[13,"Reading 3","Friends","3.1","3.1.1","4.1","4.1.2"],[14,"Writing 3","Friends","4.1","4.1.2","3.3","3.3.1"],[15,"Language Arts 3","Friends","5.1","5.1.1","2.1","2.1.5"],[16,"Reading 4","Friends","3.2","3.2.2","1.2","1.2.3"],[17,"Writing 4","Friends","4.2","4.2.1","2.1","2.1.5"],[18,"Listening 4","At School","1.2","1.2.1","2.1","2.1.5"],[19,"Speaking 4","At School","2.1","2.1.5","1.2","1.2.2"],[20,"Language Arts 4","At School","5.2","5.2.1","5.3","5.3.1"],[21,"Listening 5","At School","1.3","1.3.1","1.2","1.2.4"],[22,"Speaking 5","At School","2.1","2.1.4","1.2","1.2.2"],[23,"Reading 5","At School","3.1","3.1.3","4.3","4.3.2"],[24,"Writing 5","At School","4.2","4.2.2","4.2","4.2.4"],[25,"Language Arts 5","At School","5.2","5.2.1","2.1","2.1.5"],[26,"Speaking 6","At School","2.1","2.1.1","1.2","1.2.5"],[27,"Writing 6","At School","4.2","4.2.4","1.2","1.2.4"],[28,"Listening 6","At School","1.2","1.2.3","3.2","3.2.1"],[29,"Reading 6","At School","3.1","3.1.2","1.1","1.1.1"],[30,"Language Arts 6","At school","5.1","5.1.2","5.3","5.3.1"],[31,"Listening 7","At School","1.2","1.2.1","1.2","1.2.2"],[32,"Speaking 7","At School","2.1","2.1.4","2.2","2.2.2"],[33,"Reading 7","At School","3.1","3.1.3","3.1","3.1.4"],[34,"Writing 7","At School","4.2","4.2.2","4.3","4.3.1"],[35,"Language Arts 7","At school","5.1","5.1.1","5.1","5.1.2"],[36,"Listening 8","At School","1.2","1.2.2","2.1","2.1.1"],[37,"Speaking 8","At School","2.1","2.1.2","4.2","4.2.5"],[38,"Writing 8","At School","4.3","4.3.2","3.2","3.2.1"],[39,"Reading 8","At School","3.2","3.2.2","2.1","2.1.5"],[40,"Language Arts 8","At school","5.3","5.3.1","1.2","1.2.4"],[41,"Listening 9","At School","1.2","1.2.2","1.2","1.2.5"],[42,"Speaking 9","At School","2.1","2.1.4","1.2","1.2.4"],[43,"Reading 9","At School","3.1","3.1.2","4.3","4.3.2"],[44,"Writing 9","At School","4.3","4.3.2","3.2","3.2.2"],[45,"Language Arts 9","At school","5.1","5.1.1","5.3","5.3.1"],[46,"Listening (10)","At School","1.2","1.2.4","2.2","2.2.2"],[47,"Writing 10","At School","4.2","4.2.4","3.2","3.2.4"],[48,"Speaking 10","Let’s Play!","2.1","2.1.5","1.2","1.2.1"],[49,"Reading 10","Let’s Play!","3.2","3.2.2","2.1","2.1.2"],[50,"Language Arts 10","Let’s Play!","5.2","5.2.1","1.2","1.2.3"],[51,"Listening 11","Let’s Play!","1.2","1.2.4","2.1","2.1.5"],[52,"Speaking 11","Let’s Play!","2.1","2.1.3","2.3","2.3.1"],[53,"Reading 11","Let’s Play!","3.1","3.1.3","3.1","3.1.4"],[54,"Writing 11","Let’s Play!","4.2","4.2.3","2.2","2.2.2"],[55,"Language Arts 11","Let’s Play!","5.2","5.2.1","1.2","1.2.2"],[56,"Speaking 12","Let’s Play!","2.1","2.1.1","4.2","4.2.1"],[57,"Listening 12","Let’s Play!","1.2","1.2.2","1.2","1.2.5"],[58,"Writing 12","Let’s Play!","4.3","4.3.2","3.3","3.3.1"],[59,"Reading 12","Let’s Play!","3.2","3.2.1","1.2","1.2.3"],[60,"Language Arts 12","Let’s Play!","5.2","5.2.1","4.3","4.3.3"],[61,"Listening 13","Let’s Play!","1.3","1.3.1","1.2","1.2.2"],[62,"Speaking 13","Let’s Play!","2.1","2.1.5","2.2","2.2.2"],[63,"Reading 13","Let’s Play!","3.2","3.2.3","4.2","4.2.4"],[64,"Writing 13","Let’s Play!","4.3","4.3.1","3.2","3.2.2"],[65,"Language Arts 13","Let’s Play","5.2","5.2.1","1.2","1.2.3"],[66,"Reading 14","Let’s Play!","3.1","3.1.2","1.1","1.1.1"],[67,"Listening 14","Let’s Play!","1.2","1.2.2","3.2","3.2.2"],[68,"Writing 14","Let’s Play!","4.2","4.2.3","2.1","2.1.3"],[69,"Speaking 14","Let’s Play!","2.1","2.1.5","3.2","3.2.2"],[70,"Language Arts 14","Let’s Play","5.2","5.2.1","5.3","5.3.1"],[71,"Listening 15","Let’s Play!","1.2","1.2.2","2.1","2.1.5"],[72,"Speaking 15","Let’s Play!","2.1","2.1.3","2.2","2.2.2"],[73,"Reading 15","Let’s Play!","3.1","3.1.1","3.1","3.1.2"],[74,"Writing 15","Let’s Play!","4.3","4.3.2","4.3","4.3.3"],[75,"Language Arts 15","Let’s Play","5.1","5.1.1","5.2","5.2.1"],[76,"Speaking 16","Let’s Play!","2.1","2.1.1","2.2","2.2.2"],[77,"Reading 16","Let’s Play!","3.2","3.2.3","1.2","1.2.5"],[78,"Writing 16","Let’s Play!","4.3","4.3.2","4.2","4.2.1"],[79,"Listening 16","Pet Show","1.2","1.2.1","2.1","2.1.5"],[80,"Language Arts 16","Pet Show","5.3","5.3.1","4.2","4.2.4"],[81,"Listening 17","Pet Show","1.2","1.2.2","2.1","2.1.5"],[82,"Speaking 17","Pet Show","2.1","2.1.2","2.1","2.1.3"],[83,"Reading 17","Pet Show","3.1","3.1.3","3.3","3.3.1"],[84,"Writing 17","Pet Show","4.2","4.2.3","4.3","4.3.1"],[85,"Language Arts 17","Pet Show","5.3","5.3.1","2.1","2.1.5"],[86,"Listening 18","Pet Show","1.2","1.2.2","2.1","2.1.5"],[87,"Speaking 18","Pet Show","2.1","2.1.5","1.1","1.1.1"],[88,"Reading 18","Pet Show","3.2","3.2.2","2.1","2.1.3"],[89,"Writing 18","Pet Show","4.2","4.2.5","4.3","4.3.3"],[90,"Language Arts 18","Pet Show","5.1","5.1.1","5.1","5.1.2"],[91,"Listening 19","Pet Show","1.2","1.2.5","1.2","1.2.2"],[92,"Speaking 19","Pet Show","2.1","2.1.5","1.2","1.2.4"],[93,"Reading 19","Pet Show","3.1","3.1.3","4.3","4.3.2"],[94,"Writing 19","Pet Show","4.3","4.3.3","4.3","4.3.2"],[95,"Language Arts 19","Pet Show","5.3","5.3.1","1.2","1.2.4"],[96,"Speaking 20","Pet Show","2.1","2.1.3","1.2","1.2.2"],[97,"Listening 20","Pet Show","1.3","1.3.1","1.2","1.2.3"],[98,"Reading 20","Pet Show","3.1","3.1.3","3.1","3.1.4"],[99,"Writing 20","Pet Show","4.2","4.2.3","4.2","4.2.5"],[100,"Language Arts 20","Pet Show","5.1","5.1.1","5.1","5.1.2"],[101,"Listening 21","Pet Show","1.2","1.2.3","2.1","2.1.5"],[102,"Speaking 21","Pet Show","2.1","2.1.2","1.2","1.2.5"],[103,"Reading 21","Pet Show","3.2","3.2.2","1.2","1.2.2"],[104,"Writing 21","Pet Show","4.2","4.2.3","4.2","4.2.1"],[105,"Language Arts 21","Pet Show","5.3","5.3.1","1.1","1.1.1"],[106,"Writing 22","Pet Show","4.3","4.3.2","1.2","1.2.4"],[107,"Speaking 22","Pet Show","2.1","2.1.5","1.2","1.2.5"],[108,"Reading 22","Pet Show","3.2","3.2.3","3.1","3.1.3"],[109,"Listening 22","Pet Show","1.2","1.2.3","1.2","1.2.2"],[110,"Language Arts 22","Pet Show","5.3","5.3.1","1.2","1.2.2"],[111,"Listening 23","Pet Show","1.2","1.2.2","2.1","2.1.5"],[112,"Speaking 23","Pet Show","2.1","2.1.5","2.2","2.2.2"],[113,"Reading 23","Pet Show","3.2","3.2.3","4.2","4.2.5"],[114,"Writing 23","Pet Show","4.3","4.3.3","4.3","4.3.2"],[115,"Language Arts 23","Pet Show","5.1","5.1.2","5.3","5.3.1"],[116,"Writing 24","Pet Show","4.3","4.3.2","3.2","3.2.4"],[117,"Speaking 24","Lunchtime","2.1","2.1.5","1.2","1.2.1"],[118,"Reading 24","Lunchtime","3.2","3.2.3","2.1","2.1.1"],[119,"Listening 24","Lunchtime","1.2","1.2.2","1.2","1.2.2"],[120,"Language Arts 24","Lunchtime","5.1","5.1.1","1.2","1.2.1"],[121,"Listening 25","Lunchtime","1.2","1.2.4","2.1","2.1.5"],[122,"Speaking 25","Lunchtime","2.1","2.1.5","3.2","3.2.2"],[123,"Reading 25","Lunchtime","3.2","3.2.1","3.2","3.2.2"],[124,"Writing 25","Lunchtime","4.3","4.3.2","4.3","4.3.3"],[125,"Language Arts 25","Lunchtime","5.2","5.2.1","4.3","4.3.2"],[126,"Speaking 26","Lunchtime","2.1","2.1.2","1.2","1.2.2"],[127,"Listening 26","Lunchtime","1.2","1.2.2","3.2","3.2.1"],[128,"Writing 26","Lunchtime","4.3","4.3.3","4.3","4.3.2"],[129,"Reading 26","Lunchtime","3.2","3.2.2","1.1","1.1.1"],[130,"Language Arts 26","Lunchtime","5.2","5.2.1","1.2","1.2.3"],[131,"Listening 27","Lunchtime","1.3","1.3.1","1.2","1.2.2"],[132,"Speaking 27","Lunchtime","2.1","2.1.4","1.2","1.2.5"],[133,"Reading 27","Lunchtime","3.1","3.1.3","4.3","4.3.2"],[134,"Writing 27","Lunchtime","4.3","4.3.2","3.1","3.1.3"],[135,"Language Arts 27","Lunchtime","5.2","5.2.1","2.1","2.1.4"],[136,"Listening 28","Lunchtime","1.2","1.2.2","4.3","4.3.2"],[137,"Reading 28","Lunchtime","3.2","3.2.3","2.1","2.1.1"],[138,"Speaking 28","Lunchtime","2.1","2.1.3","3.3","3.3.1"],[139,"Writing 28","Lunchtime","4.3","4.3.2","3.3","3.3.1"],[140,"Language Arts 28","Lunchtime","5.2","5.2.1","1.3","1.3.1"],[141,"Listening 29","Lunchtime","1.2","1.2.1","1.2","1.2.2"],[142,"Speaking 29","Lunchtime","2.1","2.1.2","1.2","1.2.5"],[143,"Reading 29","Lunchtime","3.2","3.2.2","2.1","2.1.4"],[144,"Writing 29","Lunchtime","4.3","4.3.3","4.2","4.2.5"],[145,"Language Arts 29","Lunchtime","5.2","5.2.1","3.1","3.1.3"],[146,"Speaking 30","Lunchtime","2.1","2.1.1","3.2","3.2.3"],[147,"Writing 30","Lunchtime","4.2","4.2.1","3.2","3.2.2"],[148,"Reading 30","Lunchtime","3.2","3.2.4","2.1","2.1.1"],[149,"Listening 30","Lunchtime review","1.3","1.3.1","1.2","1.2.2"],[150,"Language Arts 30","Lunchtime review","5.2","5.2.1","1.2","1.2.3"],[151,"Listening 31","Year 1 Revision","1.2","1.2.5","2.1","2.1.5"],[152,"Speaking 31","Year 1 Revision","2.1","2.1.5","1.2","1.2.5"],[153,"Reading 31","Year 1 Revision","3.2","3.2.2","2.1","2.1.5"],[154,"Writing 31","Year 1 Revision","4.2","4.2.5","3.2","3.2.2"],[155,"Language Arts 31","Year 1 Revision","5.3","5.3.1","2.3","2.3.1"],[156,"Listening 32","Year 1 Revision","1.2","1.2.5","2.1","2.1.2"],[157,"Speaking 32","Year 1 Revision","2.1","2.1.1","1.2","1.2.2"],[158,"Writing 32","Year 1 Revision","4.3","4.3.2","3.2","3.2.3"],[159,"Reading 32","Year 1 Revision","3.3","3.3.1","3.2","3.2.3"],[160,"Language Arts 32","Year 1 Revision","5.3","5.3.1","2.3","2.3.1"]],"Tahun 2":[[1,"Writing 1","Introduction","4.2","4.2.1","2.3","2.3.1"],[2,"Listening 1","Free Time","1.2","1.2.1","2.1","2.1.1"],[3,"Speaking 1","Free Time","2.1","2.1.1","1.2","1.2.1"],[4,"Reading 1","Free Time","3.2","3.2.2","1.2","1.2.1"],[5,"Language Arts 1","Free Time","5.2","5.2.1","1.2","1.2.1"],[6,"Listening 2","Free Time","1.2","1.2.2","2.1","2.1.1"],[7,"Speaking 2","Free Time","2.1","2.1.1","1.2","1.2.2"],[8,"Reading 2","Free Time","3.1","3.1.2","3.1","3.1.1"],[9,"Writing 2","Free Time","4.3","4.3.3","4.2","4.2.1"],[10,"Language Arts 2","Free Time","5.2","5.2.1","2.1","2.1.3"],[11,"Speaking 3","Free Time","2.1","2.1.1","2.1","2.1.2"],[12,"Listening 3","Free Time","1.2","1.2.3","1.2","1.2.2"],[13,"Reading 3","Free Time","3.1","3.1.3","1.1","1.1.1"],[14,"Writing 3","Free Time","4.3","4.3.1","1.2","1.2.2"],[15,"Language Arts 3","Free Time","5.1","5.1.2","3.1","3.1.3"],[16,"Listening 4","Free Time","1.2","1.2.2","3.1","3.1.1"],[17,"Speaking 4","Free Time","2.1","2.1.2","4.2","4.2.1"],[18,"Reading 4","Free Time","3.2","3.2.2","3.2","3.2.3"],[19,"Writing 4","Free Time","4.3","4.3.3","4.2","4.2.5"],[20,"Language Arts 4","Free Time","5.1","5.1.2","4.2","4.2.1"],[21,"Reading 5","Free Time","3.2","3.2.2","2.1","2.1.2"],[22,"Speaking 5","Free Time","2.1","2.1.2","2.1","2.1.1"],[23,"Listening 5","Free Time","1.2","1.2.3","1.2","1.2.4"],[24,"Writing 5","Free Time","4.3","4.3.1","3.2","3.2.4"],[25,"Language Arts 5","Free Time","5.1","5.1.1","1.2","1.2.1"],[26,"Listening 6","The old house","1.2","1.2.2","4.3","4.3.2"],[27,"Speaking 6","Free Time","2.1","2.1.3","1.2","1.2.5"],[28,"Reading 6","Free Time","3.2","3.2.2","4.2","4.2.3"],[29,"Writing 6","Free Time","4.3","4.3.2","4.3","4.3.1"],[30,"Language Arts 6","Free Time","5.3","5.3.1","2.2","2.2.2"],[31,"Speaking 7","The old house","2.1","2.1.5","1.2","1.2.2"],[32,"Listening 7","The old house","1.2","1.2.2","2.2","2.2.1"],[33,"Reading 7","The old house","3.2","3.2.3","1.2","1.2.1"],[34,"Writing 7","The old house","4.3","4.3.2","2.1","2.1.2"],[35,"Language Arts 7","The old house","5.1","5.1.2","1.3","1.3.1"],[36,"Listening 8","The old house","1.2","1.2.3","1.2","1.2.2"],[37,"Speaking 8","The old house","2.1","2.1.2","2.1","2.1.5"],[38,"Reading 8","The old house","3.1","3.1.4","1.1","1.1.1"],[39,"Writing 8","The old house","4.3","4.3.3","4.3","4.3.1"],[40,"Language Arts 8","The old house","5.3","5.3.1","1.2","1.2.1"],[41,"Listening 9","The old house","1.1","1.1.1","3.1","3.1.3"],[42,"Reading 9","The old house","3.2","3.2.1","3.1","3.1.2"],[43,"Writing 9","The old house","4.2","4.2.1","4.2","4.2.5"],[44,"Speaking 9","The old house","2.1","2.1.5","2.2","2.2.2"],[45,"Language Arts 9","The old house","5.2","5.2.1","2.1","2.1.5"],[46,"Listening 10","The old house","1.2","1.2.2","2.1","2.1.5"],[47,"Reading 10","The old house","3.2","3.2.2","4.2","4.2.4"],[48,"Writing 10","The old house","4.2","4.2.5","4.3","4.3.1"],[49,"Speaking 10","The old house","2.1","2.1.5","2.2","2.2.2"],[50,"Language Arts 10","The old house","5.1","5.1.1","1.2","1.2.3"],[51,"Listening 11","The old house","1.2","1.2.2","2.1","2.1.1"],[52,"Reading 11","The old house","3.2","3.2.2","3.2","3.2.4"],[53,"Speaking 11","The old house","2.2","2.2.2","1.2","1.2.5"],[54,"Writing 11","The old house","4.2","4.2.3","4.2","4.2.4"],[55,"Language Arts 11","The old house","5.3","5.3.1","2.1","2.1.3"],[56,"Listening 12","Get dressed!","1.2","1.2.2","3.3","3.3.1"],[57,"Speaking 12","Get dressed!","2.1","2.1.2","1.2","1.2.5"],[58,"Reading 12","Get dressed!","3.1","3.1.3","3.1","3.1.4"],[59,"Writing 12","Get dressed!","4.3","4.3.2","3.1","3.1.1"],[60,"Language Arts 12","Get dressed!","5.2","5.2.1","4.3","4.3.2"],[61,"Listening 13","Get dressed!","1.2","1.2.5","1.3","1.3.1"],[62,"Speaking 13","Get dressed!","2.1","2.1.2","2.2","2.2.1"],[63,"Reading 13","Get dressed!","3.2","3.2.2","3.2","3.2.3"],[64,"Writing 13","Get dressed!","4.2","4.2.3","4.3","4.3.1"],[65,"Language Arts 13","Get dressed!","5.1","5.1.2","3.2","3.2.3"],[66,"Listening 14","Get dressed!","1.3","1.3.1","2.1","2.1.5"],[67,"Speaking 14","Get dressed!","2.1","2.1.2","4.3","4.3.1"],[68,"Reading 14","Get dressed!","3.2","3.2.1","3.2","3.2.2"],[69,"Writing 14","Get dressed!","4.3","4.3.1","4.2","4.2.5"],[70,"Language Arts 14","Get dressed!","5.2","5.2.1","1.3","1.3.1"],[71,"Listening 15","Get dressed!","1.1","1.1.1","3.1","3.1.4"],[72,"Speaking 15","Get dressed!","2.1","2.1.3","2.2","2.2.1"],[73,"Reading 15","Get dressed!","3.1","3.1.2","3.1","3.1.3"],[74,"Writing 15","Get dressed!","4.3","4.3.2","4.3","4.3.3"],[75,"Language Arts 15","Get dressed!","5.3","5.3.1","2.1","2.1.5"],[76,"Reading 16","Get dressed!","3.2","3.2.2","3.2","3.2.3"],[77,"Speaking 16","Get dressed!","2.1","2.1.2","4.2","4.2.4"],[78,"Listening 16","Get dressed!","1.3","1.3.1","2.1","2.1.5"],[79,"Writing 16","Get dressed!","4.3","4.3.2","2.1","2.1.5"],[80,"Language Arts 16","Get dressed!","5.3","5.3.1","2.1","2.1.5"],[81,"Listening 17","Get dressed!","1.3","1.3.1","2.1","2.1.5"],[82,"Speaking 17","Get dressed!","2.1","2.1.5","2.3","2.3.1"],[83,"Reading 17","Get dressed!","3.2","3.2.2","3.3","3.3.1"],[84,"Writing 17","Get dressed!","4.3","4.3.2","3.3","3.3.1"],[85,"Language Arts 17","Get dressed!","5.1","5.1.2","2.1","2.1.5"],[86,"Listening 18","Get dressed!","1.2","1.2.3","1.2","1.2.4"],[87,"Reading 18","Get dressed!","3.2","3.2.4","2.1","2.1.5"],[88,"Speaking 18","The robot","2.1","2.1.3","1.2","1.2.2"],[89,"Writing 18","The robot","4.2","4.2.2","3.2","3.2.1"],[90,"Language Arts 18","The robot","5.3","5.3.1","2.1","2.1.3"],[91,"Listening 19","The robot","1.2","1.2.2","2.1","2.1.5"],[92,"Speaking 19","The robot","2.1","2.1.4","1.2","1.2.2"],[93,"Reading 19","The robot","3.1","3.1.3","3.1","3.1.4"],[94,"Writing 19","The robot","4.2","4.2.3","3.3","3.3.1"],[95,"Language Arts 19","The robot","5.3","5.3.1","2.1","2.1.5"],[96,"Listening 20","The robot","1.2","1.2.2","2.1","2.1.4"],[97,"Speaking 20","The robot","2.1","2.1.2","2.1","2.1.1"],[98,"Reading 20","The robot","3.2","3.2.1","1.2","1.2.2"],[99,"Writing 20","The robot","4.2","4.2.2","2.1","2.1.4"],[100,"Language Arts 20","The robot","5.1","5.1.1","1.2","1.2.4"],[101,"Listening 21","The robot","1.2","1.2.2","1.2","1.2.5"],[102,"Speaking 21","The robot","2.3","2.3.1","2.1","2.1.2"],[103,"Reading 21","The robot","3.1","3.1.4","3.1","3.1.2"],[104,"Writing 21","The robot","4.3","4.3.2","3.1","3.1.1"],[105,"Language Arts 21","The robot","5.3","5.3.1","2.1","2.1.4"],[106,"Listening 22","The robot","1.1","1.1.1","3.1","3.1.2"],[107,"Speaking 22","The robot","2.1","2.1.2","4.2","4.2.1"],[108,"Writing 22","The robot","4.2","4.2.5","4.3","4.3.1"],[109,"Reading 22","The robot","3.2","3.2.3","4.3","4.3.2"],[110,"Language Arts 22","The robot","5.1","5.1.1","2.1","2.1.1"],[111,"Listening 23","The robot","1.2","1.2.5","1.3","1.3.1"],[112,"Speaking 23","The robot","2.1","2.1.4","1.2","1.2.5"],[113,"Reading 23","The robot","3.2","3.2.2","3.2","3.2.3"],[114,"Writing 23","The robot","4.3","4.3.1","4.3","4.3.3"],[115,"Language Arts 23","The robot","5.3","5.3.1","2.2","2.2.2"],[116,"Reading 24","The robot","3.2","3.2.2","2.2","2.2.1"],[117,"Writing 24","The robot","4.2","4.2.4","1.2","1.2.1"],[118,"Speaking 24","The robot","2.2","2.2.1","2.2","2.2.2"],[119,"Listening 24","The robot","1.2","1.2.2","3.2","3.2.4"],[120,"Language Arts 24","The robot","5.1","5.1.1","5.1","5.1.2"],[121,"Listening 25","The robot","1.2","1.2.2","4.3","4.3.2"],[122,"Speaking 25","The robot","2.1","2.1.5","4.2","4.2.4"],[123,"Reading 25","The robot","3.2","3.2.2","4.3","4.3.2"],[124,"Writing 25","The robot","4.3","4.3.3","4.3","4.3.1"],[125,"Language Arts 25","The robot","5.2","5.2.1","1.2","1.2.3"],[126,"Listening 26","At the beach","1.2","1.2.1","1.3","1.3.1"],[127,"Speaking 26","At the beach","2.1","2.1.2","1.3","1.3.1"],[128,"Writing 26","At the beach","4.3","4.3.2","1.2","1.2.2"],[129,"Reading 26","At the beach","3.2","3.2.2","2.1","2.1.1"],[130,"Language Arts 26","At the beach","5.1","5.1.2","3.1","3.1.2"],[131,"Listening 27","At the beach","1.2","1.2.2","4.2","4.2.5"],[132,"Speaking 27","At the beach","2.1","2.1.1","2.2","2.2.1"],[133,"Reading 27","At the beach","3.2","3.2.2","3.2","3.2.3"],[134,"Writing 27","At the beach","4.3","4.3.3","2.1","2.1.1"],[135,"Language Arts 27","At the beach","5.2","5.2.1","1.2","1.2.3"],[136,"Reading 28","At the beach","3.2","3.2.3","3.2","3.2.1"],[137,"Listening 28","At the beach","1.1","1.1.1","3.1","3.1.2"],[138,"Writing 28","At the beach","4.3","4.3.3","4.3","4.3.1"],[139,"Speaking 28","At the beach","2.1","2.1.3","1.2","1.2.4"],[140,"Language Arts 28","At the beach","5.3","5.3.1","1.2","1.2.2"],[141,"Listening 29","At the beach","1.2","1.2.2","3.1","3.1.2"],[142,"Speaking 29","At the beach","2.1","2.1.1","2.1","2.1.5"],[143,"Reading 29","At the beach","3.2","3.2.1","3.2","3.2.3"],[144,"Writing 29","At the beach","4.3","4.3.1","4.3","4.3.2"],[145,"Language Arts 29","At the beach","5.2","5.2.1","4.3","4.3.2"],[146,"Reading 30","At the beach","3.2","3.2.2","4.3","4.3.2"],[147,"Writing 30","At the beach","4.3","4.3.3","4.3","4.3.1"],[148,"Listening 30","At the beach","1.3","1.3.1","1.2","1.2.4"],[149,"Speaking 30","At the beach","2.1","2.1.5","1.2","1.2.2"],[150,"Language Arts 30","At the beach","5.1","5.1.2","5.2","5.2.1"],[151,"Reading 31","At the beach","3.2","3.2.2","3.2","3.2.4"],[152,"Writing 31","At the beach","4.3","4.3.1","4.3","4.3.3"],[153,"Listening 31","At the beach","1.2","1.2.5","1.2","1.2.2"],[154,"Speaking 31","At the beach","2.1","2.1.5","2.2","2.2.2"],[155,"Language Arts 31","At the beach","5.1","5.1.2","2.3","2.3.1"],[156,"Listening 32","Free Time","1.2","1.2.5","1.2","1.2.2"],[157,"Speaking 32","The old house","2.1","2.1.5","1.2","1.2.5"],[158,"Reading 32","Get dressed","3.2","3.2.3","1.2","1.2.5"],[159,"Writing 32","The robot","4.3","4.3.3","4.3","4.3.1"],[160,"Language Arts 42","At the beach","5.1","5.1.2","2.3","2.3.1"]]}

def _eng12_validate_sow_master():
    for _year in ("Tahun 1","Tahun 2"):
        _rows=_ENG12_SOW_MASTER.get(_year,[])
        _nums=[int(x[0]) for x in _rows]
        if len(_rows)!=160 or len(set(_nums))!=160 or set(_nums)!=set(range(1,161)):
            raise RuntimeError(f"English SOW master invalid for {_year}: {len(_rows)} rows")
        for _x in _rows:
            if len(_x)<7 or not all(str(v).strip() for v in (_x[2],_x[3],_x[4],_x[5],_x[6])):
                raise RuntimeError(f"English SOW mapping incomplete: {_year} Lesson {_x[0]}")
    return True

_eng12_validate_sow_master()

def _eng12_rows(year_label):
    import sqlite3
    path=_eng12_db_path()
    verified={}
    if path:
        con=sqlite3.connect(path); con.row_factory=sqlite3.Row
        try:
            rs=con.execute("""
            SELECT year_label,subject,lesson_no,unit_title,topic,textbook_title,
                   textbook_page_start,textbook_page_end,workbook_page_start,workbook_page_end,
                   workbook_status,audio_status,audio_reference,ready_for_bot,notes
            FROM bot_lesson_index WHERE year_label=? AND ready_for_bot=1
            ORDER BY CAST(lesson_no AS INTEGER)
            """,(year_label,)).fetchall()
            verified={int(r["lesson_no"]):dict(r) for r in rs}
        finally: con.close()
    sow=_ENG12_SOW_MASTER.get(year_label,[])
    rows=[]
    for n,skill,topic,mcs,mls,ccs,cls in sow:
        item=dict(verified.get(int(n),{}))
        item.update({"year_label":year_label,"subject":"Bahasa Inggeris","lesson_no":int(n),
                     "unit_title":topic,"topic":topic,"ready_for_bot":1,
                     "_sow_skill":skill,"_sow_main_cs":mcs,"_sow_main_ls":mls,
                     "_sow_comp_cs":ccs,"_sow_comp_ls":cls})
        rows.append(item)
    return rows if len(rows)==160 else list(verified.values())

def _eng12_standards(year_label,lesson_no):
    import sqlite3
    path=_eng12_db_path()
    if not path: return []
    con=sqlite3.connect(path); con.row_factory=sqlite3.Row
    try:
        rs=con.execute("""
        SELECT role,content_standard,learning_standard
        FROM bot_lesson_standards
        WHERE year_label=? AND lesson_no=?
        ORDER BY CASE role WHEN 'MAIN' THEN 0 ELSE 1 END,id
        """,(year_label,str(lesson_no))).fetchall()
        out=[dict(r) for r in rs]
        if out: return out
        for n,skill,topic,mcs,mls,ccs,cls in _ENG12_SOW_MASTER.get(year_label,[]):
            if int(n)==int(lesson_no):
                return [
                    {"role":"MAIN","content_standard":mcs,"learning_standard":mls},
                    {"role":"COMPLEMENTARY","content_standard":ccs,"learning_standard":cls}
                ]
        return []
    finally:
        con.close()

def _eng12_unit_menu(cid,page=0):
    ss=state.setdefault(cid,{})
    rows=_eng12_rows(_eng12_year_label(ss))
    if not rows:
        return send(cid,"🚧 <b>Data English BOT_READY Tahun 1–2 belum tersedia.</b>",
                    [[{"text":"🏠 Menu Utama","callback_data":"home"}]])
    # Group by normalized display title so e.g. "At School" / "At school" is one unit.
    units=[]; seen=set()
    # Revision/Introduction are SOW blocks, not textbook unit numbers.
    # Number textbook units explicitly: Year 1 Friends=0, At School=1...;
    # Year 2 Free Time=5 through At the beach=9.
    y=_eng12_year_label(ss)
    unit_no_map={
        "Tahun 1":{"friends":0,"at school":1,"let’s play!":2,"let's play!":2,"pet show":3,"lunchtime":4},
        "Tahun 2":{"free time":5,"the old house":6,"get dressed!":7,"get dressed":7,"the robot":8,"at the beach":9}
    }.get(y,{})
    for r in rows:
        raw=str(r.get("topic") or r.get("unit_title") or "").strip()
        norm=" ".join(raw.lower().split())
        if norm and norm not in seen:
            seen.add(norm); units.append({"title":raw,"norm":norm,"unit_no":unit_no_map.get(norm)})
    ss["_eng12_rows"]=rows; ss["_eng12_units"]=units
    per=10; page=max(0,int(page or 0)); a=page*per; b=min(a+per,len(units)); kb=[]
    for i in range(a,b):
        title=units[i]["title"]; uno=units[i].get("unit_no")
        label=(f"📘 Unit {uno} — {title}" if uno is not None else f"📚 {title}")
        kb.append([{"text":label[:60],"callback_data":f"eng12_lsnunit_{i}"}])
    nav=[]
    if a: nav.append({"text":"⬅️ Sebelum","callback_data":f"eng12_up_{page-1}"})
    if b<len(units): nav.append({"text":"Seterusnya ➡️","callback_data":f"eng12_up_{page+1}"})
    if nav: kb.append(nav)
    kb.append([{"text":"⬅️ Tukar Subjek","callback_data":"choose_grade"},{"text":"🏠 Menu Utama","callback_data":"home"}])
    return send(cid,f"🇬🇧 <b>Bahasa Inggeris • {ss.get('year','')}</b>\n\nPilih <b>Unit/Tajuk</b>. Selepas itu pilih Lesson; SK/SP dipadankan automatik.",kb)

def _eng12_lesson_menu(cid,ui,page=0):
    ss=state.setdefault(cid,{})
    units=ss.get("_eng12_units") or []
    if ui<0 or ui>=len(units): return _eng12_unit_menu(cid,0)
    unit=units[ui]
    norm=unit.get("norm","")
    rows=[r for r in (ss.get("_eng12_rows") or []) if
          " ".join(str(r.get("topic") or r.get("unit_title") or "").strip().lower().split())==norm]
    rows=sorted(rows,key=lambda r:int(str(r.get("lesson_no") or "0").strip() or 0))
    ss["_eng12_unit_index"]=ui; ss["_eng12_lesson_rows"]=rows
    per=10; page=max(0,int(page or 0)); a=page*per; b=min(a+per,len(rows)); kb=[]
    for i in range(a,b):
        r=rows[i]; ln=str(r.get("lesson_no") or "")
        ps=r.get("textbook_page_start"); pe=r.get("textbook_page_end")
        skill=str(r.get("_sow_skill") or "").strip()
        label=f"{'📖' if ps not in (None,'') else '📚'} Lesson {ln}"
        if skill: label+=f" · {skill}"
        if ps not in (None,""):
            pg=str(ps) if pe in (None,"",ps) else f"{ps}–{pe}"
            label+=f" · m/s {pg}"
        kb.append([{"text":label[:60],"callback_data":f"eng12_lesson_{i}"}])
    nav=[]
    if a: nav.append({"text":"⬅️ Sebelum","callback_data":f"eng12_lp_{ui}_{page-1}"})
    if b<len(rows): nav.append({"text":"Seterusnya ➡️","callback_data":f"eng12_lp_{ui}_{page+1}"})
    if nav: kb.append(nav)
    kb.append([{"text":"⬅️ Unit/Tajuk","callback_data":"eng12_units"},{"text":"🏠 Menu Utama","callback_data":"home"}])
    title=unit.get("title",""); uno=unit.get("unit_no")
    heading=(f"Unit {uno} — {title}" if uno is not None else title)
    return send(cid,f"📖 <b>{heading}</b>\n\nPilih <b>Lesson</b>. SK/SP dipadankan automatik.\n📖 = ada buku teks · 📚 = SOW sahaja",kb)


def _eng12_audio_zip_path():
    import os, tempfile, requests
    candidates=[
        os.environ.get("CIKGULAJU_SUPERMINDS_AUDIO_ZIP","").strip(),
        os.path.join(os.path.dirname(__file__),"super_minds_1_audio_cds.zip"),
        os.path.join("/tmp","super_minds_1_audio_cds.zip"),
    ]
    for x in candidates:
        if x and os.path.exists(x):
            return x
    # Fallback: download the verified Drive ZIP at runtime.
    drive_id=os.environ.get("CIKGULAJU_SUPERMINDS_AUDIO_DRIVE_ID","1zN35ALOo0-1N9BYkkZ53_c4t_movwHar").strip()
    if drive_id:
        url=f"https://drive.google.com/uc?export=download&id={drive_id}"
        out=os.path.join("/tmp","super_minds_1_audio_cds.zip")
        try:
            r=requests.get(url,timeout=120)
            if r.ok and r.content[:2]==b"PK":
                with open(out,"wb") as fh: fh.write(r.content)
                return out
            print("English Y1Y2 audio Drive ZIP download failed:",r.status_code,len(r.content),flush=True)
        except Exception as e:
            print("English Y1Y2 audio Drive ZIP download error:",repr(e),flush=True)
    return ""

def _eng12_audio_member_for_ref(ref):
    import zipfile,re
    zpath=_eng12_audio_zip_path()
    if not zpath: return None
    m=re.fullmatch(r"CD([123])-(\d{1,2})",str(ref or "").strip(),re.I)
    if not m: return None
    cd=int(m.group(1)); track=int(m.group(2))
    cd_token={1:"CD 1",2:"CD 2",3:"CD 3"}[cd]
    with zipfile.ZipFile(zpath) as z:
        names=[n for n in z.namelist() if not n.endswith("/")]
        for n in names:
            base=n.rsplit("/",1)[-1]
            if cd_token.lower() in n.lower() and re.match(rf"0*{track}\b",base):
                return n
    return None

def _eng12_send_verified_audio(cid,audio_reference):
    import os,zipfile,tempfile,requests
    refs=[x.strip() for x in str(audio_reference or "").replace(",", ";").split(";") if x.strip()]
    if not refs: return
    zpath=_eng12_audio_zip_path()
    if not zpath: 
        print("English Y1Y2 audio zip missing",flush=True)
        return
    token=(globals().get("BOT_TOKEN") or globals().get("TOKEN") or os.environ.get("BOT_TOKEN") or "").strip()
    if not token:
        print("English Y1Y2 Telegram token missing",flush=True)
        return
    with zipfile.ZipFile(zpath) as z:
        for ref in refs:
            member=_eng12_audio_member_for_ref(ref)
            if not member:
                print("English Y1Y2 audio member not found:",ref,flush=True)
                continue
            suffix=os.path.splitext(member)[1] or ".wma"
            with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as tmp:
                tmp.write(z.read(member))
                tpath=tmp.name
            try:
                with open(tpath,"rb") as fh:
                    files={"audio":(f"{ref}{suffix}",fh,"audio/x-ms-wma")}
                    data={"chat_id":str(cid),"caption":f"🎧 {ref}"}
                    rr=requests.post(f"https://api.telegram.org/bot{token}/sendAudio",data=data,files=files,timeout=60)
                    if not rr.ok:
                        fh.seek(0)
                        files={"document":(f"{ref}{suffix}",fh,"audio/x-ms-wma")}
                        rr=requests.post(f"https://api.telegram.org/bot{token}/sendDocument",data=data,files=files,timeout=60)
                    if not rr.ok:
                        print("English Y1Y2 audio send failed:",ref,rr.status_code,rr.text[:300],flush=True)
            finally:
                try: os.unlink(tpath)
                except Exception: pass

def _eng12_commit_lesson(cid,idx):
    ss=state.setdefault(cid,{})
    rows=ss.get("_eng12_lesson_rows") or []
    try: r=rows[int(idx)]
    except Exception: return _eng12_unit_menu(cid,0)
    ln=str(r.get("lesson_no") or "").strip()
    std=_eng12_standards(_eng12_year_label(ss),ln)
    mapped=[]
    for x in std:
        cs=str(x.get("content_standard") or "").strip()
        ls=str(x.get("learning_standard") or "").strip()
        if cs and ls:
            mapped.append({"sk_code":cs,"sk_text":"","sp_code":ls,"sp_text":""})
    if not mapped:
        return send(cid,"🚧 <b>SK/SP verified untuk Lesson ini belum lengkap.</b>",
                    [[{"text":"⬅️ Pilih Lesson Lain","callback_data":f"eng12_lsnunit_{ss.get('_eng12_unit_index',0)}"},
                      {"text":"🏠 Menu Utama","callback_data":"home"}]])
    _skill=str(r.get("_sow_skill") or "").strip()
    ss.update({
        "lesson_no":ln,"lesson":ln,
        "lesson_title":(_skill or ("Lesson "+ln)),
        "lesson_skill":_skill,
        "selected_lesson":ln,
        "selected_lesson_no":ln,
        "topic":str(r.get("unit_title") or r.get("topic") or "").strip(),
        "unit":str(r.get("unit_title") or r.get("topic") or "").strip(),
        "unit_title":str(r.get("unit_title") or r.get("topic") or "").strip(),
        "subtopic":str(r.get("topic") or "").strip(),
        "textbook_page_start":r.get("textbook_page_start"),
        "textbook_page_end":r.get("textbook_page_end"),
        "workbook_page_start":r.get("workbook_page_start"),
        "workbook_page_end":r.get("workbook_page_end"),
        "workbook_status":str(r.get("workbook_status") or ""),
        "audio_status":str(r.get("audio_status") or ""),
        "audio_reference":str(r.get("audio_reference") or "") if str(r.get("audio_status") or "")=="VERIFIED_AUDIO" else "",
        "quick_material_flow":True,
        "assessment_mode":"formative",
    })
    _commit_multi_sp(ss,mapped[:8])
    if len(mapped)>=1:
        ss["main_sk"]=mapped[0]["sk_code"]; ss["main_sp"]=mapped[0]["sp_code"]
    if len(mapped)>=2:
        ss["complementary_sk"]=mapped[1]["sk_code"]; ss["complementary_sp"]=mapped[1]["sp_code"]
    ss["curriculum_source"]="SOW_VERIFIED"
    ss["lesson_source_mode"]="TEXTBOOK_LINKED" if (r.get("textbook_page_start") or r.get("textbook_page_end")) else "SOW_ONLY"
    ss["has_textbook_link"]=bool(r.get("textbook_page_start") or r.get("textbook_page_end"))
    ss["material_curriculum_context"]=(
        f"{_eng12_year_label(ss)} | Lesson {ln} | "
        f"{str(r.get('_sow_skill') or '').strip()} | "
        f"{str(r.get('topic') or r.get('unit_title') or '').strip()} | "
        f"Main {mapped[0]['sk_code']}/{mapped[0]['sp_code']}" +
        (f" | Complementary {mapped[1]['sk_code']}/{mapped[1]['sp_code']}" if len(mapped)>1 else "")
    )
    _unit=str(r.get("topic") or r.get("unit_title") or "").strip()
    _summary=f"✅ <b>Lesson {ln}</b>"
    if _skill: _summary+=f" — {_skill}"
    if _unit: _summary+=f"\n📘 {_unit}"
    _summary+="\nSK/SP dipadankan automatik daripada SOW verified."
    if ss.get("has_textbook_link"):
        p1=ss.get("textbook_page_start"); p2=ss.get("textbook_page_end")
        _summary+=f"\n📖 Buku teks: m/s {p1}" + (f"–{p2}" if p2 and str(p2)!=str(p1) else "")
    else:
        _summary+="\n📚 SOW lesson — tiada halaman buku teks dipaksa."
    send(cid,_summary,None)
    if ss.get("audio_status")=="VERIFIED_AUDIO" and ss.get("audio_reference"):
        try:
            _eng12_send_verified_audio(cid,ss.get("audio_reference"))
        except Exception as e:
            print("English Y1Y2 verified audio send error:",repr(e),flush=True)
    # Always show the material menu first. Existing auto-pack/continuation hooks are
    # legacy-dependent and can silently stop after lesson selection.
    return send(cid,"📚 <b>Pilih bahan</b>",[
        [{"text":"📝 RPH","callback_data":"eng12_material_rph"},{"text":"📄 Worksheet","callback_data":"eng12_material_worksheet"}],
        [{"text":"🎨 BBM","callback_data":"eng12_material_bbm"},{"text":"⬅️ Lesson","callback_data":f"eng12_lsnunit_{ss.get('_eng12_unit_index',0)}"}],
        [{"text":"🏠 Menu Utama","callback_data":"home"}]
    ])

_callback_eng12_base=callback
def callback(cid,d):
    ss=state.setdefault(cid,{})
    ds=str(d or "")
    if _eng12_is_english_subject_callback(ds) and _eng12_year_label(ss) and _eng12_db_path():
        ss["subject"]="Bahasa Inggeris"
        for k in ("topic","subtopic","selected_sk","selected_sp","_eng12_rows","_eng12_units","_eng12_lesson_rows"):
            ss.pop(k,None)
        return _eng12_unit_menu(cid,0)
    if ds=="eng12_units": return _eng12_unit_menu(cid,0)
    if ds.startswith("eng12_up_"):
        try: return _eng12_unit_menu(cid,int(ds.rsplit("_",1)[1]))
        except Exception: return _eng12_unit_menu(cid,0)
    if ds.startswith("eng12_lsnunit_"):
        try: return _eng12_lesson_menu(cid,int(ds.rsplit("_",1)[1]),0)
        except Exception as e:
            print("English Y1Y2 lsnunit->lesson route error:",repr(e),flush=True)
            return _eng12_unit_menu(cid,0)
    if ds.startswith("eng12_unit_"):
        try: return _eng12_lesson_menu(cid,int(ds.rsplit("_",1)[1]),0)
        except Exception as e:
            print("English Y1Y2 unit->lesson route error:",repr(e),flush=True)
            return _eng12_unit_menu(cid,0)
    if ds.startswith("eng12_lp_"):
        try:
            _,_,ui,pg=ds.split("_")
            return _eng12_lesson_menu(cid,int(ui),int(pg))
        except Exception: return _eng12_unit_menu(cid,0)
    if ds.startswith("eng12_lesson_"):
        try: return _eng12_commit_lesson(cid,int(ds.rsplit("_",1)[1]))
        except Exception as e:
            print("English Y1Y2 BOT_READY select error:",repr(e),flush=True)
            return _eng12_unit_menu(cid,0)
    if ds.startswith("eng12_material_"):
        kind=ds.rsplit("_",1)[1]
        if not ss.get("lesson_no") or ss.get("curriculum_source")!="SOW_VERIFIED":
            return send(cid,"⚠️ Sila pilih Lesson terlebih dahulu.",[[{"text":"📚 Pilih Unit/Lesson","callback_data":"eng12_units"}]])
        ss["requested_material"]=kind
        ss["material_source_policy"]="SOW_FIRST_TEXTBOOK_OVERLAY"
        # Compatibility aliases consumed by older material engines.
        ss["material_type"]=kind
        ss["task"]=kind
        ss["current_task"]=kind
        ss["selected_topic"]=ss.get("topic","")
        ss["selected_subtopic"]=ss.get("subtopic","")
        ss["selected_unit"]=ss.get("unit_title") or ss.get("unit") or ss.get("topic","")
        ss["selected_skill"]=ss.get("lesson_skill","")
        ss["source_policy"]="SOW_FIRST_TEXTBOOK_OVERLAY"
        # Explicit pedagogical guardrails for downstream RPH/worksheet/BBM engines.
        ss["main_skill"]=ss.get("lesson_skill","")
        ss["material_guardrails"]={
            "follow_selected_lesson":True,
            "follow_sow_skill":True,
            "follow_main_and_complementary_standards":True,
            "invent_textbook_page":False,
            "invent_workbook_page":False,
            "invent_audio_reference":False,
            "textbook_optional":not bool(ss.get("has_textbook_link")),
        }
        # Common aliases used by historical RPH / worksheet / BBM builders.
        ss["rph_topic"]=ss.get("topic","")
        ss["rph_subtopic"]=ss.get("subtopic","")
        ss["rph_main_skill"]=ss.get("lesson_skill","")
        ss["rph_main_sk"]=ss.get("main_sk","")
        ss["rph_main_sp"]=ss.get("main_sp","")
        ss["rph_complementary_sk"]=ss.get("complementary_sk","")
        ss["rph_complementary_sp"]=ss.get("complementary_sp","")
        # RPH engine policy: activities/objectives must be anchored to the selected SOW skill.
        ss["rph_curriculum_context"]=ss.get("material_curriculum_context","")
        ss["rph_source_mode"]=ss.get("lesson_source_mode","SOW_ONLY")
        ss["rph_require_main_skill_match"]=True
        ss["rph_require_main_sp_match"]=True
        ss["rph_require_complementary_sp_match"]=True
        ss["rph_allow_generic_activity"]=False
        # For textbook-linked lessons, RPH must contain the usable teaching procedure
        # extracted/paraphrased from the mapped Teacher's Book guidance, not a pointer to it.
        ss["teacher_book_policy"]="EXTRACT_INTO_RPH" if ss.get("has_textbook_link") else "NOT_REQUIRED"
        ss["rph_require_teacher_book_procedure"]=bool(ss.get("has_textbook_link"))
        ss["rph_forbid_teacher_book_placeholder"]=True
        ss["rph_forbidden_placeholders"]=[
            "follow teacher's book","refer teacher's book","see teacher's book",
            "rujuk teacher's book","ikut teacher's book","rujuk buku panduan guru"
        ]
        ss["rph_teacher_book_content_mode"]="PARAPHRASE_ACTIONABLE_STEPS"
        ss["teacher_book_required_fields"]=[
            "aims","warm_up","student_book_procedure","workbook_procedure",
            "audio_procedure","checking_feedback","ending_lesson","extension_optional"
        ] if ss.get("has_textbook_link") else []
        ss["teacher_book_verified_structure"]="AIMS+SB+WB+WARMUP+ENDING+EXTENSION+TAPESCRIPT_ANSWERS"
        ss["super_minds_source_lock"]="SUPER_MINDS_1_ONLY"
        ss["super_minds_unit_scope"]=(
            "UNIT_0_TO_4" if _eng12_year_label(ss)=="Tahun 1" else
            "UNIT_5_TO_9" if _eng12_year_label(ss)=="Tahun 2" else ""
        )
        ss["super_minds_1_unit_pages"]={
            "friends":{"unit":0,"sb_start":4,"tb_start":4},
            "at school":{"unit":1,"sb_start":10,"tb_start":10},
            "let’s play!":{"unit":2,"sb_start":22,"tb_start":22},
            "let's play!":{"unit":2,"sb_start":22,"tb_start":22},
            "pet show":{"unit":3,"sb_start":34,"tb_start":34},
            "lunchtime":{"unit":4,"sb_start":46,"tb_start":46},
            "free time":{"unit":5,"sb_start":58,"tb_start":58},
            "the old house":{"unit":6,"sb_start":70,"tb_start":70},
            "get dressed!":{"unit":7,"sb_start":82,"tb_start":82},
            "get dressed":{"unit":7,"sb_start":82,"tb_start":82},
            "the robot":{"unit":8,"sb_start":94,"tb_start":94},
            "at the beach":{"unit":9,"sb_start":106,"tb_start":106},
        }
        _smkey=" ".join(str(ss.get("unit_title") or ss.get("topic") or "").lower().split())
        ss["super_minds_1_unit_page_map"]=ss["super_minds_1_unit_pages"].get(_smkey,{})
        ss["reject_super_minds_level_2"]=True
        ss["teacher_book_integration_rule"]=(
            "Map the selected SB/WB page to its Teacher's Book teaching notes; "
            "extract the relevant procedure and paraphrase it into executable RPH steps. "
            "Do not output a Teacher's Book reference as a substitute for the procedure."
        ) if ss.get("has_textbook_link") else ""
        ss["worksheet_topic"]=ss.get("topic","")
        ss["worksheet_skill"]=ss.get("lesson_skill","")
        ss["worksheet_curriculum_context"]=ss.get("material_curriculum_context","")
        ss["worksheet_source_mode"]=ss.get("lesson_source_mode","SOW_ONLY")
        ss["worksheet_require_skill_match"]=True
        ss["worksheet_require_main_sp_match"]=True
        ss["worksheet_allow_generic_questions"]=False
        ss["worksheet_require_answer_key"]=True
        ss["bbm_topic"]=ss.get("topic","")
        ss["bbm_skill"]=ss.get("lesson_skill","")
        ss["bbm_curriculum_context"]=ss.get("material_curriculum_context","")
        ss["bbm_source_mode"]=ss.get("lesson_source_mode","SOW_ONLY")
        ss["bbm_require_skill_match"]=True
        ss["bbm_require_main_sp_match"]=True
        ss["bbm_allow_generic_content"]=False
        ss["bbm_use_verified_source_content_only"]=True
        # Year 1/2 QA contract shared by all three material engines.
        ss["eng12_material_qa"]={
            "qa_version":"ENG12_QA_V1",
            "year":_eng12_year_label(ss),
            "lesson_no":int(ss.get("lesson_no") or 0),
            "unit":ss.get("unit_title") or ss.get("topic",""),
            "skill":ss.get("lesson_skill",""),
            "main_sk":ss.get("main_sk",""),
            "main_sp":ss.get("main_sp",""),
            "complementary_sk":ss.get("complementary_sk",""),
            "complementary_sp":ss.get("complementary_sp",""),
            "source_mode":ss.get("lesson_source_mode","SOW_ONLY"),
            "textbook_page":ss.get("textbook_page_start"),
            "workbook_status":ss.get("workbook_status"),
            "audio_status":ss.get("audio_status"),
            "ready_rule":"lesson+skill+main_sp+complementary_sp must match selected SOW lesson",
        }
        _qa=ss["eng12_material_qa"]
        _qa_errors=[]
        if _qa["year"] not in ("Tahun 1","Tahun 2"): _qa_errors.append("year")
        if not (1 <= int(_qa["lesson_no"] or 0) <= 160): _qa_errors.append("lesson_no")
        for _f in ("unit","skill","main_sk","main_sp","complementary_sk","complementary_sp"):
            if not str(_qa.get(_f) or "").strip(): _qa_errors.append(_f)
        if _qa_errors:
            print("ENG12 MATERIAL QA BLOCKED",kind,_qa_errors,_qa,flush=True)
            return send(cid,"⚠️ <b>Bahan belum boleh dijana.</b>\nData SOW Lesson tidak lengkap: "+", ".join(_qa_errors)+".\nSila pilih Lesson semula.",[[{"text":"📚 Pilih Unit/Lesson","callback_data":"eng12_units"}]])
        ss["eng12_material_qa_status"]="PASS"
        aliases={
            "rph":["task_rph","rph","buat_rph","generate_rph"],
            "worksheet":["task_worksheet","worksheet","buat_worksheet","generate_worksheet"],
            "bbm":["task_bbm","bbm","buat_bbm","generate_bbm"]
        }.get(kind,[])
        # Prefer a callback token that the existing app source actually handles.
        import inspect
        try: src=inspect.getsource(_callback_eng12_base)
        except Exception: src=""
        for alias in aliases:
            if (('"' + alias + '"') in src or ("'" + alias + "'") in src):
                print("ENG12 material handoff",kind,alias,ss.get("material_curriculum_context",""),flush=True)
                return _callback_eng12_base(cid,alias)
        if aliases:
            print("ENG12 material fallback",kind,aliases[0],ss.get("material_curriculum_context",""),flush=True)
            return _callback_eng12_base(cid,aliases[0])
    return _callback_eng12_base(cid,d)

APP_VERSION=str(globals().get("APP_VERSION",""))+"+ENG12-BOTREADY"
# ===== END ENGLISH Y1Y2 BOT READY V1 =====
'''

# V2: put a priority router inside the original callback before legacy handlers.
PRIORITY_MARK="# ===== ENGLISH Y1Y2 PRIORITY ROUTE V2 ====="
if PRIORITY_MARK not in s:
    anchor="def callback(cid,d):"
    pos=s.find(anchor)
    if pos < 0:
        raise SystemExit("callback anchor missing for English Y1Y2 priority route")
    body_start=s.find("\n",pos)
    priority=r"""
    # ===== ENGLISH Y1Y2 PRIORITY ROUTE V2 =====
    try:
        _eng_ds=str(d or "")
        _eng_ss=state.setdefault(cid,{})
        if globals().get("_eng12_is_english_subject_callback") and _eng12_is_english_subject_callback(_eng_ds) and globals().get("_eng12_year_label") and _eng12_year_label(_eng_ss) and globals().get("_eng12_db_path") and _eng12_db_path():
            _eng_ss["subject"]="Bahasa Inggeris"
            for _eng_k in ("topic","subtopic","selected_sk","selected_sp","_eng12_rows","_eng12_units","_eng12_lesson_rows"):
                _eng_ss.pop(_eng_k,None)
            return _eng12_unit_menu(cid,0)
        if _eng_ds=="eng12_units": return _eng12_unit_menu(cid,0)
        if _eng_ds.startswith("eng12_up_"):
            try: return _eng12_unit_menu(cid,int(_eng_ds.rsplit("_",1)[1]))
            except Exception: return _eng12_unit_menu(cid,0)
        if _eng_ds.startswith("eng12_lsnunit_"):
            try: return _eng12_lesson_menu(cid,int(_eng_ds.rsplit("_",1)[1]),0)
            except Exception as _eng_e:
                print("English Y1Y2 priority lsnunit->lesson error:",repr(_eng_e),flush=True)
                return _eng12_unit_menu(cid,0)
        if _eng_ds.startswith("eng12_unit_"):
            try: return _eng12_lesson_menu(cid,int(_eng_ds.rsplit("_",1)[1]),0)
            except Exception as _eng_e:
                print("English Y1Y2 unit->lesson route error:",repr(_eng_e),flush=True)
                return _eng12_unit_menu(cid,0)
        if _eng_ds.startswith("eng12_lp_"):
            try:
                _,_,_eng_ui,_eng_pg=_eng_ds.split("_")
                return _eng12_lesson_menu(cid,int(_eng_ui),int(_eng_pg))
            except Exception: return _eng12_unit_menu(cid,0)
        if _eng_ds.startswith("eng12_lesson_"):
            try: return _eng12_commit_lesson(cid,int(_eng_ds.rsplit("_",1)[1]))
            except Exception as _eng_e:
                print("English Y1Y2 BOT_READY priority select error:",repr(_eng_e),flush=True)
                return _eng12_unit_menu(cid,0)
    except Exception as _eng_outer:
        print("English Y1Y2 BOT_READY priority route error:",repr(_eng_outer),flush=True)
    # ===== END ENGLISH Y1Y2 PRIORITY ROUTE V2 =====
"""
    s=s[:body_start+1]+priority+s[body_start+1:]

s += "\n\n"+block
p.write_text(s,encoding="utf-8")
print("patched",p,p.stat().st_size)
