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

def _eng12_rows(year_label):
    import sqlite3
    path=_eng12_db_path()
    if not path: return []
    con=sqlite3.connect(path); con.row_factory=sqlite3.Row
    try:
        rs=con.execute("""
        SELECT year_label,subject,lesson_no,unit_title,topic,textbook_title,
               textbook_page_start,textbook_page_end,workbook_page_start,workbook_page_end,
               workbook_status,audio_status,audio_reference,ready_for_bot,notes
        FROM bot_lesson_index
        WHERE year_label=? AND ready_for_bot=1
        ORDER BY CAST(lesson_no AS INTEGER)
        """,(year_label,)).fetchall()
        return [dict(r) for r in rs]
    finally:
        con.close()

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
        return [dict(r) for r in rs]
    finally:
        con.close()

def _eng12_unit_menu(cid,page=0):
    ss=state.setdefault(cid,{})
    rows=_eng12_rows(_eng12_year_label(ss))
    if not rows:
        return send(cid,"🚧 <b>Data English BOT_READY Tahun 1–2 belum tersedia.</b>",
                    [[{"text":"🏠 Menu Utama","callback_data":"home"}]])
    units=[]; seen=set()
    for r in rows:
        key=(str(r.get("unit_title") or "").strip(),str(r.get("topic") or "").strip())
        if key not in seen:
            seen.add(key); units.append(key)
    ss["_eng12_rows"]=rows; ss["_eng12_units"]=units
    per=10; page=max(0,int(page or 0)); a=page*per; b=min(a+per,len(units)); kb=[]
    for i in range(a,b):
        u,t=units[i]
        label=t or u or f"Unit {i+1}"
        kb.append([{"text":("📘 "+label)[:60],"callback_data":f"eng12_unit_{i}"}])
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
    unit,topic=units[ui]
    rows=[r for r in (ss.get("_eng12_rows") or []) if
          str(r.get("unit_title") or "").strip()==unit and str(r.get("topic") or "").strip()==topic]
    ss["_eng12_unit_index"]=ui; ss["_eng12_lesson_rows"]=rows
    per=10; page=max(0,int(page or 0)); a=page*per; b=min(a+per,len(rows)); kb=[]
    for i in range(a,b):
        r=rows[i]; ln=str(r.get("lesson_no") or "")
        ps=r.get("textbook_page_start"); pe=r.get("textbook_page_end")
        label=f"📚 Lesson {ln}"
        if ps not in (None,""):
            pg=str(ps) if pe in (None,"",ps) else f"{ps}–{pe}"
            label+=f" · m/s {pg}"
        kb.append([{"text":label[:60],"callback_data":f"eng12_lesson_{i}"}])
    nav=[]
    if a: nav.append({"text":"⬅️ Sebelum","callback_data":f"eng12_lp_{ui}_{page-1}"})
    if b<len(rows): nav.append({"text":"Seterusnya ➡️","callback_data":f"eng12_lp_{ui}_{page+1}"})
    if nav: kb.append(nav)
    kb.append([{"text":"⬅️ Unit/Tajuk","callback_data":"eng12_units"},{"text":"🏠 Menu Utama","callback_data":"home"}])
    title=topic or unit
    return send(cid,f"📖 <b>{title}</b>\n\nPilih <b>Lesson</b>. SK/SP tidak perlu dipilih kali kedua.",kb)


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
                    [[{"text":"⬅️ Pilih Lesson Lain","callback_data":f"eng12_unit_{ss.get('_eng12_unit_index',0)}"},
                      {"text":"🏠 Menu Utama","callback_data":"home"}]])
    ss.update({
        "lesson_no":ln,"lesson":ln,
        "topic":str(r.get("unit_title") or r.get("topic") or "").strip(),
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
    send(cid,f"✅ <b>Lesson {ln}</b> dipilih.\nSK/SP dipadankan automatik daripada DB BOT_READY verified.",None)
    if ss.get("audio_status")=="VERIFIED_AUDIO" and ss.get("audio_reference"):
        try:
            _eng12_send_verified_audio(cid,ss.get("audio_reference"))
        except Exception as e:
            print("English Y1Y2 verified audio send error:",repr(e),flush=True)
    nxt=globals().get("after_curriculum_selected") or globals().get("_temporary_auto_pack_v2386")
    return nxt(cid) if callable(nxt) else None

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
