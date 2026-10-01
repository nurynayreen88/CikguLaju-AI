from pathlib import Path

P=Path(__file__).with_name("app.py")
s=P.read_text(encoding="utf-8")
MARK="# BETA50_LESSON_FIRST_QA16"

# HOTFIX v25.172 — deterministic source-level repairs before import
# Repair every misnamed v25.128 Science definition, not only the first occurrence.
s=s.replace("def _science_sp_focus_v25127(s):", "def _science_sp_focus_v25128(s):")
s=s.replace("def _science_action_v25127(text):", "def _science_action_v25128(text):")
s=s.replace("def _science_sp_activity_v25127(s, rows):", "def _science_sp_activity_v25128(s, rows):")
# If a v25.129 base assignment appears before a usable v25.128 symbol, fall back to v25.127 safely.
s=s.replace("_science_sp_focus_v25128_base = _science_sp_focus_v25128", "_science_sp_focus_v25128_base = globals().get('_science_sp_focus_v25128', globals().get('_science_sp_focus_v25127'))")
s=s.replace("_science_action_v25128_base = _science_action_v25128", "_science_action_v25128_base = globals().get('_science_action_v25128', globals().get('_science_action_v25127'))")
s=s.replace("_science_sp_activity_v25128_base = _science_sp_activity_v25128", "_science_sp_activity_v25128_base = globals().get('_science_sp_activity_v25128', globals().get('_science_sp_activity_v25127'))")
# Break worksheet v25.164 self-recursion at every occurrence.
s=s.replace("return _ws151_language(s, contract, c, fmt)", "return _ws151_language_before_v25164(s, contract, c, fmt)")
s=s.replace("return _ws151_math(s, contract, c, fmt)", "return _ws151_math_before_v25164(s, contract, c, fmt)")
s=s.replace("return _ws151_science(s, contract, c, fmt)", "return _ws151_science_before_v25164(s, contract, c, fmt)")
s=s.replace("return _ws164_language(s, contract, c, fmt)", "return _ws151_language_before_v25164(s, contract, c, fmt)")
s=s.replace("return _ws164_math(s, contract, c, fmt)", "return _ws151_math_before_v25164(s, contract, c, fmt)")
s=s.replace("return _ws164_science(s, contract, c, fmt)", "return _ws151_science_before_v25164(s, contract, c, fmt)")
# Science must not fail closed merely because a legacy format_key is absent.
s=s.replace("    if not fmt:\n        raise RuntimeError('WORKSHEET_FORMAT_MISSING')", "    if not fmt:\n        sub=str(state.get('subject') or '').lower()\n        if 'sains' in sub or 'science' in sub:\n            c=dict(c or {}); c['format_key']='science_scenario'; return c\n        raise RuntimeError('WORKSHEET_FORMAT_MISSING')")

# Runtime core is already a Git-safe 24,485,888-byte DB in the repository.
s=s.replace(
    "os.path.join(os.path.dirname(__file__), 'CikguLaju_Curriculum_Master_v1.db')",
    "os.path.join(os.path.dirname(__file__), 'CikguLaju_Curriculum_Master_v24_95_CORE.db')"
)

block=r'''
# BETA50_LESSON_FIRST_QA16
def _beta50_rpt_units(year_label, subject):
    """Verified RPT/SOW units available for lesson-first Beta flow."""
    con=_db()
    try:
        rows=con.execute("""SELECT id,sequence_no,unit_code,unit_title,topic,theme,skill_focus
                            FROM rpt_entries
                            WHERE year_label=? AND subject=? AND verified=1
                              AND content_verified=1 AND sequence_verified=1
                            ORDER BY sequence_no,id""",(year_label,subject)).fetchall()
        out=[]; seen=set()
        for r in rows:
            d=dict(r)
            key=(str(d.get('unit_title') or '').strip(),str(d.get('topic') or '').strip())
            if key not in seen:
                seen.add(key); out.append({'key':key,'unit_title':key[0],'topic':key[1]})
        return out
    finally: con.close()

def _beta50_rpt_lessons(year_label, subject, unit_key):
    con=_db()
    try:
        rows=con.execute("""SELECT id,sequence_no,unit_code,unit_title,topic,subtopic,theme,skill_focus
                            FROM rpt_entries
                            WHERE year_label=? AND subject=? AND verified=1
                              AND content_verified=1 AND sequence_verified=1
                              AND COALESCE(unit_title,'')=? AND COALESCE(topic,'')=?
                            ORDER BY sequence_no,id""",(year_label,subject,unit_key[0],unit_key[1])).fetchall()
        return [dict(r) for r in rows]
    finally: con.close()

def show_beta50_units(cid, page=0):
    st=state.setdefault(cid,{})
    units=_beta50_rpt_units(st.get('year',''),st.get('subject',''))
    if not units: return show_topics(cid,0)
    st['beta50_units']=units
    per=8; start=page*per; end=min(start+per,len(units)); kb=[]
    for i in range(start,end):
        u=units[i]; label=u.get('topic') or u.get('unit_title') or f'Unit {i+1}'
        kb.append([{'text':'📚 '+str(label)[:55],'callback_data':f'b50unit_{i}'}])
    nav=[]
    if page>0: nav.append({'text':'⬅️ Sebelum','callback_data':f'b50up_{page-1}'})
    if end<len(units): nav.append({'text':'Seterusnya ➡️','callback_data':f'b50up_{page+1}'})
    if nav: kb.append(nav)
    kb.append([{'text':'⬅️ Pilih Subjek','callback_data':'back_subjects'},{'text':'🏠 Menu Utama','callback_data':'home'}])
    send(cid,f'📚 <b>{st.get("subject","")} — {st.get("year","")}</b>\n\nPilih <b>Unit/Tajuk</b>. Selepas itu pilih Lesson; SK/SP akan dipadankan automatik.',kb)

def show_beta50_lessons(cid, unit_index, page=0):
    st=state.setdefault(cid,{})
    units=st.get('beta50_units') or _beta50_rpt_units(st.get('year',''),st.get('subject',''))
    if unit_index<0 or unit_index>=len(units): return show_beta50_units(cid,0)
    st['beta50_unit_index']=unit_index; u=units[unit_index]
    lessons=_beta50_rpt_lessons(st.get('year',''),st.get('subject',''),tuple(u['key']))
    st['beta50_lessons']=lessons
    per=10; start=page*per; end=min(start+per,len(lessons)); kb=[]
    for i in range(start,end):
        r=lessons[i]; code=str(r.get('unit_code') or f'Lesson {r.get("sequence_no",i+1)}').strip()
        focus=str(r.get('skill_focus') or '').strip(); label=code+(f' • {focus}' if focus else '')
        kb.append([{'text':'📖 '+label[:58],'callback_data':f'b50lesson_{i}'}])
    nav=[]
    if page>0: nav.append({'text':'⬅️ Sebelum','callback_data':f'b50lp_{unit_index}_{page-1}'})
    if end<len(lessons): nav.append({'text':'Seterusnya ➡️','callback_data':f'b50lp_{unit_index}_{page+1}'})
    if nav: kb.append(nav)
    kb.append([{'text':'⬅️ Unit/Tajuk','callback_data':'b50units'},{'text':'🏠 Menu Utama','callback_data':'home'}])
    send(cid,f'📖 <b>{u.get("topic") or u.get("unit_title")}</b>\n\nPilih <b>Lesson</b>. SK/SP tidak perlu dipilih kali kedua.',kb)

def _beta50_select_lesson(cid, lesson_index):
    st=state.setdefault(cid,{})
    lessons=st.get('beta50_lessons') or []
    if lesson_index<0 or lesson_index>=len(lessons): return show_beta50_units(cid,0)
    r=lessons[lesson_index]; rid=int(r['id']); con=_db()
    try:
        std=[dict(x) for x in con.execute("""SELECT standard_type,standard_code,standard_text,role,sequence_no
                                             FROM rpt_entry_standards
                                             WHERE rpt_entry_id=? AND verified=1
                                             ORDER BY CASE standard_type WHEN 'SK' THEN 0 ELSE 1 END,sequence_no,id""",(rid,)).fetchall()]
    finally: con.close()
    st['rpt_entry_id']=rid; st['textbook_lesson_no']=str(r.get('unit_code') or r.get('sequence_no') or '')
    st['topic']=str(r.get('topic') or r.get('unit_title') or '').strip()
    st['subtopic']=str(r.get('subtopic') or r.get('skill_focus') or '').strip()
    st['theme']=str(r.get('theme') or '').strip(); st['textbook_page_focus']=str(r.get('skill_focus') or '').strip()
    sk=[x for x in std if x.get('standard_type')=='SK']; sp=[x for x in std if x.get('standard_type')=='SP']
    if not sk or not sp:
        return send(cid,'ℹ️ <b>Lesson ini tidak mempunyai fixed SK/SP dalam SOW yang disahkan.</b>\n\nCikguLaju tidak akan mereka standard. Pilih Lesson lain untuk Beta 50%.',[[{'text':'⬅️ Pilih Lesson Lain','callback_data':f'b50unit_{st.get("beta50_unit_index",0)}'},{'text':'🏠 Menu Utama','callback_data':'home'}]])
    opts=[]; parent=sk[0]
    for x in sp:
        opts.append({'sk_code':parent['standard_code'],'sk_text':parent['standard_text'],'sp_code':x['standard_code'],'sp_text':x['standard_text']})
    st['selected_sp_codes']=[x['sp_code'] for x in opts]; st['multi_sp_options']=opts
    _commit_multi_sp(st,opts)
    send(cid,f'✅ <b>{html.escape(st["textbook_lesson_no"])}</b> dipilih.\nSK/SP telah dipadankan automatik daripada RPT/SOW verified.',None)
    st['beta50_verified_lesson']=True; st['beta50_curriculum_locked']=True
    return after_curriculum_selected(cid)
'''

if MARK not in s:
    anchor="def show_topics(cid, page=0):"
    if anchor not in s: raise SystemExit("Beta50 patch anchor show_topics missing")
    s=s.replace(anchor,block+"\n"+anchor,1)

old="""        if s0.get('task')=='bbm':
            s0['assessment_mode']='formative'
            return show_topics(cid,0)"""
new="""        if s0.get('task')=='bbm':
            s0['assessment_mode']='formative'
            return show_beta50_units(cid,0) if _beta50_rpt_units(s0.get('year',''),s0.get('subject','')) else show_topics(cid,0)"""
if old in s: s=s.replace(old,new,1)

handler="""    elif d == 'b50units':
        return show_beta50_units(cid,0)
    elif d.startswith('b50up_'):
        try: return show_beta50_units(cid,int(d.split('_',1)[1]))
        except Exception: return show_beta50_units(cid,0)
    elif d.startswith('b50unit_'):
        try: return show_beta50_lessons(cid,int(d.split('_',1)[1]),0)
        except Exception: return show_beta50_units(cid,0)
    elif d.startswith('b50lp_'):
        try:
            _,ui,pg=d.split('_'); return show_beta50_lessons(cid,int(ui),int(pg))
        except Exception: return show_beta50_units(cid,0)
    elif d.startswith('b50lesson_'):
        try: return _beta50_select_lesson(cid,int(d.split('_',1)[1]))
        except Exception as e:
            print('Beta50 lesson select error:',repr(e),flush=True); return show_beta50_units(cid,0)
"""
if "elif d == 'b50units':" not in s:
    anchor="    elif d == 'fast_use_rpt':"
    if anchor not in s: raise SystemExit("Beta50 callback anchor missing")
    s=s.replace(anchor,handler+anchor,1)

P.write_text(s,encoding="utf-8")
print("BETA50 patch applied", P.stat().st_size)


# ENGLISH_Y1Y2_BOT_READY_V1_APPLY
# Apply the English Year 1-2 BOT_READY runtime patch after the existing Beta50 patch.
import subprocess, sys
_eng_patch=Path(__file__).with_name("tools").joinpath("patch_english_y1y2_bot_ready_v1.py")
if _eng_patch.exists():
    subprocess.check_call([sys.executable, str(_eng_patch), str(P)])
    # Runtime audit: print the exact functions/lines still containing legacy English SK-flow wording.
    import re
    _needles=("unit buku teks","pilih **sk**","pilih <b>sk</b>","standard kandungan (sk)")
    _txt=P.read_text(encoding="utf-8")
    _low=_txt.lower()
    for _needle in _needles:
        _start=0
        while True:
            _hit=_low.find(_needle,_start)
            if _hit < 0: break
            _line=_txt.count("\n",0,_hit)+1
            _lo=max(0,_txt.rfind("\n",0,_hit-500))
            _hi=_txt.find("\n",_hit+500)
            if _hi < 0: _hi=len(_txt)
            _snippet=_txt[_lo:_hi].replace("\n","\\n")
            print(f"LEGACY_ENGLISH_FLOW_HIT line={_line} needle={_needle!r} snippet={_snippet[:1200]}",flush=True)
            _start=_hit+len(_needle)
    print("ENGLISH_BOT_READY_RUNTIME_AUDIT",
          "eng12_block=",("ENGLISH Y1Y2 BOT READY V1" in _txt),
          "eng12_unit=",("eng12_lsnunit_" in _txt),
          "eng12_lesson=",("eng12_lesson_" in _txt),
          "callback_defs=",_txt.count("\ndef callback("),
          flush=True)
    # Final guard: remove the legacy English unit->SK route after all runtime patches.
    _txt=P.read_text(encoding="utf-8")
    _legacy_phrase="Selepas itu cikgu akan pilih **SK** dan **SP** yang dipetakan kepada unit tersebut."
    if _legacy_phrase in _txt:
        print("WARNING: legacy English Unit->SK prompt still exists after BOT_READY patch",flush=True)
    # BOT_READY must own English Year 1-2 routing; fail deploy rather than silently serving old SK flow.
    if "ENGLISH Y1Y2 BOT READY V1" not in _txt or "eng12_lesson_" not in _txt:
        raise SystemExit("English Y1Y2 BOT_READY runtime route was not installed")
else:
    raise SystemExit("English Y1Y2 BOT_READY patch helper missing: "+str(_eng_patch))


# MAIN_PDP_ENTRY_V2500
# Final runtime UI guard: keep the main PdP entry stable and remove the legacy
# "Guna Bahan Cikgu" choice without touching curriculum/database content.
_txt=P.read_text(encoding="utf-8")
if "# MAIN_PDP_ENTRY_V2501" not in _txt:
    _txt += r'''

# MAIN_PDP_ENTRY_V2501
_send_v2501_base = send

def send(cid, text, kb=None, *args, **kwargs):
    """Normalize the main PdP keyboard at render time."""
    if isinstance(kb, list):
        cleaned=[]
        for row in kb:
            if not isinstance(row, list):
                cleaned.append(row); continue
            nr=[]
            for btn in row:
                if not isinstance(btn, dict):
                    nr.append(btn); continue
                label=str(btn.get("text") or "")
                low=label.lower()
                if "guna bahan cikgu" in low:
                    continue
                b=dict(btn)
                if "sediakan bahan pdp" in low:
                    b["callback_data"]="pdp_material_start_v2500"
                nr.append(b)
            if nr: cleaned.append(nr)
        kb=cleaned
    return _send_v2501_base(cid,text,kb,*args,**kwargs)

_callback_v2501_base = callback

def callback(cid,d):
    ds=str(d or "")
    if ds in ("pdp_material_start_v2500","pdp_material_start_v2501"):
        ss=state.setdefault(cid,{})
        ss["task"]="quick_material"
        ss["quick_material_flow"]=True
        ss["assessment_mode"]="formative"
        for k in ("topic","subtopic","selected_sk","selected_sp","lesson","lesson_no",
                  "selected_lesson","selected_lesson_no","rpt_entry_id",
                  "_eng12_rows","_eng12_units","_eng12_lesson_rows"):
            ss.pop(k,None)
        # Reuse the app's established grade selector instead of duplicating it.
        # Start the same proven curriculum entry used by material tasks.
        # "task_rph" is handled by the legacy dispatcher and then the later
        # English/BM lesson routers take ownership after year/subject selection.
        ss["task"]="quick_material"
        ss["requested_material"]="rph"
        return send(cid,"📚 <b>Sediakan Bahan PdP</b>\\n\\nPilih <b>Teruskan</b> untuk memilih Tahun/Tingkatan dan menyediakan bahan berdasarkan Lesson/PdP yang disusun mengikut RPT/SOW.",[[{"text":"Teruskan ➡️","callback_data":"pdp_material_continue_v2503"}],[{"text":"🏠 Menu Utama","callback_data":"home"}]])
    if ds=="pdp_material_continue_v2503":
        ss=state.setdefault(cid,{})
        ss["task"]="rph"
        ss["requested_material"]="rph"
        ss["quick_material_flow"]=True
        ss["assessment_mode"]="formative"
        return choose_grade(cid)
    return _callback_v2501_base(cid,d)

def _main_pdp_entry_v2502(cid):
    ss=state.setdefault(cid,{})
    ss["task"]="rph"
    ss["requested_material"]="rph"
    ss["quick_material_flow"]=True
    ss["assessment_mode"]="formative"
    return choose_grade(cid)

APP_VERSION=str(globals().get("APP_VERSION",""))+"+MAIN-PDP-V2502"
# END MAIN_PDP_ENTRY_V2501
'''
    P.write_text(_txt,encoding="utf-8")
    print("MAIN PDP entry v2501 installed",flush=True)


# MATH_V2599_CANONICAL_RUNTIME
# Patch the ORIGINAL v25.42 Math reader in app.py before import. No callback wrappers.
_txt=P.read_text(encoding="utf-8")
_old=r'''def _sm2542_rows(year_label, subject):
    if subject not in ('Sains','Matematik'):
        return []
    con=_db()
    try:
        # v25.99: Matematik uses the new canonical sequence exclusively.
        # Sains remains on the existing verified_pdp_sequence table.
        table = 'verified_pdp_sequence_v2' if subject == 'Matematik' else 'verified_pdp_sequence'
        rs=con.execute(f"""SELECT * FROM {table}
            WHERE year_label=? AND subject=?
              AND COALESCE(pdp_sequence_code,'')<>''
              AND COALESCE(verification_status,'') NOT IN ('REJECT_NON_SK','SOURCE_NONCORE','REJECTED')
            ORDER BY COALESCE(source_sequence_no,9999), id""",
            (str(year_label or '').strip(),subject)).fetchall()
        return [dict(r) for r in rs]
    finally:
        con.close()
'''
_new=r'''def _math_v2599_db_path():
    import os as _os, hashlib as _hashlib, sqlite3 as _sqlite3
    _base=_os.path.dirname(__file__)
    _stem="CikguLaju_Curriculum_Master_v25_99_MATH_T1_T6_CANONICAL"
    _parts=[_os.path.join(_base,_stem+f".part{i:02d}") for i in range(3)]
    if not all(_os.path.isfile(p) for p in _parts):
        raise RuntimeError("Math v25_99 incomplete: part00-part02 required")
    _target=_os.path.join("/tmp",_stem+".db")
    _expected="74f1e139ae6e7f64379ee3fb103334f450c683152186b03368bb02dfe3b8c821"
    def _sha(path):
        h=_hashlib.sha256()
        with open(path,"rb") as fh:
            for chunk in iter(lambda:fh.read(1024*1024),b""): h.update(chunk)
        return h.hexdigest()
    if not _os.path.isfile(_target) or _sha(_target)!=_expected:
        _tmp=_target+".tmp"
        with open(_tmp,"wb") as out:
            for p in _parts:
                with open(p,"rb") as src:
                    for chunk in iter(lambda:src.read(1024*1024),b""): out.write(chunk)
        if _sha(_tmp)!=_expected:
            try: _os.remove(_tmp)
            except OSError: pass
            raise RuntimeError("Math v25_99 SHA256 verification failed")
        con=_sqlite3.connect(_tmp)
        try:
            if con.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                raise RuntimeError("Math v25_99 integrity_check failed")
        finally: con.close()
        _os.replace(_tmp,_target)
    return _target

def _sm2542_rows(year_label, subject):
    if subject not in ('Sains','Matematik'):
        return []
    if subject=='Matematik':
        import sqlite3 as _sqlite3
        con=_sqlite3.connect(_math_v2599_db_path())
        con.row_factory=_sqlite3.Row
        table='verified_pdp_sequence_v2'
    else:
        con=_db()
        table='verified_pdp_sequence'
    try:
        rs=con.execute(f"""SELECT * FROM {table}
            WHERE year_label=? AND subject=?
              AND COALESCE(pdp_sequence_code,'')<>''
              AND COALESCE(verification_status,'') NOT IN ('REJECT_NON_SK','SOURCE_NONCORE','REJECTED')
            ORDER BY COALESCE(source_sequence_no,9999), id""",
            (str(year_label or '').strip(),subject)).fetchall()
        return [dict(r) for r in rs]
    finally:
        con.close()
'''
if _old not in _txt:
    raise SystemExit("Math v25.99 source patch anchor missing")
_txt=_txt.replace(_old,_new,1)
P.write_text(_txt,encoding="utf-8")
print("MATH v25.99 original reader patched",flush=True)


# MATH_V2599_AUTO_SKSP_V1
# Final generated-app patch: Math PdP owns its verified SK/SP and skips legacy manual SK/SP screens.
_txt=P.read_text(encoding="utf-8")
_math_auto = r'''
# MATH_V2599_AUTO_SKSP_V1
_math2599_callback_base = callback

def _math2599_auto_commit(cid, idx):
    ss=state.setdefault(cid,{})
    rows=ss.get("_sm2542_pdp_rows") or ss.get("_sm2542_rows") or []
    titles=ss.get("_sm2542_pdp_titles") or ss.get("_sm2542_pdp_codes") or []
    selected=[]
    if 0 <= idx < len(titles):
        key=titles[idx]
        for r in rows:
            if str(r.get("pdp_sequence_code") or "")==str(key) or str(r.get("pdp_title") or "")==str(key):
                selected.append(r)
    if not selected and 0 <= idx < len(rows):
        selected=[rows[idx]]
    if not selected:
        return _math2599_callback_base(cid,"home")
    r0=selected[0]
    ss.update({
        "task":"quick_material","quick_material_flow":True,"rph_mode":"fast_rpt","assessment_mode":"formative",
        "topic":str(r0.get("unit_title") or r0.get("theme") or ""),
        "subtopic":str(r0.get("pdp_title") or ""),
        "pdp_title":str(r0.get("pdp_title") or ""),
        "pdp_sequence_code":str(r0.get("pdp_sequence_code") or ""),
        "rpt_theme":str(r0.get("theme") or ""),
        "rpt_unit_title":str(r0.get("unit_title") or ""),
        "rpt_topic":str(r0.get("pdp_title") or ""),
        "skill_metadata":str(r0.get("skill_metadata") or ""),
        "textbook_ref":str(r0.get("textbook_ref") or ""),
        "activitybook_ref":str(r0.get("activitybook_ref") or "")
    })
    mapped=[]
    seen=set()
    for r in selected:
        sk=str(r.get("sk_code") or "").strip()
        sp=str(r.get("sp_code") or "").strip()
        if not sp: continue
        k=(sk,sp)
        if k in seen: continue
        seen.add(k)
        mapped.append({"sk_code":sk,"sk_text":str(r.get("sk_text") or ""),"sp_code":sp,"sp_text":str(r.get("sp_text") or "")})
    if not mapped:
        return send(cid,"⚠️ <b>SK/SP verified untuk PdP Matematik ini belum lengkap.</b>",[[{"text":"🏠 Menu Utama","callback_data":"home"}]])
    _commit_multi_sp(ss,mapped[:12])
    return _temporary_auto_pack_v2386(cid)

def callback(cid,d):
    ss=state.setdefault(cid,{})
    ds=str(d or "")
    if ds.startswith("sm2542_pdp_") and (ss.get("subject")=="Matematik" or bool(ss.get("_sm2542_pdp_rows"))):
        try: idx=int(ds.rsplit("_",1)[1])
        except Exception: idx=-1
        return _math2599_auto_commit(cid,idx)
    return _math2599_callback_base(cid,d)
'''
_txt += _math_auto
P.write_text(_txt,encoding="utf-8")
print("MATH v25.99 auto SK/SP route installed",flush=True)
